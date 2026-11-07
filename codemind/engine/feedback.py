"""Feedback Processor – Phase 5: Adaptive Learning Loop.

Receives Accept/Reject decisions from developers and stores them in Hindsight
to influence future reviews.
"""

import logging
from codemind.memory import MemoryManager
from codemind.schemas import FeedbackDecision, FeedbackRequest, FeedbackResponse

logger = logging.getLogger(__name__)


class FeedbackProcessor:
    """Processes developer feedback and stores it as Hindsight memory."""

    def __init__(self):
        self._memory = MemoryManager()

    async def process(self, feedback: FeedbackRequest) -> FeedbackResponse:
        """Store feedback in Hindsight based on the developer's decision."""
        try:
            if feedback.decision == FeedbackDecision.accept:
                await self._memory.retain_accepted(
                    suggestion_text=feedback.suggestion_text,
                    code_context=feedback.code_context,
                    reason=feedback.reason,
                )
                return FeedbackResponse(
                    status="ok",
                    message=(
                        f"✅ Suggestion accepted and stored as a team convention. "
                        f"Future reviews will apply this standard."
                    ),
                    memory_stored=True,
                )
            else:  # reject
                await self._memory.retain_rejected(
                    suggestion_text=feedback.suggestion_text,
                    code_context=feedback.code_context,
                    reason=feedback.reason,
                )
                return FeedbackResponse(
                    status="ok",
                    message=(
                        f"🚫 Suggestion rejected and stored as a guardrail. "
                        f"Future reviews will suppress similar suggestions."
                    ),
                    memory_stored=True,
                )
        except Exception as exc:
            logger.error("FeedbackProcessor error: %s", exc)
            return FeedbackResponse(
                status="error",
                message=f"Failed to store feedback: {exc}",
                memory_stored=False,
            )
