"""Adapter for ZentroMart mock tools (lookup_order and create_ticket)."""
import sys
from typing import Dict, Any, Optional
from src.config import TOOLS_DIR, DATASET_ROOT

# Ensure tools directory is in sys.path
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
if str(DATASET_ROOT) not in sys.path:
    sys.path.insert(0, str(DATASET_ROOT))

from tools import lookup_order as _raw_lookup_order, create_ticket as _raw_create_ticket


class ToolsAdapter:
    @staticmethod
    def lookup_order(order_id: str, verification_value: Optional[str] = None) -> Dict[str, Any]:
        """Wrapper for mock lookup_order. Ensures clean string ID and proof."""
        clean_oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9")
        clean_proof = "".join(ch for ch in str(verification_value) if "0" <= ch <= "9") if verification_value else None
        return _raw_lookup_order(clean_oid, verification_value=clean_proof)

    @staticmethod
    def create_ticket(summary: str, order_id: Optional[str] = None, reason: Optional[str] = None, intent: Optional[str] = None) -> Dict[str, Any]:
        """Wrapper for mock create_ticket with guardrails for summary length."""
        clean_summary = summary.strip()
        if len(clean_summary) < 20:
            clean_summary = f"Handover ticket: {clean_summary} for order {order_id or 'N/A'}. Escalation required per support policy."
        clean_oid = "".join(ch for ch in str(order_id) if "0" <= ch <= "9") if order_id else None
        return _raw_create_ticket(summary=clean_summary, order_id=clean_oid, reason=reason, intent=intent)
