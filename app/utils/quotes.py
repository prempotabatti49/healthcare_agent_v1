"""
Health Quotes
=============
Curated positive quotes covering major physical and mental health areas.
Served daily (or on-demand) in chat or as notifications.
"""
from __future__ import annotations

import random
from datetime import date
from typing import Optional

from app.models.pydantic_models import HealthQuote


_QUOTES: list[dict] = [
    # ── Digestion & Gut Health ─────────────────────────────────────────────
    {"quote": "All disease begins in the gut.", "author": "Hippocrates", "category": "digestion"},
    {"quote": "Your gut is your second brain. Nourish it wisely.", "author": None, "category": "digestion"},
    {"quote": "Let food be thy medicine and medicine be thy food.", "author": "Hippocrates", "category": "nutrition"},
    {"quote": "A healthy outside starts from the inside.", "author": "Robert Urich", "category": "nutrition"},

    # ── Mental Health & Emotions ───────────────────────────────────────────
    {"quote": "You don't have to be positive all the time. It's perfectly okay to feel sad, angry, or upset. Having feelings doesn't make you a negative person. It makes you human.", "author": "Lori Deschene", "category": "mental_health"},
    {"quote": "Mental health is not a destination, but a process. It's about how you drive, not where you're going.", "author": "Noam Shpancer", "category": "mental_health"},
    {"quote": "There is hope, even when your brain tells you there isn't.", "author": "John Green", "category": "mental_health"},
    {"quote": "Self-care is not selfish. You cannot pour from an empty cup.", "author": None, "category": "mental_health"},
    {"quote": "You are allowed to be both a masterpiece and a work in progress simultaneously.", "author": "Sophia Bush", "category": "mental_health"},

    # ── Sleep ──────────────────────────────────────────────────────────────
    {"quote": "Sleep is the best meditation.", "author": "Dalai Lama", "category": "sleep"},
    {"quote": "A good laugh and a long sleep are the best cures in the doctor's book.", "author": "Irish Proverb", "category": "sleep"},
    {"quote": "The best bridge between despair and hope is a good night's sleep.", "author": "Matthew Walker", "category": "sleep"},

    # ── Stress & Anxiety ───────────────────────────────────────────────────
    {"quote": "Breathe. You are strong enough to handle your challenges.", "author": None, "category": "stress"},
    {"quote": "Anxiety is the dizziness of freedom.", "author": "Søren Kierkegaard", "category": "stress"},
    {"quote": "You can't always control what goes on outside, but you can always control what goes on inside.", "author": "Wayne Dyer", "category": "stress"},
    {"quote": "In the middle of difficulty lies opportunity — and in the middle of anxiety, lies growth.", "author": None, "category": "stress"},

    # ── Social Media & Digital Wellness ───────────────────────────────────
    {"quote": "Almost everything will work again if you unplug it for a few minutes, including you.", "author": "Anne Lamott", "category": "digital_wellness"},
    {"quote": "The present moment is the only moment available to us, and it is the door to all moments.", "author": "Thich Nhat Hanh", "category": "digital_wellness"},
    {"quote": "Don't let the highlight reel of others' lives dim your own.", "author": None, "category": "digital_wellness"},

    # ── Exercise & Movement ────────────────────────────────────────────────
    {"quote": "Take care of your body. It's the only place you have to live.", "author": "Jim Rohn", "category": "exercise"},
    {"quote": "Movement is medicine for creating change in a person's physical, emotional, and mental states.", "author": "Carol Welch", "category": "exercise"},
    {"quote": "Your body can stand almost anything. It's your mind that you have to convince.", "author": None, "category": "exercise"},

    # ── General Wellness ───────────────────────────────────────────────────
    {"quote": "Health is not valued until sickness comes.", "author": "Thomas Fuller", "category": "general"},
    {"quote": "The greatest wealth is health.", "author": "Virgil", "category": "general"},
    {"quote": "It is health that is real wealth and not pieces of gold and silver.", "author": "Mahatma Gandhi", "category": "general"},
    {"quote": "To keep the body in good health is a duty, otherwise we shall not be able to keep our mind strong and clear.", "author": "Buddha", "category": "general"},
    {"quote": "Knowing yourself is the beginning of all wisdom.", "author": "Aristotle", "category": "general"},
    {"quote": "Small steps every day add up to big changes over time.", "author": None, "category": "general"},
    {"quote": "Be patient with yourself. Self-growth is tender; it's holy ground.", "author": "Stephen Covey", "category": "general"},
]


def get_daily_quote(category: Optional[str] = None) -> HealthQuote:
    """
    Returns a deterministic daily quote (same quote all day for a user).
    If category is specified, filter to that category first.
    """
    pool = _QUOTES
    if category:
        pool = [q for q in _QUOTES if q["category"] == category] or _QUOTES

    # Deterministic index based on day-of-year
    index = date.today().timetuple().tm_yday % len(pool)
    q = pool[index]
    return HealthQuote(quote=q["quote"], author=q.get("author"), category=q["category"])


def get_random_quote(category: Optional[str] = None) -> HealthQuote:
    """Returns a random quote, optionally filtered by category."""
    pool = _QUOTES
    if category:
        pool = [q for q in _QUOTES if q["category"] == category] or _QUOTES
    q = random.choice(pool)
    return HealthQuote(quote=q["quote"], author=q.get("author"), category=q["category"])


def get_all_categories() -> list[str]:
    return sorted({q["category"] for q in _QUOTES})
