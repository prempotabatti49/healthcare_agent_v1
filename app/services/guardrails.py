"""
Guardrails
==========
Two-stage check on every incoming user message:

  1. Healthcare relevance gate — reject clearly off-topic queries
  2. Crisis detection — flag suicidal ideation or self-harm signals

Design: keyword pre-filter (fast) + optional LLM classifier (accurate).
In V1 we use keyword-based detection for speed; the LLM classifier is
available for higher-precision pipelines.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ── Healthcare keywords (allow-list heuristic) ─────────────────────────────────

_HEALTH_KEYWORDS = {
    # Physical
    "pain", "ache", "hurt", "fever", "cold", "cough", "nausea", "vomit",
    "diarrhea", "constipation", "bloat", "digestion", "stomach", "bowel",
    "blood", "pressure", "sugar", "diabetes", "cholesterol", "weight",
    "exercise", "sleep", "fatigue", "tired", "energy", "nutrition", "diet",
    "vitamin", "mineral", "supplement", "medicine", "medication", "drug",
    "prescription", "doctor", "hospital", "clinic", "therapy", "treatment",
    "symptom", "diagnosis", "lab", "report", "test", "scan", "xray", "mri",
    "allergy", "infection", "inflammation", "immune", "vaccine", "surgery",
    "recovery", "rehabilitation", "ayurvedic", "ayurveda", "herbal", "remedy",
    # Mental / emotional
    "mental", "anxiety", "depress", "stress", "worry", "panic", "fear",
    "mood", "emotion", "feeling", "sad", "happy", "calm", "relax", "meditat",
    "mindful", "breath", "overwhelm", "burnout", "trauma", "grief", "loss",
    "social media", "instagram", "screen", "addiction", "habit", "urge",
    "crave", "compulsion", "impulse", "loneliness", "isolated", "therapy",
    "psycholog", "psychiatr", "counsel",
    # General wellness
    "health", "wellness", "wellbeing", "fit", "healthy", "unhealthy",
    "lifestyle", "routine", "water", "hydrat", "fast", "detox",
}

# Purely off-topic domains (hard block)
_OFF_TOPIC_SIGNALS = {
    "stock", "invest", "crypto", "finance", "loan", "mortgage",
    "lawsuit", "attorney", "legal advice", "tax", "insurance claim",
    "recipe", "travel", "hotel", "flight", "visa",
    "code", "programming", "javascript", "python script",
    "movie", "song", "music", "game", "sport",
}

# ── Crisis signals ─────────────────────────────────────────────────────────────

_CRISIS_PHRASES = [
    r"\bsuicid",
    r"\bkill\s+myself\b",
    r"\bend\s+my\s+life\b",
    r"\bwant\s+to\s+die\b",
    r"\bdon['\u2019]?t\s+want\s+to\s+live\b",
    r"\bno\s+reason\s+to\s+live\b",
    r"\bself[- ]?harm\b",
    r"\bcut\s+myself\b",
    r"\bhurt\s+myself\b",
    r"\btake\s+my\s+own\s+life\b",
    r"\bthinking\s+about\s+dying\b",
    r"\bbetter\s+off\s+dead\b",
]

_CRISIS_RE = re.compile("|".join(_CRISIS_PHRASES), re.IGNORECASE)


@dataclass
class GuardrailResult:
    is_allowed: bool
    is_crisis: bool
    block_reason: str = ""   # non-empty only when is_allowed=False


def check_message(text: str) -> GuardrailResult:
    """
    Returns a GuardrailResult for the given user message.

    Priority:
      crisis detected  → allowed=True, crisis=True  (we don't block, we support)
      off-topic        → allowed=False
      health-related   → allowed=True
      ambiguous        → allowed=True  (lean permissive to avoid mis-blocking
                          mental health / emotional topics)
    """
    lower = text.lower()

    # 1. Crisis check — never block, always respond with care
    if _CRISIS_RE.search(text):
        logger.warning("Crisis signal detected in message")
        return GuardrailResult(is_allowed=True, is_crisis=True)

    # 2. Hard off-topic block (only if zero health signals present)
    has_health = any(kw in lower for kw in _HEALTH_KEYWORDS)
    has_off_topic = any(kw in lower for kw in _OFF_TOPIC_SIGNALS)

    if has_off_topic and not has_health:
        return GuardrailResult(
            is_allowed=False,
            is_crisis=False,
            block_reason=(
                "I'm here to support your health and wellness journey. "
                "I'm not able to help with that topic. "
                "Is there anything health-related I can help you with?"
            ),
        )

    # 3. Very short / greeting messages — allow (user is starting a conversation)
    if len(text.strip()) < 30:
        return GuardrailResult(is_allowed=True, is_crisis=False)

    # 4. Default: allow (lean permissive for mental/emotional wellbeing)
    return GuardrailResult(is_allowed=True, is_crisis=False)
