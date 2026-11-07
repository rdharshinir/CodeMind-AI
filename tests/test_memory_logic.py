"""Unit tests for CodeMind AI memory and prompt synthesis logic."""

import pytest
from codemind.memory import (
    TAG_ACCEPTED,
    TAG_REJECTED,
    TAG_GUARDRAIL,
    TAG_CONVENTION,
    TAG_CUSTOM_RULE,
    TAG_REVIEW_HISTORY,
)
from codemind.engine import _build_user_prompt, _parse_llm_response


def test_tag_taxonomy_constants():
    assert TAG_ACCEPTED == "accepted_rule"
    assert TAG_REJECTED == "rejected_rule"
    assert TAG_GUARDRAIL == "guardrail"
    assert TAG_CONVENTION == "convention"
    assert TAG_CUSTOM_RULE == "custom_rule"
    assert TAG_REVIEW_HISTORY == "review_history"


def test_build_user_prompt_structure():
    code = "def calculate(x): return x * 2"
    ast_summary = "=== AST Analysis ===\nFunctions: calculate"
    memories = "=== Retrieved Memory ===\n[Memory 1] Use type hints."
    guardrails = "=== Guardrails ===\n- Do not suggest docstrings."
    context = "Payments service repository"

    prompt = _build_user_prompt(
        code=code,
        ast_summary=ast_summary,
        memories=memories,
        guardrails=guardrails,
        context=context,
    )

    assert "## Project Context" in prompt
    assert "Payments service repository" in prompt
    assert "## Retrieved Team Memory (Hindsight)" in prompt
    assert "Use type hints" in prompt
    assert "## Active Guardrails (Do NOT suggest these)" in prompt
    assert "Do not suggest docstrings" in prompt
    assert "## AST Analysis" in prompt
    assert "## Source Code to Review" in prompt
    assert code in prompt


def test_parse_llm_response_valid_json():
    sample_json = '''
    {
        "issues": [
            {
                "id": "item-1",
                "category": "security",
                "severity": "high",
                "line_start": 4,
                "line_end": 4,
                "title": "Hardcoded secret",
                "explanation": "API key literal exposed in source.",
                "suggestion": "api_key = os.getenv('API_KEY')",
                "memory_applied": "Team security rule"
            }
        ],
        "summary": "Found 1 security issue."
    }
    '''
    issues, summary = _parse_llm_response(sample_json)
    assert len(issues) == 1
    assert issues[0].category.value == "security"
    assert issues[0].severity.value == "high"
    assert issues[0].title == "Hardcoded secret"
    assert summary == "Found 1 security issue."


def test_parse_llm_response_recovers_markdown_fences():
    fenced_json = '''```json
    {
        "issues": [
            {
                "id": "item-2",
                "category": "style",
                "severity": "low",
                "title": "Naming convention",
                "explanation": "Use snake_case for functions.",
                "suggestion": "def my_func(): pass"
            }
        ],
        "summary": "1 style issue found."
    }
    ```'''
    issues, summary = _parse_llm_response(fenced_json)
    assert len(issues) == 1
    assert issues[0].category.value == "style"
    assert issues[0].title == "Naming convention"
