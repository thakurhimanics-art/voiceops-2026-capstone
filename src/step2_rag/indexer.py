"""Knowledge Base Indexer enforcing policy precedence and exclusion of superseded policies."""
from typing import List, Dict, Any, Optional
from src.step2_rag.parser import parse_kb_documents, parse_products_catalog

# Precedence hierarchy: Policy > Agent Guide > Help > FAQ > Marketing
DOC_TYPE_WEIGHTS = {
    "policy": 1.5,
    "agent_guide": 1.3,
    "help": 1.1,
    "catalog": 1.1,
    "faq": 0.8,
    "marketing": 0.5,
    "meta": 0.7,
}


class KnowledgeIndexer:
    def __init__(self, include_superseded: bool = False):
        self.include_superseded = include_superseded
        self.authoritative_chunks: List[Dict[str, Any]] = []
        self.superseded_chunks: List[Dict[str, Any]] = []
        self.catalog_chunks: List[Dict[str, Any]] = []
        self.all_indexed_chunks: List[Dict[str, Any]] = []
        self.build_index()

    def build_index(self):
        """Build chunks list respecting policy status and precedence."""
        kb_chunks = parse_kb_documents()
        product_chunks = parse_products_catalog()

        self.authoritative_chunks = []
        self.superseded_chunks = []
        self.catalog_chunks = product_chunks

        for chunk in kb_chunks:
            # Check document status
            if chunk.get("status") == "superseded":
                self.superseded_chunks.append(chunk)
            else:
                self.authoritative_chunks.append(chunk)

        # Base pool for retrieval
        if self.include_superseded:
            self.all_indexed_chunks = self.authoritative_chunks + self.superseded_chunks + self.catalog_chunks
        else:
            # Exclude superseded policies from authoritative retrieval
            self.all_indexed_chunks = self.authoritative_chunks + self.catalog_chunks

    def get_chunk_by_section_id(self, section_id: str) -> Optional[Dict[str, Any]]:
        """Find chunk by exact section ID or catalog SKU."""
        clean_id = section_id.strip()
        for chunk in self.all_indexed_chunks:
            if chunk["section_id"].lower() == clean_id.lower():
                return chunk
        # Check superseded if not found
        for chunk in self.superseded_chunks:
            if chunk["section_id"].lower() == clean_id.lower():
                return chunk
        return None
