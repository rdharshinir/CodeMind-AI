"""Unit tests for CodeMind AI Pydantic schemas."""

import pytest
from pydantic import ValidationError
from codemind.schemas import (
    IssueCategory,
    IssueSeverity,
    ReviewIssue,
    ReviewRequest,
    ReviewResponse,
    FeedbackDecision,
    FeedbackRequest,
    FeedbackResponse,
    ConventionAddRequest,
    HealthResponse,
)


def test_review_issue_valid():
    issue = ReviewIssue(
        id="test-123",
        category=IssueCategory.security,
        severity=IssueSeverity.critical,
        line_start=10,
        line_end=12,
        title="SQL Injection vulnerability",
        explanation="Raw string formatting in SQL query allows injection.",
        suggestion="cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))",
        memory_applied="Team security convention: use parameterized queries.",
    )
    assert issue.category == IssueCategory.security
    assert issue.severity == IssueSeverity.critical
    assert issue.line_start == 10
    assert issue.memory_applied is not None


def test_review_request_valid():
    req = ReviewRequest(code="def add(a, b): return a + b", filename="math_utils.py")
    assert req.filename == "math_utils.py"
    assert "def add" in req.code


def test_feedback_request_valid():
    fb = FeedbackRequest(
        issue_id="issue-001",
        decision=FeedbackDecision.accept,
        suggestion_text="Use snake_case for all helper functions.",
        code_context="def HelperFunction(): pass",
        reason="Matches team PEP8 standard.",
    )
    assert fb.decision == FeedbackDecision.accept
    assert fb.reason == "Matches team PEP8 standard."


def test_feedback_decision_reject():
    fb = FeedbackRequest(
        issue_id="issue-002",
        decision=FeedbackDecision.reject,
        suggestion_text="Add docstrings to pytest fixtures.",
        code_context="@pytest.fixture\ndef sample(): pass",
        reason="We deliberately do not write docstrings on simple fixtures.",
    )
    assert fb.decision == FeedbackDecision.reject


def test_convention_add_request():
    req = ConventionAddRequest(
        rule="Always use structlog instead of standard print statements.",
        author="Tech Lead",
    )
    assert "structlog" in req.rule
    assert req.author == "Tech Lead"


def test_health_response():
    health = HealthResponse(
        status="ok",
        hindsight_connected=True,
        groq_model="qwen/qwen3.8-27b",
        bank_id="codemind-main-bank",
    )
    assert health.status == "ok"
    assert health.hindsight_connected is True
