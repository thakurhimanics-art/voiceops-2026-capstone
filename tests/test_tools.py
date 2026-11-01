"""Unit tests for tools adapter, ticket creation, and summary requirements."""
from unittest.mock import patch
from src.step3_agent.tools_adapter import ToolsAdapter


def test_create_ticket_short_summary_handled():
    # ToolsAdapter automatically pads summaries < 20 chars so critical escalations never fail silently
    with patch("src.step3_agent.tools_adapter._raw_create_ticket", return_value={"created": True, "ticket_id": "TKT12345"}) as mock_create:
        res = ToolsAdapter.create_ticket("short", order_id="89782837", reason="test")
        assert res.get("created") is True
        assert res.get("ticket_id", "").startswith("TKT")
        mock_create.assert_called_once()
        called_summary = mock_create.call_args[1]["summary"]
        assert len(called_summary) >= 20


def test_create_ticket_full_summary():
    summary = "High-value damage reported on Smart TV exceeding ₹10,000 threshold. Escalating to Priority team."
    with patch("src.step3_agent.tools_adapter._raw_create_ticket", return_value={"created": True, "ticket_id": "TKT67890"}) as mock_create:
        res = ToolsAdapter.create_ticket(summary, order_id="89782837", reason="high_value_damage", intent="damage")
        assert res.get("created") is True
        assert "ticket_id" in res
        mock_create.assert_called_once()
