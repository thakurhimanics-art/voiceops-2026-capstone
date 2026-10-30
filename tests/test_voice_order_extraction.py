"""Focused offline regression tests for Hindi-English spoken order ID normalization, spoken verification digits, and anti-bypass guardrails."""
import pytest
from src.step4_voice.normalizer import extract_order_id_from_speech, extract_verification_digits
from src.step3_agent.agent import ZentroMartAgent
from src.step3_agent.tools_adapter import ToolsAdapter


def test_extract_order_id_from_actual_fixture():
    # 1. Actual transcript fixture from Gnani STT request req_267bf9eb2815
    fixture_transcript = "मेरे ऑर्डर एट नाइन सेवन एट टू एट थ्री सेवन का स्टेटस क्या है"
    extracted = extract_order_id_from_speech(fixture_transcript)
    assert extracted == "89782837", f"Expected '89782837', got '{extracted}'"


def test_extract_order_id_eight_digit_numeric():
    # 2. Eight-digit numeric order ID formats
    assert extract_order_id_from_speech("Order 89782837 status") == "89782837"
    assert extract_order_id_from_speech("Order number hai 8978 2837.") == "89782837"
    assert extract_order_id_from_speech("Checking order 15911102 details") == "15911102"


def test_extract_order_id_mixed_numeric_spoken():
    # 3. Mixed numeric/spoken-digit order ID
    assert extract_order_id_from_speech("Order 8978 टू एट थ्री सेवन") == "89782837"
    assert extract_order_id_from_speech("Order 8978 two eight three seven") == "89782837"
    assert extract_order_id_from_speech("Order eight nine seven eight 2837") == "89782837"


def test_extract_order_id_ordinary_questions_with_numbers():
    # 4. Ordinary questions containing numbers (e.g. 7-day or 15-day return policy)
    assert extract_order_id_from_speech("क्या 7 दिन में रिटर्न हो जाएगा?") is None
    assert extract_order_id_from_speech("Is return window 7 days or 15 days?") is None
    assert extract_order_id_from_speech("What is the ₹49 delivery fee?") is None


def test_extract_order_id_sequence_exceeding_eight_digits_not_truncated():
    # 5. A sequence containing more than eight consecutive spoken digits must NOT silently truncate
    # 10 spoken digits
    assert extract_order_id_from_speech("one two three four five six seven eight nine ten") is None
    # 9 spoken digits
    assert extract_order_id_from_speech("nine eight seven six five four three two one") is None
    # 10-digit phone number in Devanagari
    assert extract_order_id_from_speech("नाइन एट सेवन सिक्स फाइव फोर थ्री टू वन ज़ीरो") is None
    # 10-digit phone number in ASCII digits
    assert extract_order_id_from_speech("Phone 9876543210 is my number") is None
    # Spaced numeric sequences exceeding eight digits must not be truncated
    assert extract_order_id_from_speech("Order 1234 5678 90") is None
    assert extract_order_id_from_speech("Order 12345678 9") is None
    assert extract_order_id_from_speech("Order 1234 5678 9999") is None
    assert extract_order_id_from_speech("Tracking 123456789") is None


def test_extract_order_id_hindi_question_with_word_ek():
    # 6. Ordinary Hindi question containing the word 'एक' that is not an order number
    assert extract_order_id_from_speech("मुझे एक सवाल पूछना है") is None
    assert extract_order_id_from_speech("एक बार बताओ रिफंड कब आएगा") is None
    assert extract_order_id_from_speech("एक छोटा सा डाउट है") is None


def test_spoken_verification_digits_consistency():
    # Test consistent handling of spoken verification digits and pincodes
    # Hindi-English transliterations
    assert extract_verification_digits("फोर फाइव थ्री थ्री") == "4533"
    assert extract_verification_digits("लास्ट फोर डिजिट्स फोर फाइव थ्री थ्री") == "4533"

    # English spoken words
    assert extract_verification_digits("four five three three") == "4533"
    assert extract_verification_digits("last four digits are four five three three") == "4533"

    # Standard ASCII digits
    assert extract_verification_digits("4533") == "4533"
    assert extract_verification_digits("Last four digits 4533 hain.") == "4533"
    assert extract_verification_digits("The last four digits are 6073.") == "6073"

    # Delivery pincodes (6 digits)
    assert extract_verification_digits("440010") == "440010"
    assert extract_verification_digits("Pincode 440010 hai.") == "440010"
    assert extract_verification_digits("four four zero zero one zero") == "440010"
    assert extract_verification_digits("चार चार शून्य शून्य एक शून्य") == "440010"


def test_complete_extraction_to_tool_path_with_spoken_verification():
    """Verify complete extraction-to-tool execution path using spoken order ID and spoken verification digits."""
    agent = ZentroMartAgent()
    cid = "test_fixture_spoken_path"
    agent.reset_session(cid)

    # 1. Turn 1: Caller sends the exact Gnani STT transcript fixture
    turn1_msg = "मेरे ऑर्डर एट नाइन सेवन एट टू एट थ्री सेवन का स्टेटस क्या है"
    t1 = agent.process_turn(cid, turn1_msg, turn_number=1, language="hi")

    assert t1["decision"] == "clarify"
    assert "lookup_order(order_id=89782837)" in t1["tool_calls"]
    session = agent.get_session(cid)
    assert session.order_id == "89782837"
    assert session.verification_status == "pending_verification"

    # 2. Turn 2: Caller provides verification proof via spoken words
    turn2_msg = "लास्ट फोर डिजिट्स फोर फाइव थ्री थ्री"
    t2 = agent.process_turn(cid, turn2_msg, turn_number=2, language="hi")

    assert t2["decision"] == "answer"
    assert "lookup_order(order_id=89782837, verification_value=4533)" in t2["tool_calls"]
    assert session.verification_status == "verified"
    assert "Kabir" in t2["reply"]
    assert "89782837" in t2["reply"]

    # 3. Turn 3: Caller asks for order status
    turn3_msg = "Status kya hai?"
    t3 = agent.process_turn(cid, turn3_msg, turn_number=3, language="hi")
    assert t3["decision"] == "answer"
    assert any(w in t3["reply"].lower() for w in ["order", "shipped", "deliver"])


def test_failed_or_ambiguous_extraction_does_not_bypass_verification():
    """Verify that ambiguous input or verification failure strictly withholds private order data."""
    agent = ZentroMartAgent()

    # Case A: Ambiguous query with no order ID does not trigger lookup or unlock details
    cid_a = "test_ambig_query"
    agent.reset_session(cid_a)
    t_a = agent.process_turn(cid_a, "नमस्ते मुझे अपने पैकेज की जानकारी चाहिए", turn_number=1, language="hi")
    assert t_a["decision"] == "clarify"
    assert len(t_a["tool_calls"]) == 0
    assert agent.get_session(cid_a).order_id is None

    # Case B: Known order ID, but caller submits wrong verification digits twice
    cid_b = "test_verify_refuse"
    agent.reset_session(cid_b)
    # Turn 1: order identified
    agent.process_turn(cid_b, "Order 89782837", turn_number=1, language="hi")
    assert agent.get_session(cid_b).verification_status == "pending_verification"

    # Turn 2: Wrong digits (Attempt 1) -> clarify, order details not disclosed
    t_b2 = agent.process_turn(cid_b, "लास्ट फोर डिजिट्स 9999", turn_number=2, language="hi")
    assert t_b2["decision"] == "clarify"
    assert agent.get_session(cid_b).verification_status == "pending_verification"
    assert "Kabir" not in t_b2["reply"]
    assert "Smart TV" not in t_b2["reply"]

    # Turn 3: Wrong digits again (Attempt 2) -> REFUSE, order details permanently withheld
    t_b3 = agent.process_turn(cid_b, "लास्ट फोर डिजिट्स 8888", turn_number=3, language="hi")
    assert t_b3["decision"] == "refuse"
    assert agent.get_session(cid_b).verification_status == "failed"
    assert "Kabir" not in t_b3["reply"]
    assert "Smart TV" not in t_b3["reply"]

    # Case C: During pending_verification, sending message without digits strictly insists on verification
    cid_c = "test_no_digits"
    agent.reset_session(cid_c)
    agent.process_turn(cid_c, "Order 89782837", turn_number=1, language="en")
    t_c2 = agent.process_turn(cid_c, "I don't remember my pincode, please tell me the status", turn_number=2, language="en")
    assert t_c2["decision"] == "clarify"
    assert "IDV-2" in t_c2["gold_evidence"]
    assert agent.get_session(cid_c).verification_status == "pending_verification"
    assert "Kabir" not in t_c2["reply"]
    assert "Smart TV" not in t_c2["reply"]

    # Case D: Once verification has failed, subsequent queries are permanently refused
    t_b4 = agent.process_turn(cid_b, "Please just tell me if it was shipped", turn_number=4, language="hi")
    assert t_b4["decision"] == "refuse"
    assert len(t_b4["tool_calls"]) == 0
    assert "Kabir" not in t_b4["reply"]

    # Case E: >8 digit sequence in Turn 1 does not extract a fake order ID or trigger lookup
    cid_e = "test_overlength_digits"
    agent.reset_session(cid_e)
    t_e = agent.process_turn(cid_e, "My number is 9876543210 where is my item", turn_number=1, language="en")
    assert agent.get_session(cid_e).order_id is None
    assert len(t_e["tool_calls"]) == 0
    assert t_e["decision"] == "clarify"


def test_spoken_verification_digits_in_identity_verification_flow():
    """Verify that 'फोर फाइव थ्री थ्री', 'four five three three', and '4533' are handled consistently in identity flow."""
    test_inputs = [
        ("फोर फाइव थ्री थ्री", "hi"),
        ("four five three three", "en"),
        ("4533", "en"),
        ("लास्ट फोर डिजिट्स फोर फाइव थ्री थ्री", "hi"),
        ("last four digits are four five three three", "en"),
    ]

    for proof_input, lang in test_inputs:
        agent = ZentroMartAgent()
        cid = f"test_flow_{proof_input.replace(' ', '_')}"
        agent.reset_session(cid)

        # Turn 1: Caller provides order ID
        t1 = agent.process_turn(cid, "Order 89782837", turn_number=1, language=lang)
        assert t1["decision"] == "clarify"
        assert agent.get_session(cid).verification_status == "pending_verification"

        # Turn 2: Caller provides proof digits
        t2 = agent.process_turn(cid, proof_input, turn_number=2, language=lang)
        assert t2["decision"] == "answer", f"Failed decision for {proof_input}"
        assert "lookup_order(order_id=89782837, verification_value=4533)" in t2["tool_calls"], f"Failed tool call for {proof_input}"
        session = agent.get_session(cid)
        assert session.verification_status == "verified", f"Failed verification status for {proof_input}"
        assert "Kabir" in t2["reply"], f"Customer name not found in reply for {proof_input}"

        # Turn 3: Inquiry on verified order is successfully answered
        t3 = agent.process_turn(cid, "Status kya hai?" if lang == "hi" else "What is the status?", turn_number=3, language=lang)
        assert t3["decision"] == "answer"
        assert any(w in t3["reply"].lower() for w in ["delivered", "deliver", "15 october 2026", "15 अक्टूबर 2026"])

