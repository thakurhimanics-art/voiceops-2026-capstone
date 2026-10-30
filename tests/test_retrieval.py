"""Unit tests for knowledge base parsing, section IDs, precedence, and anti-superseded checks."""
from src.step2_rag.parser import parse_kb_documents, parse_products_catalog
from src.step2_rag.indexer import KnowledgeIndexer
from src.step2_rag.retriever import HybridRetriever


def test_kb_section_parsing():
    chunks = parse_kb_documents()
    assert len(chunks) > 20
    section_ids = {c["section_id"] for c in chunks}
    # Check key section IDs exist
    assert "RET-2" in section_ids
    assert "REF-2" in section_ids
    assert "DWM-1" in section_ids
    assert "DEL-4" in section_ids
    assert "ESC-1" in section_ids
    assert "IDV-2" in section_ids


def test_superseded_policy_excluded():
    indexer = KnowledgeIndexer(include_superseded=False)
    indexed_doc_ids = {c["doc_id"] for c in indexer.all_indexed_chunks}
    # POL-RET-v3 is superseded, should not be in authoritative pool
    assert "POL-RET-v3" not in indexed_doc_ids

    # But POL-RET (v4) is present
    assert "POL-RET" in indexed_doc_ids


def test_support_logs_not_in_index():
    indexer = KnowledgeIndexer()
    for c in indexer.all_indexed_chunks:
        assert "support_logs" not in c["source"]
        assert c.get("doc_type") != "support_log"


def test_catalog_sku_retrieval():
    retriever = HybridRetriever()
    results = retriever.retrieve("SKU ELE-0012 warranty claim details", top_k=3)
    retrieved_ids = [c["section_id"] for c in results]
    assert "products.csv:ELE-0012" in retrieved_ids or "WAR-2" in retrieved_ids


def test_faq_trap_avoidance_on_wallet():
    retriever = HybridRetriever()
    results = retriever.retrieve("How fast are refunds to the ZentroMart Wallet?", top_k=3)
    retrieved_ids = [c["section_id"] for c in results]
    # REF-2 should be in top results, FAQ-1 should NOT be top-1
    assert "REF-2" in retrieved_ids
    assert results[0]["section_id"] != "FAQ-1"
