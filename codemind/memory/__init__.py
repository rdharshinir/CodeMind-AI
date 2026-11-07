"""Hindsight Memory Manager for CodeMind AI (Phase 3).

Wraps the official hindsight-client SDK and provides high-level operations
specifically for code review memory: retaining feedback, recalling conventions,
and reflecting on the team's accumulated coding standards.
"""

import logging
from typing import List, Optional

from hindsight_client import Hindsight
from hindsight_client import RecallResponse, RetainResponse

from codemind.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tag taxonomy
# ---------------------------------------------------------------------------
# When feedback is accepted, it is tagged as a positive team convention.
# When rejected, it is tagged as a guardrail so the LLM knows to suppress it.
TAG_ACCEPTED = "accepted_rule"
TAG_REJECTED = "rejected_rule"
TAG_GUARDRAIL = "guardrail"
TAG_CONVENTION = "convention"
TAG_CUSTOM_RULE = "custom_rule"
TAG_REVIEW_HISTORY = "review_history"


class MemoryManager:
    """High-level Hindsight memory interface for CodeMind AI.

    Uses async methods internally (aretain, arecall, areflect) to work
    correctly inside FastAPI/asyncio event loops.
    """

    def __init__(self):
        settings = get_settings()

        if not settings.hindsight_api_key:
            raise ValueError(
                "HINDSIGHT_API_KEY is not set. "
                "Please add it to your .env file."
            )

        self._client = Hindsight(
            base_url=settings.hindsight_base_url,
            api_key=settings.hindsight_api_key,
            user_agent="codemind-ai/0.1.0",
        )
        self._bank_id = settings.hindsight_bank_id
        logger.info("MemoryManager initialized | bank_id=%s", self._bank_id)

    # ------------------------------------------------------------------
    # Retain
    # ------------------------------------------------------------------
    async def retain_accepted(
        self,
        suggestion_text: str,
        code_context: str,
        reason: Optional[str] = None,
    ) -> RetainResponse:
        """Store an accepted suggestion as a positive team convention."""
        reason_part = f"\nDeveloper rationale: {reason}" if reason else ""
        content = (
            f"ACCEPTED CODE REVIEW RULE:\n"
            f"Suggestion: {suggestion_text}\n"
            f"Code context: {code_context[:300]}"
            f"{reason_part}"
        )
        response = await self._client.aretain(
            bank_id=self._bank_id,
            content=content,
            tags=[TAG_ACCEPTED, TAG_CONVENTION],
        )
        logger.info("Retained accepted rule | doc_id=%s", getattr(response, "document_id", "?"))
        return response

    async def retain_rejected(
        self,
        suggestion_text: str,
        code_context: str,
        reason: Optional[str] = None,
    ) -> RetainResponse:
        """Store a rejected suggestion as an explicit guardrail.

        Future reviews recall this and suppress similar suggestions.
        """
        reason_part = f"\nDeveloper rationale: {reason}" if reason else ""
        content = (
            f"REJECTED CODE REVIEW SUGGESTION (GUARDRAIL):\n"
            f"Do NOT suggest the following for this codebase:\n"
            f"Rejected suggestion: {suggestion_text}\n"
            f"Code context: {code_context[:300]}"
            f"{reason_part}"
        )
        response = await self._client.aretain(
            bank_id=self._bank_id,
            content=content,
            tags=[TAG_REJECTED, TAG_GUARDRAIL],
        )
        logger.info("Retained rejected guardrail | doc_id=%s", getattr(response, "document_id", "?"))
        return response

    async def retain_custom_rule(
        self,
        rule_text: str,
        author: Optional[str] = None,
    ) -> RetainResponse:
        """Manually add a team rule or coding convention into Hindsight."""
        author_part = f" (added by {author})" if author else ""
        content = (
            f"TEAM CODING CONVENTION{author_part}:\n"
            f"{rule_text}"
        )
        response = await self._client.aretain(
            bank_id=self._bank_id,
            content=content,
            tags=[TAG_CUSTOM_RULE, TAG_CONVENTION],
        )
        logger.info("Retained custom rule | doc_id=%s", getattr(response, "document_id", "?"))
        return response

    async def retain_review_session(
        self,
        filename: str,
        issue_count: int,
        summary: str,
    ) -> RetainResponse:
        """Store a review session summary in memory for history tracking."""
        content = (
            f"CODE REVIEW SESSION:\n"
            f"File: {filename}\n"
            f"Issues found: {issue_count}\n"
            f"Summary: {summary}"
        )
        response = await self._client.aretain(
            bank_id=self._bank_id,
            content=content,
            tags=[TAG_REVIEW_HISTORY],
        )
        return response

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------
    async def recall_conventions(
        self,
        code_context: str,
        max_tokens: int = 2048,
    ) -> str:
        """Recall relevant team conventions and guardrails for the given code.

        Returns a formatted string ready to be injected into the LLM prompt.
        """
        query = (
            f"What are the team's coding conventions, accepted standards, "
            f"and rejected suggestion guardrails relevant to this code?\n\n"
            f"Code context:\n{code_context[:500]}"
        )
        response: RecallResponse = await self._client.arecall(
            bank_id=self._bank_id,
            query=query,
            max_tokens=max_tokens,
            budget="mid",
        )

        if not response.results:
            return "(No prior conventions or feedback found in memory — this may be the first review.)"

        lines = ["=== Retrieved Team Memory (via Hindsight) ==="]
        for i, result in enumerate(response.results, 1):
            lines.append(f"\n[Memory {i}]")
            lines.append(result.text)

        return "\n".join(lines)

    async def recall_guardrails(self, max_tokens: int = 1024) -> str:
        """Recall all stored guardrails (rejected suggestions) to suppress repeats."""
        response: RecallResponse = await self._client.arecall(
            bank_id=self._bank_id,
            query="What suggestions were rejected by the team and should not be repeated?",
            max_tokens=max_tokens,
            tags=[TAG_GUARDRAIL],
            tags_match="any",
            budget="low",
        )

        if not response.results:
            return "(No guardrails stored yet.)"

        lines = ["=== Guardrails: Do NOT repeat these suggestions ==="]
        for result in response.results:
            lines.append(f"- {result.text}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Reflect
    # ------------------------------------------------------------------
    async def reflect_team_profile(self) -> str:
        """Generate a synthesized high-level summary of the team's coding standards."""
        response = await self._client.areflect(
            bank_id=self._bank_id,
            query=(
                "Summarize the team's coding standards, accepted conventions, "
                "and rejected suggestion guardrails stored in memory. "
                "Present as a structured profile of the team's coding preferences."
            ),
            budget="mid",
        )
        return getattr(response, "answer", str(response))

    async def recall_review_history(self, max_tokens: int = 2048) -> List[str]:
        """Return past review session summaries from memory."""
        response: RecallResponse = await self._client.arecall(
            bank_id=self._bank_id,
            query="Previous code review sessions and their outcomes",
            max_tokens=max_tokens,
            tags=[TAG_REVIEW_HISTORY],
            tags_match="any",
            budget="mid",
        )
        return [r.text for r in response.results]

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------
    async def ping(self) -> bool:
        """Check connectivity to the Hindsight server."""
        try:
            await self._client.monitoring.get_version()
            return True
        except Exception as exc:
            logger.warning("Hindsight ping failed: %s", exc)
            return False
