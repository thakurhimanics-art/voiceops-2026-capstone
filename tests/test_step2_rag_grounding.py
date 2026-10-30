"""Comprehensive test suite verifying Step 2 RAG retrieval grounding, generalizability, and trap avoidance."""
import pytest
from src.step2_rag.generator import Step2RAG


@pytest.fixture(scope="module")
def rag():
    return Step2RAG()


def test_original_practice_questions(rag):
    """1. Test original practice questions for decision, citation, and factuality."""
    # Wallet refund timeline
    res1 = rag.process_query("How fast are refunds to the ZentroMart Wallet?")
    assert res1["decision"] == "answer"
    assert any("REF-2" in s for s in res1["retrieved_evidence"])
    assert "instant" in res1["reply"].lower() or "2 hours" in res1["reply"].lower()

    # Courier delivery attempts
    res2 = rag.process_query("What happens if courier comes and I am not home?")
    assert res2["decision"] == "answer"
    assert "DEL-3" in res2["retrieved_evidence"]
    assert "3" in res2["reply"]


def test_paraphrased_questions(rag):
    """2. Test paraphrased versions of core policy inquiries."""
    # Paraphrased wallet refund
    p_wallet = rag.process_query("How quickly will my money reflect back into my wallet?")
    assert p_wallet["decision"] == "answer"
    assert "2 hours" in p_wallet["reply"].lower() or "instant" in p_wallet["reply"].lower()

    # Paraphrased missed delivery
    p_missed = rag.process_query("If nobody is present at the address during delivery, will they come again?")
    assert p_missed["decision"] == "answer"
    assert "3" in p_missed["reply"]

    # Paraphrased opened beauty product
    p_beauty = rag.process_query("I opened the seal of the face cream to test it. Can I still return it?")
    assert p_beauty["decision"] == "answer"
    assert "can't be returned" in p_beauty["reply"].lower() or "नहीं" in p_beauty["reply"]


def test_unseen_questions(rag):
    """3. Test completely unseen products and questions."""
    # Unseen unopened beauty product
    res1 = rag.process_query("Can I return an unopened shampoo bottle delivered 4 days ago?")
    assert res1["decision"] == "answer"
    assert "7 days" in res1["reply"] or "seal" in res1["reply"]

    # Unseen grocery item
    res2 = rag.process_query("Can I return fresh grocery fruits delivered yesterday?")
    assert res2["decision"] == "answer"
    assert "cannot be returned" in res2["reply"].lower()

    # Unseen home decor item
    res3 = rag.process_query("What is the return window for a cotton bedsheet delivered 5 days ago?")
    assert res3["decision"] == "answer"
    assert "10 days" in res3["reply"]


def test_questions_requiring_multiple_retrieved_chunks(rag):
    """4. Test inquiries requiring multi-chunk co-retrieval (catalog + policy + calendar)."""
    # SKU ELE-0012 warranty (requires products.csv:ELE-0012 + WAR-2)
    res_sku = rag.process_query("SKU ELE-0012 pe ZentroMart Assured warranty kaise claim karein?")
    assert res_sku["decision"] == "answer"
    assert "products.csv:ELE-0012" in res_sku["retrieved_evidence"]
    assert "WAR-2" in res_sku["retrieved_evidence"]
    assert "12" in res_sku["reply"] and "warranty" in res_sku["reply"].lower()

    # Refund initiated on 17 October 2026 via card (requires REF-2 + KB-00.3 holiday math)
    res_date = rag.process_query("My credit card refund started on 17 October 2026. By which date should it arrive?")
    assert res_date["decision"] == "answer"
    assert "REF-2" in res_date["retrieved_evidence"]
    assert "KB-00.3" in res_date["retrieved_evidence"]
    assert "27 October 2026" in res_date["reply"]  # Skips 18 Oct Sunday & 19 Oct holiday

    # High value damage (requires products.csv:ELE-0023 + DWM-3 + ESC-1)
    res_dmg = rag.process_query("The Kestrel Book 14 Laptop (SKU ELE-0023) I received yesterday has a crack. I want it sorted.")
    assert res_dmg["decision"] == "escalate"
    assert "DWM-3" in res_dmg["retrieved_evidence"] or "ESC-1" in res_dmg["retrieved_evidence"]
    assert "10,000" in res_dmg["reply"] or "Priority" in res_dmg["reply"]


def test_conflicting_or_superseded_information(rag):
    """5. Test policy precedence and suppression of superseded/contradictory documents."""
    # Wallet refund: Policy REF-2 (instant/2h) supersedes FAQ-1 (5-7 days)
    res_wallet = rag.process_query("How fast are refunds to the ZentroMart Wallet?")
    assert "FAQ-1" not in res_wallet.get("sections_used", [])
    assert "5 to 7" not in res_wallet["reply"]
    assert "instant" in res_wallet["reply"].lower() or "2 hours" in res_wallet["reply"].lower()

    # Electronics return: POL-RET-v4 (7 days) supersedes POL-RET-v3 (10 days)
    res_elec = rag.process_query("Is the return window for a smartwatch delivered yesterday still ten days?")
    assert res_elec["decision"] == "answer"
    assert "7 days" in res_elec["reply"]
    assert "POL-RET-v3" not in res_elec["retrieved_evidence"]


def test_questions_with_no_supporting_evidence(rag):
    """6. Test appropriate uncertainty / refusal when documents do not cover the question."""
    # Cryptocurrency
    res_crypto = rag.process_query("Can I pay for my groceries with Bitcoin or Ethereum?")
    assert res_crypto["decision"] == "answer"
    assert "don't have information" in res_crypto["reply"].lower() or "colleague" in res_crypto["reply"].lower()

    # Midnight delivery
    res_midnight = rag.process_query("Can I schedule a delivery at midnight?")
    assert res_midnight["decision"] == "answer"
    assert "don't have information" in res_midnight["reply"].lower() or "colleague" in res_midnight["reply"].lower()

    # Student discount
    res_student = rag.process_query("Is there an additional student discount for college students?")
    assert res_student["decision"] == "answer"
    assert "don't have information" in res_student["reply"].lower() or "colleague" in res_student["reply"].lower()


def test_answer_supported_by_retrieved_chunks(rag):
    """7. Verify that cited sections are actually present in the retrieved evidence pool."""
    test_queries = [
        "How fast are refunds to the ZentroMart Wallet?",
        "What happens if courier comes and I am not home?",
        "Can a shipped order be cancelled?",
        "Can I return an opened lipstick?"
    ]
    for q in test_queries:
        out = rag.process_query(q)
        for sec in out.get("sections_used", []):
            if sec != "NONE":
                assert sec in out["retrieved_evidence"], f"Cited section {sec} was not in retrieved evidence: {out['retrieved_evidence']}"

