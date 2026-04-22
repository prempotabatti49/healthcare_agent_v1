"""
SuperMemory service — single interface for both:
  1. Document storage  (doctor reports, lab results, …)
  2. Conversational memory  (symptoms, events, treatments, …)

Each user gets an isolated SuperMemory container:
  container_tag = f"{prefix}_{user_id}"

SuperMemory handles chunking, embedding, and retrieval automatically.
Metadata keeps must-have context queryable.
"""
from __future__ import annotations

import logging
from typing import Any, Optional
from supermemory import Supermemory

from app.config.secrets import get_secret
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
_settings = get_settings()


class SuperMemoryService:
    """Thread-safe, lazy-initialised SuperMemory client wrapper."""

    def __init__(self) -> None:
        self._client: Optional[Supermemory] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    @property
    def client(self) -> Supermemory:
        if self._client is None:
            api_key = get_secret("SUPERMEMORY_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "SUPERMEMORY_API_KEY is not set. "
                    "Add it to your .env file."
                )
            self._client = Supermemory(api_key=api_key)
        return self._client

    # ── Container helpers ─────────────────────────────────────────────────────

    def _container(self, user_id: str) -> str:
        """Return user-scoped container tag."""
        return f"{_settings.supermemory_container_prefix}_{user_id}"

    # ── Documents (vector DB layer) ───────────────────────────────────────────

    def add_document(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any],
    ) -> str | None:
        """
        Store a processed document (report, prescription, etc.) in the
        vector DB layer. SuperMemory chunks and embeds automatically.

        Returns the created document id on success, None on failure.
        """
        try:
            print("Adding document to SuperMemory for user:", user_id)
            result = self.client.add(
                content=content,
                container_tag=self._container(user_id),
                metadata={
                    "entry_type": "document",
                    **metadata,
                },
            )
            print("Document added to SuperMemory for user:", user_id)
            doc_id = getattr(result, "id", None) or str(result)
            logger.info("SuperMemory document stored: %s for user %s", doc_id, user_id)
            return doc_id
        except Exception as exc:
            logger.error("SuperMemory add_document failed: %s", exc)
            return None

    # ── Memory (conversational layer) ─────────────────────────────────────────

    def add_memory(
        self,
        user_id: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> str | None:
        """
        Store a conversational health event or exchange.
        SuperMemory's memory algo creates rich relational nodes automatically.

        content  — typically the full user+assistant turn, or a structured
                   health note (e.g. "User reported bloating after eating pizza
                   at 2 AM. Treatment: ayurvedic herbs. Relief after 3 days.")
        """
        try:
            result = self.client.add(
                content=content,
                container_tag=self._container(user_id),
                metadata={
                    "entry_type": "memory",
                    **(metadata or {}),
                },
            )
            mem_id = getattr(result, "id", None) or str(result)
            logger.info("SuperMemory memory stored for user %s", user_id)
            return mem_id
        except Exception as exc:
            logger.error("SuperMemory add_memory failed: %s", exc)
            return None

    # ── Search ────────────────────────────────────────────────────────────────

    def search(
        self,
        user_id: str,
        query: str,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        """
        Unified search across both documents and memories for a user.
        Returns a list of result dicts with 'content' and 'metadata' keys.
        """
        try:
            results = self.client.search.memories(
                q=query,
                container_tag=self._container(user_id),
                limit=limit,
                search_mode="hybrid"
            )
            items = []
            for r in results.results:
                items.append({
                    "content": getattr(r, "memory", str(r)),
                    "metadata": getattr(r, "metadata", {}),
                    "score": getattr(r, "score", None),
                })
            return items
        except Exception as exc:
            logger.error("SuperMemory search failed: %s", exc)
            return []

    def search_documents(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search only document entries (entry_type == document)."""
        results = self.search(user_id, query, limit=limit * 2)
        return [r for r in results if r.get("metadata", {}).get("entry_type") == "document"][:limit]

    def search_memories(
        self,
        user_id: str,
        query: str,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Search only conversational memory entries."""
        results = self.search(user_id, query, limit=limit * 2)
        return [r for r in results if r.get("metadata", {}).get("entry_type") == "memory"][:limit]

    # ── Context builder ───────────────────────────────────────────────────────

    def build_context_block(
        self,
        user_id: str,
        query: str,
        max_results: int = 6,
    ) -> str:
        """
        Return a formatted context string ready to inject into the LLM prompt.
        Pulls relevant memories + documents and formats them clearly.
        """
        results = self.search(user_id, query, limit=max_results)
        if not results:
            return ""

        lines = ["=== Your Relevant Health History ==="]
        for i, r in enumerate(results, 1):
            entry_type = r.get("metadata", {}).get("entry_type", "record")
            lines.append(f"[{i}] ({entry_type.upper()}) {r['content']}")
        lines.append("=== End of History ===")
        return "\n".join(lines)


# Singleton — import and use directly
supermemory_service = SuperMemoryService()
