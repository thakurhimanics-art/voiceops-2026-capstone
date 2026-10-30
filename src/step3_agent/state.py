"""Conversation Session State tracking for multi-turn support interactions."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class ConversationSession:
    conversation_id: str
    turn: int = 0
    language: str = "en"
    order_id: Optional[str] = None
    customer_id: Optional[str] = None
    verification_status: str = "unverified"  # unverified, pending_verification, verified, failed
    verification_attempts: int = 0
    verified_order_data: Optional[Dict[str, Any]] = None
    history: List[Dict[str, str]] = field(default_factory=list)
    current_issue: Optional[str] = None
    target_sku: Optional[str] = None
    escalated: bool = False
    ticket_id: Optional[str] = None
    refused: bool = False

    def add_turn(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
