"""Research memory - indexed research reports for retrieval augmented generation."""

from __future__ import annotations

from datetime import UTC, datetime

import structlog

from .vector_store import vector_store

logger = structlog.get_logger()


class ResearchMemory:
    """Stores and retrieves research reports for RAG."""

    COLLECTION = "research"

    async def index_report(self, report: dict) -> str:
        """Index a research report for future retrieval."""
        content = report.get("synthesis", "") or report.get("content", "")
        if not content:
            return ""
        metadata = {
            "collection": self.COLLECTION,
            "symbol": report.get("symbol", ""),
            "report_type": report.get("report_type", "general"),
            "provider": report.get("provider", ""),
            "indexed_at": datetime.now(UTC).isoformat(),
        }
        doc_id = await vector_store.add(content=content, metadata=metadata)
        logger.info("research_indexed", doc_id=doc_id, symbol=metadata["symbol"])
        return doc_id

    async def search_reports(self, query: str, top_k: int = 5) -> list[dict]:
        """Search past research reports."""
        results = await vector_store.search(
            query, top_k=top_k, filter_metadata={"collection": self.COLLECTION}
        )
        return results

    async def build_research_context(self, query: str, symbol: str = "", top_k: int = 3) -> str:
        """Build context from relevant past research."""
        filter_meta = {"collection": self.COLLECTION}
        if symbol:
            filter_meta["symbol"] = symbol
        results = await vector_store.search(query, top_k=top_k, filter_metadata=filter_meta)
        if not results:
            return ""
        parts = ["Relevant past research:"]
        for r in results:
            if r["score"] > 0.2:
                sym = r["metadata"].get("symbol", "N/A")
                parts.append(f"[{sym}] {r['content'][:300]}")
        return "\n\n".join(parts)


# Global instance
research_memory = ResearchMemory()
