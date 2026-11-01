"""Regression tests for damaged high-value product escalation, return flow, and WAV playback format."""
import wave
from pathlib import Path
from unittest.mock import patch
import pytest

from src.config import PROJECT_ROOT
from src.step3_agent.agent import ZentroMartAgent
from src.step3_agent.tools_adapter import ToolsAdapter
from src.step3_agent.rules import PolicyRules


def test_damaged_high_value_escalation_and_variations():
    """Verify natural-language variations of damaged high-value products escalate properly."""
    variations = [
        "mere Tv ka screen tuta hua h please replacement krdo",
        "My TV screen arrived broken. Please replace it.",
        "Mere TV ka screen toot gaya hai.",
        "The television was damaged when delivered.",
        "Screen cracked nikli, turant replacement approve kar do",
        "TV display defective hai, replace please",
    ]

    for msg in variations:
        agent = ZentroMartAgent()
        cid = f"test_esc_{abs(hash(msg))}"
        # Set up verified session with order 89782837 (contains TV valued ₹31,649)
        agent.process_turn(cid, "Order number 8978 2837", turn_number=2)
        agent.process_turn(cid, "Last four digits 4533", turn_number=3)

        with patch.object(ToolsAdapter, "create_ticket", return_value={"created": True, "ticket_id": "TKT_MOCK_TEST"}):
            res = agent.process_turn(cid, msg, turn_number=4)
            assert res["decision"] == "escalate", f"Failed decision for: {msg}"
            assert "create_ticket()" in res["tool_calls"], f"create_ticket missing for: {msg}"
            assert "DWM-3" in res["gold_evidence"], f"DWM-3 missing for: {msg}"
            assert "ESC-1" in res["gold_evidence"], f"ESC-1 missing for: {msg}"
            assert "TKT_MOCK_TEST" in res["reply"], f"Ticket ID not in reply for: {msg}"


def test_generic_return_policy_does_not_escalate():
    """Verify that generic return policy queries receive return policy response without escalation."""
    generic_queries = [
        "is order ki return window kya hai",
        "kya main is item ko return kar sakta hoon",
        "what is the return deadline for electronics",
    ]

    for msg in generic_queries:
        agent = ZentroMartAgent()
        cid = f"test_gen_{abs(hash(msg))}"
        agent.process_turn(cid, "Order number 8978 2837", turn_number=2)
        agent.process_turn(cid, "Last four digits 4533", turn_number=3)

        res = agent.process_turn(cid, msg, turn_number=4)
        assert res["decision"] == "answer", f"Generic query should not escalate: {msg}"
        assert "create_ticket()" not in res["tool_calls"]
        assert "RET-2" in res["gold_evidence"]


def test_return_application_and_refund_inquiry():
    """Verify that 'apply kaise krun' and 'refund chahiye' provide grounded guidance."""
    agent = ZentroMartAgent()
    cid = "test_ret_inquiry"
    agent.process_turn(cid, "Order number 8978 2837", turn_number=2)
    agent.process_turn(cid, "Last four digits 4533", turn_number=3)

    # 1. How to apply
    r1 = agent.process_turn(cid, "apply kaise krun", turn_number=4)
    assert r1["decision"] == "answer"
    assert "RVP-1" in r1["gold_evidence"]
    assert "My Orders" in r1["reply"]

    # 2. Refund request
    r2 = agent.process_turn(cid, "refund chahiye", turn_number=5)
    assert r2["decision"] == "answer"
    assert "REF-1" in r2["gold_evidence"]
    assert "REF-2" in r2["gold_evidence"]


def test_unverified_session_blocks_private_data_and_escalation():
    """Unverified users must not access private order data or trigger privileged workflows."""
    agent = ZentroMartAgent()
    cid = "test_unverified_block"
    # Provide order ID but do not verify
    agent.process_turn(cid, "Order 89782837", turn_number=2)
    session = agent.get_session(cid)
    assert session.verification_status == "pending_verification"
    assert session.verified_order_data is None

    # Attempt to ask for delivery status without verification
    res = agent.process_turn(cid, "Is order ka status kya hai?", turn_number=3)
    assert res["decision"] == "clarify"
    assert "15 October" not in res["reply"]
    assert "Kabir" not in res["reply"]


def test_wav_playback_file_validity():
    """Verify sample_outputs/live_gnani_tts_playback.wav is a valid standard PCM WAV file."""
    wav_path = PROJECT_ROOT / "sample_outputs" / "live_gnani_tts_playback.wav"
    assert wav_path.exists(), f"Playback WAV does not exist: {wav_path}"
    assert wav_path.stat().st_size > 1000, "WAV file is too small"

    with wave.open(str(wav_path), "rb") as w:
        assert w.getnchannels() == 1, "Expected mono channel"
        assert w.getsampwidth() == 2, "Expected 16-bit PCM (2 bytes per sample)"
        assert w.getframerate() == 48000, "Expected 48 kHz sample rate"
        assert w.getnframes() > 0, "Frames must be positive"
        duration = w.getnframes() / w.getframerate()
        assert 3.0 < duration < 5.0, f"Expected ~3.68s duration, got {duration}"
