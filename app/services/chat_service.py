"""
Chat Service
============
Orchestrates the full conversation pipeline:

  1. Run guardrails (healthcare relevance + crisis detection)
  2. Get or create a conversation in PostgreSQL
  3. Load recent conversation history
  4. Reflection — classify the request and either:
       a. Return clarifying questions (personalised request, gaps exist), OR
       b. Expand into multiple search queries (personalised request, ready), OR
       c. Use message as-is (simple factual question)
  5. Fetch relevant memory + document context from SuperMemory
       — All expanded queries run in parallel via asyncio.gather
  6. Build the system prompt with merged context injected
  7. Call the LLM and get a response
  8. Persist: save messages to PostgreSQL
  9. Extract and store health facts in SuperMemory (only confirmed facts)
 10. Return a structured ChatResponse

Crisis flow:
  Detected → skip reflection → inject crisis helplines into the response
           → create a CrisisAlert record so admins can follow up
"""
from __future__ import annotations

import asyncio
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.db.queries import (
    create_conversation,
    create_crisis_alert,
    get_conversation,
    get_conversation_messages,
    save_message,
)
from app.models.db_models import MessageRole
from app.models.pydantic_models import ChatResponse
from app.services.guardrails import check_message
from app.services.llm import LLMMessage, get_llm
from app.services.supermemory import supermemory_service
from app.utils.crisis_resources import CRISIS_RESOURCES_TEXT
from app.utils.quotes import get_daily_quote

logger = logging.getLogger(__name__)

HISTORY_WINDOW = 15  # number of past messages to include in LLM context

DISCLAIMER = (
    "\n\n---\n*Sunflower is a wellness companion, not a medical provider. "
    "Please consult a qualified doctor for medical advice.*"
)

# ── Prompts ───────────────────────────────────────────────────────────────────
def reflection_prompt(user_message: str, history_snippet: str) -> str:
    """Prompt to classify the user's request and generate clarifying questions if needed."""
    REFLECTION_PROMPT = f"""
    # Role
    You are a senior healthcare professional (physician, clinical dietitian, or allied health specialist) with deep expertise in evidence-based medicine, nutrition, and lifestyle interventions. Your task is NOT to answer the user's question yet — it is to decide whether the question needs clarification before a high-quality, personalized answer can be given, and if so, to generate those clarifying questions.

    - User's current message:
    {{user_message}}

    # Task
    Classify the user's message into one of two modes, then produce output accordingly.

    ## Mode 1: STATUS_QUO
    Use when the message is:
    - A factual or definitional question ("what is cholesterol?", "how does insulin work?")
    - A general explanation request ("explain intermittent fasting")
    - A request for population-level guidance ("is coffee bad for you?")
    - Any question that can be answered well from general medical knowledge without personal context

    Output: empty items list.

    ## Mode 2: REFLECTED_QUESTIONS
    Use when the message requires personalization to answer well:
    - Diet, meal, or nutrition plans
    - Exercise or training programs
    - Symptom analysis or triage
    - Medication questions tied to the individual
    - Lifestyle recommendations
    - Interpretation of personal medical reports, labs, or tracked data
    - Any "for me" framing implying individualized advice

    ### Reflection process (internal — do not output)
    1. Identify what the user is actually asking for (the underlying goal).
    2. List the minimum information a clinician would need to give a safe, specific, useful answer.
    3. Remove anything already provided in the history or current message.
    4. Combine closely related sub-facts into a single question (e.g. age + sex + height + weight in one question).

    ### Question-crafting rules (these questions will be used for vector-DB retrieval)
    - Write each question as a FULL standalone sentence that makes sense without the user's original message as context. A retriever will embed these in isolation.
    - Use semantically rich, specific phrasing. Prefer "What is the user's current weight, height, age, and sex?" over "Stats?" or "Body info?".
    - Keep each question focused on one topic or one tight cluster of related facts — do not merge unrelated areas.
    - Generate only as many questions as genuinely needed (typically 3–7). No filler, no padding.
    - Cover essentials in roughly this priority order: demographics → medical conditions & medications → goals → constraints/preferences → current baseline habits.
    - Do NOT ask about information the user has already provided in the history or current message.

    # Output format
    Return ONLY valid JSON. No markdown, no code fences, no commentary.

    Schema:
    {{
    "mode": "STATUS_QUO" | "REFLECTED_QUESTIONS",
    "items": []
    }}

    # Examples

    Example 1
    user_message: "What is LDL cholesterol?"
    output:
    {{"mode": "STATUS_QUO", "items": []}}

    Example 2
    user_message: "Give me a diet plan."
    output:
    {{
    "mode": "REFLECTED_QUESTIONS",
    "items": [
        "What are the user's age, sex, height, and current weight?",
        "What is the user's primary health goal — weight loss, muscle gain, disease management, or general wellness?",
        "Does the user have any dietary preferences or restrictions such as vegetarian, vegan, halal, kosher, or food allergies?",
        "Does the user have any existing medical conditions (diabetes, hypertension, kidney disease, thyroid disorders, etc.) or take medications that affect nutrition?",
        "What does the user's current daily eating pattern look like, including meal timing and approximate calorie intake?",
        "What is the user's typical physical activity level and weekly exercise routine?"
    ]
    }}

    Example 3
    user_message: "I've been getting headaches every afternoon for the past two weeks. What could be causing it?"
    output:
    {{
    "mode": "REFLECTED_QUESTIONS",
    "items": [
        "What is the character of the headache — location on the head, throbbing versus dull, one-sided versus both sides, and severity on a 1 to 10 scale?",
        "What associated symptoms accompany the headache, such as nausea, visual changes, light or sound sensitivity, or neck stiffness?",
        "What is the user's daily hydration, caffeine intake, and meal timing pattern, particularly in the hours before the headache starts?",
        "What has the user's sleep duration and quality been over the past two weeks?",
        "How much screen time does the user have, and what is their posture during the hours leading up to the afternoon onset?",
        "Does the user have a relevant medical history such as migraines, hypertension, or recent head injury, and what medications are they currently taking?"
    ]
    }}

    Example 4
    user_message: "Is coffee bad for you?"
    output:
    {{"mode": "STATUS_QUO", "items": []}}

    # Critical rules
    - Output ONLY the JSON object. No preamble, no explanation, no markdown fences, no trailing text.
    - mode values must be EXACTLY "STATUS_QUO" or "REFLECTED_QUESTIONS" (uppercase with underscore).
    - When in doubt, prefer STATUS_QUO if the question is phrased generally, and REFLECTED_QUESTIONS if it is phrased personally ("me", "my", "I", "my report").
    - Never invent clarifying questions just to fill the list. An empty list is always the correct output for STATUS_QUO.
    - Never answer the health question itself — only classify and, if needed, ask.
    """
    return REFLECTION_PROMPT

FACT_EXTRACTION_PROMPT = """\
You are a health fact extractor. Given a conversation exchange between a user and a \
health AI, extract only concrete, confirmed facts about the user's health, body, diet, \
medical history, symptoms, or lifestyle.

Rules:
- Only extract facts the user explicitly stated about themselves (not questions or hypotheticals).
- Do NOT extract advice given by the AI.
- Do NOT extract questions, hypotheticals, or things the user is "considering".
- If there are no real user health facts, respond with exactly: NONE

Return a concise bullet-point list of facts, or NONE.

Exchange:
User: {user_message}
AI: {ai_response}
"""

SYSTEM_PROMPT_TEMPLATE = """\
You are Sunflower, a warm, empathetic, and knowledgeable personal health \
companion. You help individuals understand their health journey, recall past \
health events, and receive wellness guidance informed by their own history.

CORE RULES:
1. ONLY discuss health and wellness topics (physical, mental, emotional, \
nutrition, sleep, exercise, lifestyle). Gently redirect any off-topic queries.
2. You are NOT a medical doctor. Never provide a clinical diagnosis or prescribe \
medication. Always encourage consulting a qualified healthcare professional.
3. Reference the user's personal health history (from CONTEXT below) whenever \
relevant. Remind them of what worked and what didn't for them specifically.
4. Be empathetic, non-judgmental, and supportive — especially for mental health.
5. If the user has uploaded doctor's reports or notes, reference them accurately.
6. End every substantive response with the medical disclaimer.

{context_block}

Today is {today}. Respond in a warm, conversational, and concise manner.
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_system_prompt(context_block: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        context_block=context_block,
        today=datetime.now(timezone.utc).strftime("%B %d, %Y"),
    )


def _parse_reflection(raw: str) -> tuple[str, list[str]]:
    """
    Parse reflection output into (mode, items).
    mode is "clarify" or "queries".
    items is a list of questions or search queries.
    """
    import json
    raw = raw.replace("\n", "").strip().replace("```json", "").replace("```", "")  # clean up common formatting artifacts
    print(raw)
    reflection = json.loads(raw)  # validate JSON format, but we'll parse manually to be more flexible
    mode = reflection.get("mode", "").lower()
    items = reflection.get("items", [])

    return mode, items


def _reflect(user_message: str, history: list) -> tuple[str, list[str]]:
    """
    Single LLM call that:
    - Classifies the request (simple vs personalised)
    - Either returns clarifying questions ("clarify", [questions])
      or expanded search queries ("queries", [queries])

    Falls back to ("queries", [user_message]) on any error.
    """
    try:
        history_snippet = "\n".join(
            f"{m.role.value.capitalize()}: {m.content[:200]}"
            for m in history[-6:]
        ) or "No prior conversation."
        print(f"history_snippet: {history_snippet}\n\nuser_message: {user_message}")  # Debug log

        llm = get_llm()
        print("instantiated llm for reflection")  # Debug log
        prompt = reflection_prompt(user_message, history_snippet)
        print(prompt)
        raw = llm.chat(
            messages=[LLMMessage(role="user", content=prompt)],
            temperature=0.0,
        )
        print(f"RAW REFLECTION OUTPUT: {raw}")  # Debug log
        mode, items = _parse_reflection(raw)
        # Ensure at least the original message is always a query
        if mode == "STATUS QUO":
            items = [user_message]
        return mode, items
    except Exception as exc:
        logger.warning("Reflection failed, using original message as query: %s", exc)
        return "queries", [user_message]


async def _search_supermemory_parallel(user_id: str, queries: list[str]) -> list[dict]:
    """
    Run all SuperMemory search queries in parallel using asyncio.gather.
    The supermemory client is synchronous, so each call runs in a thread executor.
    Returns a deduplicated list of result dicts.
    """
    loop = asyncio.get_event_loop()
    executor = ThreadPoolExecutor(max_workers=len(queries))

    async def _search_one(query: str):
        return await loop.run_in_executor(
            executor,
            lambda q=query: supermemory_service.search(user_id, q, limit=6),
        )

    all_results = await asyncio.gather(*[_search_one(q) for q in queries])

    # Deduplicate by content string
    seen: set[str] = set()
    merged: list[dict] = []
    for result_list in all_results:
        for r in result_list:
            content = r.get("content", "")
            if content and content not in seen:
                seen.add(content)
                merged.append(r)

    executor.shutdown(wait=False)
    return merged


def _build_context_block(results: list[dict]) -> str:
    """Format merged SuperMemory results into a context string for the prompt."""
    if not results:
        return ""
    lines = ["=== Your Relevant Health History ==="]
    for i, r in enumerate(results, 1):
        entry_type = r.get("metadata", {}).get("entry_type", "record")
        lines.append(f"[{i}] ({entry_type.upper()}) {r['content']}")
    lines.append("=== End of History ===")
    return "\n".join(lines)


def _extract_health_facts(user_message: str, ai_response: str) -> Optional[str]:
    """
    Use the LLM to extract confirmed health facts from the exchange.
    Returns a string of facts to store, or None if nothing worth storing.
    """
    try:
        llm = get_llm()
        result = llm.chat(
            [LLMMessage(role="user", content=FACT_EXTRACTION_PROMPT.format(
                user_message=user_message,
                ai_response=ai_response,
            ))],
            temperature=0.0,
            max_tokens=300,
        ).strip()
        if result.upper() == "NONE" or not result:
            return None
        return result
    except Exception as exc:
        logger.warning("Fact extraction failed (skipping memory storage): %s", exc)
        return None


# ── Main entry point ──────────────────────────────────────────────────────────

async def process_message(
    db: Session,
    user_id: str,
    message_text: str,
    conversation_id: Optional[str] = None,
    include_daily_quote: bool = False,
) -> ChatResponse:
    """
    Async entry point. Takes an open DB session (passed in from the route handler).
    """
    import uuid

    # ── 1. Guardrails ─────────────────────────────────────────────────────────
    guard = check_message(message_text)

    if not guard.is_allowed:
        return ChatResponse(
            conversation_id=conversation_id or str(uuid.uuid4()),
            message_id=str(uuid.uuid4()),
            response=guard.block_reason,
        )

    # ── 2. Get or create conversation ─────────────────────────────────────────
    if conversation_id:
        conv = get_conversation(db, conversation_id, user_id)
    else:
        conv = None

    if not conv:
        conv = create_conversation(db, user_id)

    # ── 3. Load conversation history ──────────────────────────────────────────
    history = get_conversation_messages(db, conv.id, limit=HISTORY_WINDOW)

    # ── 4. Reflection (skip for crisis — respond immediately) ─────────────────
    # search_queries = [message_text]  # default: search with original message

    print("REFLECTING")
    mode, search_queries = _reflect(message_text, history)
    print("REFLECTION RESULT: mode=%s, items=%s", mode, search_queries)
    print(f"search_queries: {search_queries}")

    # if mode == "clarify" and items:
    #     clarification = (
    #         "Before I give you a personalised answer, I have a few quick questions:\n\n"
    #         + "\n".join(f"{i}. {q}" for i, q in enumerate(items, 1))
    #         + "\n\nFeel free to answer what you know — I'll work with whatever you share!"
    #     )
    #     save_message(db, conv.id, MessageRole.user, message_text,
    #                  was_crisis_flagged=False, memory_context_used=False)
    #     asst_clarify = save_message(db, conv.id, MessageRole.assistant, clarification,
    #                                 was_crisis_flagged=False, memory_context_used=False)
    #     db.commit()
    #     return ChatResponse(
    #         conversation_id=conv.id,
    #         message_id=asst_clarify.id,
    #         response=clarification,
    #         was_crisis_flagged=False,
    #         memory_context_used=False,
    #     )

    # mode == "queries": use expanded queries for SuperMemory

    # ── 5. Fetch context from SuperMemory (all queries in parallel) ───────────
    supermemory_results = await _search_supermemory_parallel(user_id, search_queries)
    context_block = _build_context_block(supermemory_results)
    memory_used = bool(context_block)

    # ── 6. Build system prompt ────────────────────────────────────────────────
    system_prompt = _build_system_prompt(context_block)

    if guard.is_crisis:
        system_prompt = (
            "IMPORTANT: The user may be experiencing suicidal ideation or severe "
            "distress. Respond with deep empathy. Provide crisis helpline numbers. "
            "Do NOT minimise their feelings. Encourage them to seek immediate help.\n\n"
            + system_prompt
        )

    # ── 7. Call the LLM ───────────────────────────────────────────────────────
    llm_messages = [LLMMessage(role="system", content=system_prompt)]
    llm_messages += [LLMMessage(role=m.role.value, content=m.content) for m in history]
    llm_messages.append(LLMMessage(role="user", content=message_text))

    llm = get_llm()
    ai_response = llm.chat(llm_messages, temperature=0.7)

    if guard.is_crisis:
        ai_response = ai_response + "\n\n" + CRISIS_RESOURCES_TEXT

    ai_response += DISCLAIMER

    # ── 8. Persist to PostgreSQL ──────────────────────────────────────────────
    if guard.is_crisis:
        create_crisis_alert(db, user_id, message_text)

    save_message(
        db, conv.id, MessageRole.user, message_text,
        was_crisis_flagged=guard.is_crisis,
        memory_context_used=memory_used,
    )
    asst_msg = save_message(
        db, conv.id, MessageRole.assistant, ai_response,
        was_crisis_flagged=guard.is_crisis,
        memory_context_used=memory_used,
    )
    db.commit()

    # ── 9. Store confirmed health facts in SuperMemory ────────────────────────
    facts = _extract_health_facts(message_text, ai_response)
    if facts:
        dated_facts = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%d')}]\n{facts}"
        supermemory_service.add_memory(
            user_id,
            content=dated_facts,
            metadata={"was_crisis": guard.is_crisis},
        )
        logger.info("SuperMemory: stored facts for user %s", user_id)
    else:
        logger.info("SuperMemory: no storable facts in exchange for user %s", user_id)

    # ── 10. Optional daily quote ──────────────────────────────────────────────
    daily_quote = None
    if include_daily_quote:
        q = get_daily_quote()
        daily_quote = f'"{q.quote}" — {q.author or "Unknown"}'

    print(f"search_queries: {search_queries}")
    print(f"supermemory_results: {supermemory_results}")
    print(f"context_block: {context_block}")
    return ChatResponse(
        conversation_id=conv.id,
        message_id=asst_msg.id,
        response=ai_response,
        was_crisis_flagged=guard.is_crisis,
        memory_context_used=memory_used,
        daily_quote=daily_quote,
        supermemory_results=supermemory_results,
        search_queries=search_queries,
        context_block=context_block,
    )
