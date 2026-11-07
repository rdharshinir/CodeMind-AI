"""Unit tests for the AST code analyzer (Phase 2)."""

import pytest
from codemind.analyzer import analyze_code

SAMPLE_BAD = '''
import os
import subprocess

password = "hunter2"  # hardcoded credential

def calculate(x, items=[]):
    try:
        result = eval(x)
    except:
        pass
    items.append(result)
    return items

class MyService:
    """A service."""
    def __init__(self, host):
        self.host = host

    def run_cmd(self, cmd):
        subprocess.run(cmd, shell=True)
'''

SAMPLE_GOOD = '''
"""Module docstring."""

import os
from typing import List


def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b


class Calculator:
    """A simple calculator."""

    def multiply(self, x: int, y: int) -> int:
        """Multiply two numbers."""
        return x * y
'''


def test_bad_code_detects_smells():
    result = analyze_code(SAMPLE_BAD)
    assert result.parse_error is None
    categories = {s.category for s in result.smells}
    assert "security" in categories
    assert "bug" in categories


def test_hardcoded_password_detected():
    result = analyze_code(SAMPLE_BAD)
    security_smells = [s for s in result.smells if s.category == "security"]
    desc_texts = " ".join(s.description for s in security_smells)
    assert "password" in desc_texts.lower() or "credential" in desc_texts.lower()


def test_eval_detected():
    result = analyze_code(SAMPLE_BAD)
    eval_smells = [s for s in result.smells if "eval" in s.description]
    assert len(eval_smells) >= 1


def test_bare_except_detected():
    result = analyze_code(SAMPLE_BAD)
    bare = [s for s in result.smells if "bare" in s.description.lower()]
    assert len(bare) >= 1


def test_mutable_default_detected():
    result = analyze_code(SAMPLE_BAD)
    mutable = [s for s in result.smells if "mutable default" in s.description.lower()]
    assert len(mutable) >= 1


def test_shell_true_detected():
    result = analyze_code(SAMPLE_BAD)
    shell = [s for s in result.smells if "shell=True" in s.description]
    assert len(shell) >= 1


def test_good_code_no_critical_smells():
    result = analyze_code(SAMPLE_GOOD)
    assert result.parse_error is None
    high_severity = [s for s in result.smells if s.severity == "high"]
    assert len(high_severity) == 0


def test_function_extraction():
    result = analyze_code(SAMPLE_GOOD)
    fn_names = [f.name for f in result.functions]
    assert "add" in fn_names


def test_class_extraction():
    result = analyze_code(SAMPLE_GOOD)
    class_names = [c.name for c in result.classes]
    assert "Calculator" in class_names


def test_summary_string():
    result = analyze_code(SAMPLE_GOOD)
    summary = result.to_summary_string()
    assert "AST Analysis" in summary
    assert "Functions" in summary
