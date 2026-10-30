"""Unit tests for tools adapter, ticket creation, and summary requirements."""
from src.step3_agent.tools_adapter import ToolsAdapter


def test_create_ticket_short_summary_handled():
    # ToolsAdapter automatically pads summaries < 20 chars so critical escalations never fail silently
    res = ToolsAdapter.create_ticket("short", order_id="89782837", reason="test")
    assert res.get("created") is True
    assert res.get("ticket_id", "").startswith("TKT")


def test_create_ticket_full_summary():
    summary = "High-value damage reported on Smart TV exceeding ₹10,000 threshold. Escalating to Priority team."
    res = ToolsAdapter.create_ticket(summary, order_id="89782837", reason="high_value_damage", intent="damage")
    assert res.get("created") is True
    assert "ticket_id" in res
