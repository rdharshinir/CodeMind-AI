"""Review Engine – Phase 4.

Assembles a rich prompt from:
  1. The raw source code.
  2. AST analysis summary.
  3. Hindsight-recalled team conventions and guardrails.

Then calls Groq with native JSON mode and resilient repair fallback.
"""

import json
import logging
import uuid
from typing import List, Optional

from groq import AsyncGroq
import json_repair

from codemind.analyzer import analyze_code, AnalysisResult
from codemind.config import get_settings
from codemind.memory import MemoryManager
from codemind.schemas import (
    IssueCategory,
    IssueSeverity,
    ReviewIssue,
    ReviewRequest,
    ReviewResponse,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CodeMind AI — an adaptive code review agent.
You have been given:
  1. Python source code to review.
  2. An AST analysis summary with pre-detected smells.
  3. Team memory retrieved from Hindsight — containing accepted conventions,
     custom rules, and GUARDRAILS (suggestions that were previously REJECTED
     by this team and must NOT be repeated).

Your job:
- Identify bugs, security issues, performance problems, style violations, and architecture concerns.
- Respect ALL guardrails: do NOT suggest anything that is tagged as a rejected/guardrail memory.
- When a team convention from memory is relevant, cite it in `memory_applied`.
- Limit output to the top 6-10 most impactful issues (prioritize critical security vulnerabilities and bugs).
- Keep each explanation concise (1-2 sentences).
- Keep each code suggestion concise (only the relevant fix snippet, under 6 lines).
- Return ONLY valid JSON matching this exact schema:

{
  "issues": [
    {
      "id": "<uuid>",
      "category": "bug|security|performance|style|architecture",
      "severity": "low|medium|high|critical",
      "line_start": <int or null>,
      "line_end": <int or null>,
      "title": "<short title>",
      "explanation": "<concise explanation>",
      "suggestion": "<concise code fix>",
      "memory_applied": "<which stored memory influenced this, or null>"
    }
  ],
  "summary": "<2-3 sentence high-level review summary>"
}
"""


def _build_user_prompt(
    code: str,
    ast_summary: str,
    memories: str,
    guardrails: str,
    context: Optional[str],
) -> str:
    parts = []

    if context:
        parts.append(f"## Project Context\n{context}\n")

    parts.append(f"## Retrieved Team Memory (Hindsight)\n{memories}\n")
    parts.append(f"## Active Guardrails (Do NOT suggest these)\n{guardrails}\n")
    parts.append(f"## AST Analysis\n{ast_summary}\n")
    parts.append(f"## Source Code to Review\n```python\n{code}\n```")

    return "\n".join(parts)


def _clean_markdown_fences(text: str) -> str:
    """Safely strip markdown code fences from LLM responses."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        first_newline = cleaned.find("\n")
        if first_newline != -1:
            cleaned = cleaned[first_newline + 1:]
        else:
            cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


def _parse_llm_response(raw: str) -> tuple[List[ReviewIssue], str]:
    """Parse LLM JSON output into ReviewIssue list + summary string with resilient repair."""
    cleaned = _clean_markdown_fences(raw)

    data = None
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Standard JSON parse failed, attempting resilient json_repair...")
        try:
            repaired = json_repair.repair_json(cleaned, return_objects=True)
            if isinstance(repaired, dict):
                data = repaired
            elif isinstance(repaired, str):
                data = json.loads(repaired)
        except Exception as repair_exc:
            logger.error("json_repair also failed: %s", repair_exc)

    if not isinstance(data, dict):
        return [
            ReviewIssue(
                id=str(uuid.uuid4()),
                category=IssueCategory.style,
                severity=IssueSeverity.low,
                title="Review engine parse error",
                explanation="The review response could not be parsed as JSON. Please retry.",
                suggestion="Please retry the review.",
            )
        ], "Parse error — raw response returned."

    issues = []
    for item in data.get("issues", []):
        try:
            issues.append(ReviewIssue(
                id=item.get("id") or str(uuid.uuid4()),
                category=IssueCategory(item.get("category", "style")),
                severity=IssueSeverity(item.get("severity", "low")),
                line_start=item.get("line_start"),
                line_end=item.get("line_end"),
                title=item.get("title", ""),
                explanation=item.get("explanation", ""),
                suggestion=item.get("suggestion", ""),
                memory_applied=item.get("memory_applied"),
            ))
        except Exception as exc:
            logger.warning("Skipping malformed issue item: %s | %s", exc, item)

    summary = data.get("summary", "Review complete.")
    return issues, summary


class ReviewEngine:
    """Orchestrates AST analysis, Hindsight recall, and LLM review."""

    def __init__(self):
        settings = get_settings()

        if not settings.groq_api_key:
            raise ValueError("GROQ_API_KEY is not set in .env")

        self._groq = AsyncGroq(api_key=settings.groq_api_key)
        self._model = settings.groq_model
        self._memory = MemoryManager()
        logger.info("ReviewEngine initialized | model=%s", self._model)

    async def review(self, request: ReviewRequest) -> ReviewResponse:
        """Full review pipeline: AST → Hindsight Recall → LLM → Response."""

        # --- Step 1: AST Analysis ---
        logger.info("Running AST analysis on %s", request.filename)
        ast_result: AnalysisResult = analyze_code(request.code)
        ast_summary = ast_result.to_summary_string()

        # --- Step 2: Retrieve Memory from Hindsight ---
        logger.info("Recalling team conventions from Hindsight...")
        memories_text = await self._memory.recall_conventions(
            code_context=request.code[:800],
        )
        guardrails_text = await self._memory.recall_guardrails()

        # --- Step 3: Build Prompt ---
        user_prompt = _build_user_prompt(
            code=request.code,
            ast_summary=ast_summary,
            memories=memories_text,
            guardrails=guardrails_text,
            context=request.context,
        )

        # --- Step 4: Call Groq LLM with JSON format ---
        logger.info("Sending prompt to Groq model: %s", self._model)
        chat_completion = await self._groq.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=6000,
        )
        raw_response = chat_completion.choices[0].message.content

        # --- Step 5: Parse LLM Output ---
        issues, summary = _parse_llm_response(raw_response)

        # --- Step 6: Store review session summary in Hindsight ---
        await self._memory.retain_review_session(
            filename=request.filename or "untitled.py",
            issue_count=len(issues),
            summary=summary,
        )

        return ReviewResponse(
            filename=request.filename or "untitled.py",
            total_lines=ast_result.total_lines,
            issues=issues,
            summary=summary,
            memories_recalled=memories_text,
            ast_summary=ast_summary,
        )
