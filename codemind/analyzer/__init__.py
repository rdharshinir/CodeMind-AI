"""AST-based Python code analyzer for CodeMind AI.

Extracts structural information and detects common code smells
to enrich the LLM review prompt with factual, pre-computed context.
"""

import ast
import textwrap
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    end_lineno: int
    has_docstring: bool
    args: List[str]
    is_async: bool
    decorator_names: List[str]
    cyclomatic_complexity: int = 1  # min 1 (branches add +1 each)


@dataclass
class ClassInfo:
    name: str
    lineno: int
    bases: List[str]
    methods: List[str]
    has_docstring: bool


@dataclass
class CodeSmell:
    category: str           # 'bug' | 'security' | 'style' | 'performance'
    lineno: int
    description: str
    severity: str           # 'low' | 'medium' | 'high'


@dataclass
class AnalysisResult:
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    smells: List[CodeSmell] = field(default_factory=list)
    total_lines: int = 0
    parse_error: Optional[str] = None

    def to_summary_string(self) -> str:
        """Produce a concise textual summary suitable for prompt injection."""
        lines = ["=== AST Analysis Summary ==="]
        lines.append(f"Total lines: {self.total_lines}")
        lines.append(f"Functions defined: {len(self.functions)}")
        lines.append(f"Classes defined: {len(self.classes)}")
        lines.append(f"Imports: {', '.join(self.imports) if self.imports else 'none'}")

        if self.functions:
            lines.append("\nFunctions:")
            for fn in self.functions:
                flags = []
                if fn.is_async:
                    flags.append("async")
                if not fn.has_docstring:
                    flags.append("no-docstring")
                if fn.cyclomatic_complexity > 5:
                    flags.append(f"complexity={fn.cyclomatic_complexity}")
                flags_str = f" [{', '.join(flags)}]" if flags else ""
                lines.append(f"  - {fn.name}(line {fn.lineno}){flags_str}")

        if self.classes:
            lines.append("\nClasses:")
            for cls in self.classes:
                bases_str = f"({', '.join(cls.bases)})" if cls.bases else ""
                lines.append(f"  - {cls.name}{bases_str} (line {cls.lineno}) methods: {', '.join(cls.methods)}")

        if self.smells:
            lines.append("\nPre-detected issues:")
            for smell in self.smells:
                lines.append(f"  [{smell.severity.upper()}] Line {smell.lineno}: {smell.description}")

        return "\n".join(lines)


class _ComplexityVisitor(ast.NodeVisitor):
    """Counts cyclomatic complexity branches inside a function body."""

    BRANCH_NODES = (
        ast.If, ast.While, ast.For, ast.AsyncFor,
        ast.ExceptHandler, ast.With, ast.AsyncWith,
        ast.Assert, ast.comprehension,
    )

    def __init__(self):
        self.complexity = 1

    def visit_BoolOp(self, node):
        # Each extra 'and'/'or' operand beyond the first adds a path
        self.complexity += len(node.values) - 1
        self.generic_visit(node)

    def generic_visit(self, node):
        if isinstance(node, self.BRANCH_NODES):
            self.complexity += 1
        super().generic_visit(node)


def _get_decorator_names(node: ast.FunctionDef) -> List[str]:
    names = []
    for d in node.decorator_list:
        if isinstance(d, ast.Name):
            names.append(d.id)
        elif isinstance(d, ast.Attribute):
            names.append(f"{ast.unparse(d)}")
    return names


def _has_docstring(node) -> bool:
    return (
        isinstance(node.body, list)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )


class ASTVisitor(ast.NodeVisitor):
    """Traverses a Python AST and fills an AnalysisResult."""

    def __init__(self):
        self.result = AnalysisResult()
        self._smells: List[CodeSmell] = []

    # ------------------------------------------------------------------
    # Import tracking
    # ------------------------------------------------------------------
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.result.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        names = [alias.name for alias in node.names]
        self.result.imports.append(f"{module}.{{{','.join(names)}}}")
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Function / async function tracking
    # ------------------------------------------------------------------
    def _process_function(self, node):
        args = [arg.arg for arg in node.args.args]

        cv = _ComplexityVisitor()
        cv.visit(node)
        complexity = cv.complexity

        fn = FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            end_lineno=getattr(node, "end_lineno", node.lineno),
            has_docstring=_has_docstring(node),
            args=args,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            decorator_names=_get_decorator_names(node),
            cyclomatic_complexity=complexity,
        )
        self.result.functions.append(fn)

        # --- smell: bare except ---
        for child in ast.walk(node):
            if isinstance(child, ast.ExceptHandler) and child.type is None:
                self._smells.append(CodeSmell(
                    category="bug",
                    lineno=child.lineno,
                    description=f"Bare 'except:' in '{node.name}' – catches all exceptions silently.",
                    severity="medium",
                ))

        # --- smell: mutable default arguments ---
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self._smells.append(CodeSmell(
                    category="bug",
                    lineno=node.lineno,
                    description=f"Mutable default argument in '{node.name}' – use None + guard instead.",
                    severity="high",
                ))

        # --- smell: very high complexity ---
        if complexity > 10:
            self._smells.append(CodeSmell(
                category="style",
                lineno=node.lineno,
                description=f"'{node.name}' has cyclomatic complexity {complexity} (>10). Consider splitting.",
                severity="medium",
            ))

        self.generic_visit(node)

    visit_FunctionDef = _process_function
    visit_AsyncFunctionDef = _process_function

    # ------------------------------------------------------------------
    # Class tracking
    # ------------------------------------------------------------------
    def visit_ClassDef(self, node: ast.ClassDef):
        bases = []
        for b in node.bases:
            try:
                bases.append(ast.unparse(b))
            except Exception:
                bases.append("?")

        methods = [
            n.name for n in ast.walk(node)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
            and n is not node
        ]
        # deduplicate preserving order
        seen = set()
        methods_unique = []
        for m in methods:
            if m not in seen:
                seen.add(m)
                methods_unique.append(m)

        self.result.classes.append(ClassInfo(
            name=node.name,
            lineno=node.lineno,
            bases=bases,
            methods=methods_unique,
            has_docstring=_has_docstring(node),
        ))
        self.generic_visit(node)

    # ------------------------------------------------------------------
    # Security smells (global-pass)
    # ------------------------------------------------------------------
    def visit_Assign(self, node: ast.Assign):
        DANGEROUS_PATTERNS = ("password", "secret", "api_key", "token", "passwd")
        for target in node.targets:
            if isinstance(target, ast.Name):
                name_lower = target.id.lower()
                if any(pat in name_lower for pat in DANGEROUS_PATTERNS):
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        self._smells.append(CodeSmell(
                            category="security",
                            lineno=node.lineno,
                            description=(
                                f"Hardcoded credential detected: '{target.id}' assigned a string literal. "
                                "Move to environment variable."
                            ),
                            severity="high",
                        ))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Detect eval() / exec() usage
        if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
            self._smells.append(CodeSmell(
                category="security",
                lineno=node.lineno,
                description=f"Use of '{node.func.id}()' is a security risk – avoid dynamic code execution.",
                severity="high",
            ))
        # Detect subprocess with shell=True
        if isinstance(node.func, ast.Attribute) and node.func.attr in ("run", "call", "Popen"):
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    self._smells.append(CodeSmell(
                        category="security",
                        lineno=node.lineno,
                        description="subprocess call with shell=True is a command injection risk.",
                        severity="high",
                    ))
        self.generic_visit(node)


def analyze_code(source: str) -> AnalysisResult:
    """Parse Python source and return an AnalysisResult.

    Args:
        source: Raw Python source code string.

    Returns:
        AnalysisResult with functions, classes, imports, and detected smells.
    """
    source = textwrap.dedent(source)
    result = AnalysisResult(total_lines=len(source.splitlines()))

    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        result.parse_error = f"SyntaxError: {exc.msg} (line {exc.lineno})"
        return result

    visitor = ASTVisitor()
    visitor.result = result
    visitor.visit(tree)
    result.smells = visitor._smells

    return result
