"""Unit tests for identity verification, data leakage prevention, and retry limits."""
from src.step3_agent.tools_adapter import ToolsAdapter
from src.step3_agent.agent import ZentroMartAgent


def test_unverified_lookup_does_not_leak_details():
    order_id = "89782837"
    res = ToolsAdapter.lookup_order(order_id)
    assert res.get("verification_required") is True
    assert "items" not in res
    assert "status" not in res
    assert "total_inr" not in res
    assert "phone" not in res
    assert "customer_id" not in res


def test_invalid_verification_rejected():
    order_id = "89782837"
    res = ToolsAdapter.lookup_order(order_id, verification_value="0000")
    assert res.get("verified") is False
    assert res.get("verification_required") is True
    assert "items" not in res


def test_valid_phone_suffix_verification():
    # Order 89782837, customer phone suffix is 4533
    order_id = "89782837"
    res = ToolsAdapter.lookup_order(order_id, verification_value="4533")
    assert res.get("found") is True
    assert res.get("verified") is True
    assert "items" in res
    assert "status" in res
    assert "total_inr" in res
    # Should not disclose the full phone number or phone_last4
    assert "phone_last4" not in res


def test_valid_pincode_verification():
    # Order 15911102 has delivery pincode 440010
    order_id = "15911102"
    res = ToolsAdapter.lookup_order(order_id, verification_value="440010")
    assert res.get("found") is True
    assert res.get("verified") is True
    assert "items" in res


def test_agent_retry_and_refusal_on_failed_verification():
    agent = ZentroMartAgent()
    cid = "test_verify_fail"
    agent.reset_session(cid)

    # Turn 1: Greeting
    t1 = agent.process_turn(cid, "Hello", turn_number=1)
    assert t1["decision"] == "clarify"

    # Turn 2: Provide order ID
    t2 = agent.process_turn(cid, "Order 89782837", turn_number=2)
    assert t2["decision"] == "clarify"
    assert "lookup_order(order_id=89782837)" in t2["tool_calls"]

    # Turn 3: Wrong digits (Attempt 1) -> asks to retry (clarify)
    t3 = agent.process_turn(cid, "Digits 9999", turn_number=3)
    assert t3["decision"] == "clarify"

    # Turn 4: Wrong digits again (Attempt 2) -> max retry exceeded -> refuse!
    t4 = agent.process_turn(cid, "Digits 8888", turn_number=4)
    assert t4["decision"] == "refuse"
