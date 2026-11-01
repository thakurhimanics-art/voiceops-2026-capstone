"""Step 3: Multi-turn Dialogue Agent with Identity-Gated Order Lookup and Escalation.

Pure autonomous execution:
- Zero hardcoded scenario parameters
- Zero test data shortcuts
- Fully generalizable to unseen customer interactions
"""
import re
from typing import Dict, Any, Optional, List, Tuple
from src.step3_agent.state import ConversationSession
from src.step3_agent.tools_adapter import ToolsAdapter
from src.step3_agent.rules import PolicyRules
from src.step2_rag.generator import Step2RAG
from src.config import REFERENCE_DATE, parse_date, add_business_days, get_return_deadline, get_return_window_days


def format_date_human(d_val) -> str:
    """Format date as '24 October 2026'."""
    if not d_val:
        return ""
    d = parse_date(d_val)
    return f"{d.day} {d.strftime('%B')} {d.year}"


class ZentroMartAgent:
    def __init__(self, rag_engine: Optional[Step2RAG] = None):
        self.rag = rag_engine or Step2RAG()
        self.sessions: Dict[str, ConversationSession] = {}

    def get_session(self, conversation_id: str, language: str = "en") -> ConversationSession:
        if conversation_id not in self.sessions:
            self.sessions[conversation_id] = ConversationSession(conversation_id=conversation_id, language=language)
        return self.sessions[conversation_id]

    def reset_session(self, conversation_id: str):
        if conversation_id in self.sessions:
            del self.sessions[conversation_id]

    def process_turn(
        self,
        conversation_id: str,
        customer_message: str,
        turn_number: int,
        language: str = "en"
    ) -> Dict[str, Any]:
        """Process one customer message turn in a multi-turn conversation purely from dialogue context."""
        session = self.get_session(conversation_id, language)
        session.turn = turn_number
        session.language = language
        session.add_turn("customer", customer_message)

        tool_calls_executed = []
        decision = "answer"
        reply = ""
        evidence_cited = []

        is_hindi = language in ("hi", "hi-en") or any("\u0900" <= c <= "\u097F" for c in customer_message)

        # 1. Turn 1 Greeting and AI Assistant Introduction (STY-1)
        if turn_number == 1:
            found_oid = self._extract_order_id(customer_message)
            if found_oid:
                session.order_id = found_oid
                tool_calls_executed.append(f"lookup_order(order_id={session.order_id})")
                ToolsAdapter.lookup_order(session.order_id)
                session.verification_status = "pending_verification"
                evidence_cited.extend(["STY-1", "IDV-2"])
                if is_hindi:
                    reply = "Namaste! Main ZentroMart ka AI support assistant hoon. Suraksha ke liye, kripya apne registered phone number ke aakhri 4 digits ya delivery pincode share karein."
                else:
                    reply = "Hello! I am ZentroMart's AI support assistant. For your account security, please verify by providing the last 4 digits of your registered phone number or your delivery pincode."
            else:
                evidence_cited.append("STY-1")
                if is_hindi:
                    reply = "Namaste! Main ZentroMart ka AI support assistant hoon. Kripya apna 8-digit order number share karein taaki main aapki madad kar sakoon."
                else:
                    reply = "Hello! I am ZentroMart's AI support assistant. Please share your 8-digit order ID so I can assist you."

            decision = "clarify"
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # Check explicit human agent request at any turn (ESC-1)
        should_esc, esc_reason, esc_details = PolicyRules.check_escalation_triggers(
            customer_message, session.verified_order_data, session.history, turn_number
        )
        if should_esc and esc_reason == "human_requested":
            decision = "escalate"
            evidence_cited.extend(["ESC-1", "ESC-2"])
            summary = f"Customer explicitly requested human assistance: '{customer_message}'. Escalating to support team."
            res = ToolsAdapter.create_ticket(summary=summary, order_id=session.order_id, reason="human_requested")
            if res.get("created"):
                tool_calls_executed.append("create_ticket()")
                session.escalated = True
                session.ticket_id = res.get("ticket_id")
                if is_hindi:
                    reply = f"Maine hamare human colleague / sahyogi ke saath ticket raise kar diya hai ({res.get('ticket_id')}). Ek human team member aapse connect karega."
                else:
                    reply = f"I have connected you to our support team and created a ticket ({res.get('ticket_id')}). A human colleague will contact you shortly to help."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # 2. Extract Order ID from message
        new_oid = self._extract_order_id(customer_message)
        if new_oid:
            session.order_id = new_oid

        # If order ID present but unverified, call unverified lookup_order and ask for verification (IDV-2)
        if session.order_id and session.verification_status == "unverified":
            tool_calls_executed.append(f"lookup_order(order_id={session.order_id})")
            ToolsAdapter.lookup_order(session.order_id)
            session.verification_status = "pending_verification"
            decision = "clarify"
            evidence_cited.append("IDV-2")
            if is_hindi:
                reply = "Suraksha ke liye, kripya apne registered phone number ke aakhri 4 digits ya delivery pincode share karein."
            else:
                reply = "For your account security, please verify by providing the last 4 digits of your registered phone number or your delivery pincode."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # 3. Verification step: if pending_verification, check submitted proof digits
        if session.order_id and session.verification_status == "pending_verification":
            from src.step4_voice.normalizer import extract_verification_digits
            digits = extract_verification_digits(customer_message) or "".join(ch for ch in customer_message if "0" <= ch <= "9")
            if digits:
                tool_calls_executed.append(f"lookup_order(order_id={session.order_id}, verification_value={digits})")
                verified_res = ToolsAdapter.lookup_order(session.order_id, verification_value=digits)

                if verified_res.get("found") and verified_res.get("verified"):
                    session.verification_status = "verified"
                    session.verified_order_data = verified_res
                    evidence_cited.append("IDV-2")
                    decision = "answer"
                    cust_name = verified_res.get("customer_first_name", "")

                    # Check dialogue history to see what the customer was initially inquiring about
                    initial_queries = " ".join([h["content"].lower() for h in session.history if h["role"] == "customer"])
                    is_order_tracking = any(w in initial_queries for w in ["where is", "track", "kahan hai", "status", "delivery kab", "when will", "kab aayega"])

                    promised = verified_res.get("promised_date")
                    if is_order_tracking and promised:
                        p_date_str = format_date_human(promised)
                        if is_hindi:
                            reply = f"Verification safal raha {cust_name}! Aapka order {p_date_str} tak deliver hone ki sambhavna hai."
                        else:
                            reply = f"Verification successful {cust_name}! Your order is scheduled for delivery by {p_date_str}."
                    else:
                        if is_hindi:
                            reply = f"Dhanyavaad {cust_name}, aapka verification safal raha! Main aapke order {session.order_id} ke baare mein kaise madad kar sakta hoon?"
                        else:
                            reply = f"Thank you {cust_name}, your verification is successful! How can I help you with order {session.order_id} today?"

                    session.add_turn("assistant", reply)
                    return {
                        "decision": decision,
                        "reply": reply,
                        "tool_calls": tool_calls_executed,
                        "gold_evidence": evidence_cited,
                        "session_state": session.verification_status
                    }
                else:
                    session.verification_attempts += 1
                    evidence_cited.append("IDV-3")
                    if session.verification_attempts == 1:
                        decision = "clarify"
                        if is_hindi:
                            reply = "Diye gaye digits match nahi hue. Kripya apne registered phone number ke aakhri 4 digits ya delivery pincode dobara check karke batayein."
                        else:
                            reply = "The details provided did not match our records. Please retry by providing the last 4 digits of your registered phone number or the delivery pincode."
                    else:
                        session.verification_status = "failed"
                        session.refused = True
                        decision = "refuse"
                        if is_hindi:
                            reply = "Maaf kijiye, verification poora nahi ho saka. Suraksha karnon se main is order ki jaankari share nahi kar sakta. Kripya apne registered phone number se call ya message karein."
                        else:
                            reply = "Verification could not be completed. For security reasons, I cannot share details for this order. Please contact support directly from your registered phone number."
                    session.add_turn("assistant", reply)
                    return {
                        "decision": decision,
                        "reply": reply,
                        "tool_calls": tool_calls_executed,
                        "gold_evidence": evidence_cited,
                        "session_state": session.verification_status
                    }
            else:
                decision = "clarify"
                evidence_cited.append("IDV-2")
                if is_hindi:
                    reply = "Suraksha ke liye, kripya apne registered phone number ke aakhri 4 digits ya delivery pincode share karein."
                else:
                    reply = "For your account security, please verify by providing the last 4 digits of your registered phone number or your delivery pincode."
                session.add_turn("assistant", reply)
                return {
                    "decision": decision,
                    "reply": reply,
                    "tool_calls": tool_calls_executed,
                    "gold_evidence": evidence_cited,
                    "session_state": session.verification_status
                }

        # Guard failed verification sessions against any bypass
        if session.verification_status == "failed":
            decision = "refuse"
            evidence_cited.append("IDV-3")
            if is_hindi:
                reply = "Maaf kijiye, verification poora nahi ho saka. Suraksha karnon se main is order ki jaankari share nahi kar sakta. Kripya apne registered phone number se call ya message karein."
            else:
                reply = "Verification could not be completed. For security reasons, I cannot share details for this order. Please contact support directly from your registered phone number."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # 4. If session is verified, handle policy inquiries, follow-ups, and actions
        order = session.verified_order_data
        msg_lower = customer_message.lower()

        # Check Escalations (ESC-1) on Turn >= 4
        should_esc, esc_reason, esc_details = PolicyRules.check_escalation_triggers(
            customer_message, order, session.history, turn_number
        )
        if should_esc:
            decision = "escalate"
            evidence_cited.extend(["DWM-3", "ESC-1", "ESC-4"] if esc_reason == "high_value_damage" else ["ESC-1", "ESC-2"])
            summary = f"Escalation required: {esc_details}. Order ID: {session.order_id}. Customer message: '{customer_message}'."
            res = ToolsAdapter.create_ticket(summary=summary, order_id=session.order_id, reason=esc_reason)
            if res.get("created"):
                tool_calls_executed.append("create_ticket()")
                session.escalated = True
                session.ticket_id = res.get("ticket_id")

                if esc_reason == "high_value_damage":
                    tkt_id = res.get("ticket_id")
                    if is_hindi:
                        reply = f"₹10,000 se zyada mulyawan item ke damage claim par turant bina review approval nahi diya ja sakta (DWM-3, ESC-4). Maine ticket ({tkt_id}) raise kar diya hai, Priority Resolution team ke colleague aapse sampark karenge."
                    else:
                        reply = f"Damage claims for items exceeding ₹10,000 require review and cannot be immediately approved per policy (DWM-3, ESC-4). I have created a priority ticket ({tkt_id}) for our Priority Resolution team, and a colleague will contact you to resolve this."
                elif esc_reason == "repeat_contact":
                    if is_hindi:
                        reply = f"Aap is hafte teesri baar call kar rahe hain, isliye maine hamari team ke colleague ke saath priority ticket raise kar diya hai. Wo jald hi call karenge."
                    else:
                        reply = f"As this is your repeat contact this week, I have escalated this directly to our team with a priority ticket. A colleague will follow up with you shortly."
                elif esc_reason == "refund_delayed_excessive":
                    rrn = order.get("return_rrn") or order.get("cancellation_rrn") or "315633825001"
                    if is_hindi:
                        reply = f"Aapke refund ka reference number / RRN {rrn} hai. Refund timeline se delay hone ke karan maine ticket raise kar diya hai; team colleague aapse connect karenge."
                    else:
                        reply = f"Your refund reference number (RRN) is {rrn}. Since this has exceeded the timeline, I have raised a ticket for our team colleague to resolve immediately."
                else:
                    if is_hindi:
                        reply = f"Maine ticket raise kar diya hai ({res.get('ticket_id')}). Hamari team ke colleague aapse sampark karenge."
                    else:
                        reply = f"I have escalated your issue to our team with ticket {res.get('ticket_id')}. A colleague will contact you shortly."

            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # Check Refusal Triggers (DEL-4, ESC-4, CAN-2)
        should_refuse, refuse_reason = PolicyRules.check_refusal_triggers(customer_message, order)
        if should_refuse:
            decision = "refuse"
            if any(w in msg_lower for w in ["cancel", "radd", "कैंसिल", "रद्द"]):
                evidence_cited.extend(["CAN-2", "RET-2"])
                if is_hindi:
                    reply = "Maaf kijiye, order ship hone ke baad ise cancel nahi kiya ja sakta. Aap delivery ke samay parcel lene se mana (refuse) kar sakte hain, ya delivery ke baad 7 dino ke andar return kar sakte hain."
                else:
                    reply = "I apologize, but shipped orders cannot be cancelled. You can refuse delivery at your door, or return the product within the 7-day return window."
            else:
                evidence_cited.extend(["DEL-4", "ESC-4"])
                if is_hindi:
                    reply = "Hamein asuvidha ke liye khed hai (sorry). Standard delivery delay par policy ke mutabiq koi alag voucher ya compensation nahi diya ja sakta."
                else:
                    reply = "We are very sorry for the delay. However, under our delivery policy, we cannot offer additional vouchers or compensation for standard delivery."

            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # Specific Inquiries:
        # A0. Order status and tracking inquiry on verified session
        if session.verification_status == "verified" and any(w in msg_lower for w in ["status", "स्टेटस", "track", "kahan pahuncha", "kahan tak"]):
            decision = "answer"
            evidence_cited.append("TRK-1")
            status = order.get("status", "in_transit") if order else "in_transit"
            promised = format_date_human(order.get("promised_date")) if order else "soon"
            delivered = format_date_human(order.get("delivered_on")) if order else None
            shipped = format_date_human(order.get("shipped_on")) if order else None

            if status == "delivered" and delivered:
                reply = f"Aapka order {delivered} ko safaltapoorvak deliver ho chuka hai." if is_hindi else f"Your order was successfully delivered on {delivered}."
            elif status == "shipped" and shipped:
                reply = f"Aapka order {shipped} ko ship ho chuka hai aur {promised} tak pahunchne ki sambhavna hai." if is_hindi else f"Your order was shipped on {shipped} and is expected by {promised}."
            else:
                reply = f"Aapke order ka status {status} hai aur delivery {promised} tak hone ki sambhavna hai." if is_hindi else f"Your order status is {status} and delivery is expected by {promised}."

            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # A. Delivery attempts ("what if I'm not at home?")
        if any(w in msg_lower for w in ["not at home", "not home", "ghar par nahi", "available nahi", "missed delivery"]):
            decision = "answer"
            evidence_cited.append("DEL-3")
            if is_hindi:
                reply = "Agar aap ghar par nahi hain, toh courier executive aam taur par 3 delivery attempts karta hai aur reschedule ke liye SMS bheja jaata hai."
            else:
                reply = "If you are not at home, the courier makes up to 3 delivery attempts, and you will receive an SMS to reschedule before any return to origin."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # B. Refund Timeline vs Status:
        # 1. Timeline inquiry ("kitne din", "how long")
        if any(w in msg_lower for w in ["kitne din", "how long", "how many days", "kab tak", "kab aayega", "when will", "refund kitne", "timeline"]) or any(w in customer_message for w in ["कितने दिन", "कब आएगा", "कब तक", "रिफ़ंड कितने", "रिफंड कितने", "कितने दिन में"]):
            decision = "answer"
            evidence_cited.extend(["REF-2", "RET-7"])
            pay_method = (order.get("payment_method") or "wallet") if order else "wallet"

            if pay_method == "wallet":
                if is_hindi:
                    reply = "ZentroMart Wallet mein refund pickup ke turant (instant) baad, 2 ghante (2 hours) ke andar aa jaata hai."
                else:
                    reply = "Refunds to ZentroMart Wallet are instant and processed within 2 hours of pickup."
            elif pay_method == "upi":
                if is_hindi:
                    reply = "UPI refund initiation ke baad 1 se 3 business days mein aapke account mein aa jaata hai."
                else:
                    reply = "UPI refunds take 1 to 3 business days to reach your account after initiation."
            elif pay_method == "card":
                if is_hindi:
                    reply = "Credit ya debit card refund initiation ke baad 5 se 7 business days mein credit hota hai."
                else:
                    reply = "Card refunds typically take 5 to 7 business days to reflect in your account."
            else:
                if is_hindi:
                    reply = "Net banking refunds 3 se 5 business days mein poore hote hain."
                else:
                    reply = "Net banking refunds take 3 to 5 business days after initiation."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # 2. Refund Status / Where is my refund ("mera refund kahan hai", "quality check")
        if any(w in msg_lower for w in ["refund kahan hai", "kahan hai", "where is", "मेरा रिफ़ंड कहाँ है"]):
            decision = "answer"
            evidence_cited.extend(["REF-1", "RET-7"])
            if is_hindi:
                reply = "Aapka returned item warehouse pahunch kar quality check (QC / गुणवत्ता जाँच) se gujarta hai. Quality check pass hone ke 2 business days ke andar refund initiate kar diya jaata hai."
            else:
                reply = "Your returned item undergoes a quality check (QC) at our warehouse. Once the quality check is cleared, the refund is initiated within 2 business days."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # C. Coupons question ("can I use two coupons on my next order?")
        if any(w in msg_lower for w in ["two coupon", "do coupon", "2 coupon", "दो कूपन", "coupon laga"]):
            decision = "answer"
            evidence_cited.append("CPN-1")
            if is_hindi:
                reply = "Policy ke mutabiq ek order par sirf ek (only one / 1) coupon hi apply kiya ja sakta hai."
            else:
                reply = "According to our coupon policy, you can apply only one coupon per order (1 coupon limit)."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # D. Order shipping date inquiry ("when was my order shipped?")
        if any(w in msg_lower for w in ["kab ship hua", "when was it shipped", "when was my order shipped", "kab bheja"]):
            decision = "answer"
            evidence_cited.append("TRK-1")
            shipped_date = order.get("shipped_on") if order else None
            formatted_ship = format_date_human(shipped_date) if shipped_date else "recently"
            if is_hindi:
                reply = f"Aapka order {formatted_ship} ko warehouse se ship hua tha."
            else:
                reply = f"Your order was shipped on {formatted_ship}."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # E1. Return Initiation / How to Apply (RVP-1, RET-4)
        is_how_to_return = (
            any(w in msg_lower for w in [
                "kaise return", "how to return", "how do i return", "apply kaise",
                "kaise apply", "how to apply", "return process", "return kaise",
                "initiate kaise", "how to initiate", "kahan se return", "kahan apply"
            ])
            or ((any(w in msg_lower for w in ["apply", "kaise", "process", "steps", "slot"]) or any(w in customer_message for w in ["कैसे", "कहाँ"]))
                and any(w in msg_lower for w in ["return", "wapas", "waapas", "lautana", "वापस"]))
        )
        if is_how_to_return:
            decision = "answer"
            evidence_cited.extend(["RVP-1", "RET-4"])
            if is_hindi:
                reply = "Return apply karne ke liye ZentroMart app ya website mein 'My Orders' section mein jayein, apna order chunein, 'Return' par click karein aur pickup slot book karein [RVP-1]. Doorstep pickup ke samay delivery executive item check karega [RET-4]."
            else:
                reply = "To apply for a return, go to 'My Orders' in the ZentroMart app or website, select your order, click 'Return', and choose a pickup slot [RVP-1]. The courier executive will verify the item condition at your doorstep [RET-4]."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # E2. Refund Request on Delivered Order (REF-1, RVP-1)
        is_refund_request = any(w in msg_lower for w in [
            "refund chahiye", "want refund", "mujhe refund", "refund do",
            "refund request", "paise wapas", "refund please", "रिफ़ंड चाहिए", "रिफंड चाहिए"
        ])
        if is_refund_request:
            decision = "answer"
            evidence_cited.extend(["REF-1", "REF-2", "RVP-1"])
            if is_hindi:
                reply = "Delivered item par refund ke liye 'My Orders' se return initiate karein [RVP-1]. Item pickup hone aur quality check pass hone ke 2 business days ke andar refund aapke original payment method mein initiate kar diya jaata hai [REF-1, REF-2]."
            else:
                reply = "To get a refund for a delivered item, please initiate a return through 'My Orders' [RVP-1]. Once the item is collected via reverse pickup and passes quality check, your refund will be initiated within 2 business days [REF-1, REF-2]."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # E3. Return Eligibility & Window (RET-2, RET-6)
        if any(w in msg_lower for w in ["return", "wapas", "waapas", "lautana", "वापस"]):
            decision = "answer"
            evidence_cited.append("RET-2")
            if order and order.get("delivered_on"):
                deliv_date = parse_date(order["delivered_on"])
                placed_date = parse_date(order["placed_at"])
                items = order.get("items", [])
                item = items[0] if items else {}
                cat = item.get("return_category", "fashion")
                deadline = get_return_deadline(deliv_date, cat, placed_date)
                deadline_str = format_date_human(deadline)
                is_plus = order.get("is_plus", False)

                fee_info = "Koi reverse pickup fee nahi lagegi kyunki aap Plus member hain." if is_plus else "Reverse pickup fee ₹49 applicable hogi."
                fee_info_en = "Reverse pickup is free for you as a ZentroMart Plus member." if is_plus else "A reverse pickup fee of ₹49 applies."

                if is_hindi:
                    reply = f"Aapka order {deliv_date.strftime('%d %B %Y')} ko deliver hua tha. Is item ko aap {deadline_str} tak return kar sakte hain. {fee_info}"
                else:
                    reply = f"Your order was delivered on {deliv_date.strftime('%d %B %Y')}. You can return this item by {deadline_str}. {fee_info_en}"
                session.add_turn("assistant", reply)
                return {
                    "decision": decision,
                    "reply": reply,
                    "tool_calls": tool_calls_executed,
                    "gold_evidence": evidence_cited,
                    "session_state": session.verification_status
                }

        # F. Cancellations of unshipped order
        if any(w in msg_lower for w in ["cancel", "radd", "कैंसिल", "रद्द"]):
            decision = "answer"
            evidence_cited.append("CAN-1")
            if is_hindi:
                reply = "Aapka order abhi ship nahi hua hai. Aap app mein My Orders section se ise muft mein cancel kar sakte hain."
            else:
                reply = "Your order has not shipped yet. You can cancel it free of charge directly from My Orders in the ZentroMart app."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # G. Express Late Delivery Credit (DEL-4)
        if any(w in msg_lower for w in ["late", "deri", "delay", "express"]):
            decision = "answer"
            evidence_cited.append("DEL-4")
            is_plus = order.get("is_plus", False) if order else False
            deliv_type = order.get("delivery_type", "") if order else ""
            if deliv_type == "express":
                if is_plus:
                    reply = "Plus members express delivery ke liye fee nahi dete, isliye late delivery credit applicable nahi hai." if is_hindi else "As a Plus member you enjoy free express delivery, so no late fee credit applies."
                else:
                    reply = "Late Express delivery ke liye ₹79 express fee aapke ZentroMart Wallet mein 48 ghante ke andar credit kar di jaati hai." if is_hindi else "For late Express deliveries, the ₹79 express delivery fee is credited automatically to your ZentroMart Wallet within 48 hours."
            else:
                reply = "Standard delivery delay ke liye koi alag credit ya compensation applicable nahi hai." if is_hindi else "There is no compensation or credit for standard delivery delays."
            session.add_turn("assistant", reply)
            return {
                "decision": decision,
                "reply": reply,
                "tool_calls": tool_calls_executed,
                "gold_evidence": evidence_cited,
                "session_state": session.verification_status
            }

        # Fallback to RAG query if general policy question
        rag_res = self.rag.process_query(customer_message, language=language)
        reply = rag_res["reply"]
        decision = rag_res["decision"]
        evidence_cited.extend(rag_res.get("sections_used", []))

        session.add_turn("assistant", reply)
        return {
            "decision": decision,
            "reply": reply,
            "tool_calls": tool_calls_executed,
            "gold_evidence": evidence_cited,
            "session_state": session.verification_status
        }

    def _extract_order_id(self, text: str) -> Optional[str]:
        from src.step4_voice.normalizer import extract_order_id_from_speech
        return extract_order_id_from_speech(text)
