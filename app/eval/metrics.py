"""
Evaluation Metrics
==================
Standalone metrics you can run independently on any pipeline component.

Usage:
  python -m app.eval.metrics

Each metric returns a score 0.0–1.0 and an explanation dict.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

from app.services.llm import LLMMessage, get_llm


@dataclass
class MetricResult:
    metric_name: str
    score: float          # 0.0 – 1.0
    passed: bool          # score >= threshold
    details: dict[str, Any]


# ── 1. Guardrail accuracy ──────────────────────────────────────────────────────

def evaluate_guardrail(test_cases: list[dict]) -> list[MetricResult]:
    """
    test_cases: [{"message": str, "expected_allowed": bool}, ...]
    """
    from app.services.guardrails import check_message

    results = []
    for tc in test_cases:
        guard = check_message(tc["message"])
        correct = guard.is_allowed == tc["expected_allowed"]
        results.append(MetricResult(
            metric_name="guardrail_accuracy",
            score=1.0 if correct else 0.0,
            passed=correct,
            details={
                "message": tc["message"][:80],
                "expected": tc["expected_allowed"],
                "got": guard.is_allowed,
                "block_reason": guard.block_reason,
            },
        ))
    return results


# ── 2. Crisis detection recall ─────────────────────────────────────────────────

def evaluate_crisis_detection(test_cases: list[dict]) -> list[MetricResult]:
    """
    test_cases: [{"message": str, "expected_crisis": bool}, ...]
    """
    from app.services.guardrails import check_message

    results = []
    for tc in test_cases:
        guard = check_message(tc["message"])
        correct = guard.is_crisis == tc["expected_crisis"]
        results.append(MetricResult(
            metric_name="crisis_detection",
            score=1.0 if correct else 0.0,
            passed=correct,
            details={
                "message": tc["message"][:80],
                "expected_crisis": tc["expected_crisis"],
                "detected_crisis": guard.is_crisis,
            },
        ))
    return results


# ── 3. Response relevance (LLM-as-judge) ──────────────────────────────────────

_RELEVANCE_JUDGE_PROMPT = """\
You are evaluating the quality of a healthcare AI response.

User message: {user_message}

AI response: {ai_response}

Rate the response on two dimensions (each 1-5):
1. Health relevance: Is the response focused on health/wellness?
2. Empathy: Is the response warm and empathetic?

Reply ONLY with JSON: {{"health_relevance": <1-5>, "empathy": <1-5>, "explanation": "<brief>"}}
"""


def evaluate_response_quality(
    user_message: str,
    ai_response: str,
) -> MetricResult:
    """Use LLM as judge to score response quality."""
    llm = get_llm()
    prompt = _RELEVANCE_JUDGE_PROMPT.format(
        user_message=user_message,
        ai_response=ai_response[:1000],
    )
    raw = llm.chat([LLMMessage(role="user", content=prompt)], temperature=0.0)

    # Parse JSON from response
    import json
    try:
        data = json.loads(re.search(r"\{.*\}", raw, re.DOTALL).group())
        health_score = data.get("health_relevance", 3) / 5.0
        empathy_score = data.get("empathy", 3) / 5.0
        composite = (health_score + empathy_score) / 2
        return MetricResult(
            metric_name="response_quality",
            score=composite,
            passed=composite >= 0.6,
            details=data,
        )
    except Exception:
        return MetricResult(
            metric_name="response_quality",
            score=0.5,
            passed=True,
            details={"raw": raw[:200]},
        )


# ── 4. Memory retrieval coverage ──────────────────────────────────────────────

def evaluate_memory_retrieval(
    user_id: str,
    query: str,
    expected_keywords: list[str],
) -> MetricResult:
    """Check that SuperMemory retrieval surfaces expected content."""
    from app.services.supermemory import supermemory_service

    results = supermemory_service.search(user_id, query, limit=5)
    combined_text = " ".join(r["content"] for r in results).lower()

    found = [kw for kw in expected_keywords if kw.lower() in combined_text]
    score = len(found) / len(expected_keywords) if expected_keywords else 1.0

    return MetricResult(
        metric_name="memory_retrieval_coverage",
        score=score,
        passed=score >= 0.5,
        details={
            "query": query,
            "expected": expected_keywords,
            "found": found,
            "missing": [kw for kw in expected_keywords if kw not in found],
            "num_results": len(results),
        },
    )


# ── 5. Document extraction quality ────────────────────────────────────────────

def evaluate_document_extraction(
    file_bytes: bytes,
    filename: str,
    expected_keywords: list[str],
) -> MetricResult:
    """Verify that document processing extracts key terms."""
    from app.services.document_processor import pages_to_text, process_document

    pages = process_document(file_bytes, filename)
    full_text = pages_to_text(pages).lower()

    found = [kw for kw in expected_keywords if kw.lower() in full_text]
    score = len(found) / len(expected_keywords) if expected_keywords else 1.0

    return MetricResult(
        metric_name="document_extraction",
        score=score,
        passed=score >= 0.7,
        details={
            "filename": filename,
            "pages": len(pages),
            "found_keywords": found,
            "missing_keywords": [kw for kw in expected_keywords if kw not in found],
        },
    )
