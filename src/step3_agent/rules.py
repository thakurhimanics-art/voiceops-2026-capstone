"""Policy rules and decision guardrails for Step 3 Agent (Zero Hardcoded Scenarios)."""
import re
from typing import Dict, Any, Optional, Tuple, List
from src.config import REFERENCE_DATE, parse_date, business_days_between


class PolicyRules:
    @staticmethod
    def check_escalation_triggers(
        customer_message: str,
        order_data: Optional[Dict[str, Any]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        turn_number: int = 1
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Check if any escalation condition from ESC-1 is triggered.

        Returns (should_escalate, reason, summary_details)
        """
        msg_lower = customer_message.lower()

        # Trigger 6: Customer asks for a human agent (English, Hindi, and Devanagari)
        human_keywords = [
            "human", "agent", "person", "insaan", "colleague", "representative",
            "executive", "support staff", "real person", "aadmi", "insan",
            "baat karni hai", "connect karo", "connect me",
            "इंसान", "व्यक्ति", "बात करनी", "सहयोगी", "प्रतिनिधि"
        ]
        if any(k in msg_lower for k in human_keywords) or any(k in customer_message for k in ["इंसान", "व्यक्ति", "बात"]):
            return True, "human_requested", "Customer explicitly requested to speak with a human agent."

        # Trigger 2: Fraud / unauthorized activity
        fraud_keywords = [
            "didn't make", "did not make", "fraud", "scam", "unauthorized",
            "unauthorised", "not my order", "hacked", "maine nahi kiya",
            "maine order nahi kiya", "dhokha", "धोखा", "मैंने नहीं किया"
        ]
        if any(k in msg_lower for k in fraud_keywords) or any(k in customer_message for k in ["धोखा"]):
            return True, "fraud_unauthorized", "Customer reported unauthorized order or payment activity."

        # Trigger 3: Legal, consumer court, police complaint
        legal_keywords = ["legal", "court", "consumer court", "police", "lawyer", "vakil", "kanooni", "वकील", "कोर्ट", "पुलिस"]
        if any(k in msg_lower for k in legal_keywords):
            return True, "legal_threat", "Customer mentioned legal action or consumer court complaint."

        # Trigger 7: Product safety risk
        safety_keywords = [
            "swelling", "swollen", "burning", "sparks", "spark", "smoke",
            "heat", "blast", "injury", "aag", "dhuan", "jal gaya", "आग", "धुआं"
        ]
        if any(k in msg_lower for k in safety_keywords):
            return True, "product_safety", "Critical safety hazard reported (battery swelling, heat, or fire risk)."

        # Trigger 1: Damaged, defective or wrong item worth > ₹10,000 (DWM-3, ESC-1)
        is_damage_query = any(w in msg_lower for w in ["damage", "broken", "defective", "kharab", "toota", "damaged", "replacement approve", "approve", "खराब", "टूटा"])
        if order_data and is_damage_query:
            items = order_data.get("items", [])
            for it in items:
                price = int(it.get("unit_price_inr", 0))
                if price > 10000:
                    return True, "high_value_damage", f"Damage/replacement claim for high-value item '{it.get('title')}' worth ₹{price} (threshold ₹10,000)."

        # Trigger 4: Repeat contact (contacts_last_7_days >= 2 per ESC-1)
        if order_data and turn_number >= 4:
            contacts = int(order_data.get("contacts_last_7_days") or 0)
            repeat_msg = any(w in msg_lower for w in ["teesri baar", "third time", "already called", "multiple times", "fir se call", "bar bar", "तीसरी बार", "is hafte"])
            if contacts >= 2 and repeat_msg:
                return True, "repeat_contact", f"Customer has contacted support {contacts} times in the last 7 days regarding this order."

        # Trigger 5: Refund more than 3 business days past maximum timeline
        if order_data and turn_number >= 4 and any(w in msg_lower for w in ["refund", "paise", "रिफ़ंड", "रिफंड"]):
            rrn = order_data.get("return_rrn") or order_data.get("cancellation_rrn") or order_data.get("rto_rrn")
            init_str = order_data.get("return_refund_initiated_on") or order_data.get("cancellation_refund_initiated_on")
            if init_str and not order_data.get("return_refund_completed_on"):
                init_date = parse_date(init_str)
                method = order_data.get("return_refund_method") or order_data.get("payment_method") or "card"
                max_days = 7 if method == "card" else (5 if method == "netbanking" else (3 if method == "upi" else 0))
                elapsed_b_days = business_days_between(init_date, REFERENCE_DATE)
                if elapsed_b_days > (max_days + 3):
                    return True, "refund_delayed_excessive", f"Refund RRN {rrn} initiated on {init_date} via {method} is delayed {elapsed_b_days} business days past maximum SLA."

        return False, None, None

    @staticmethod
    def check_refusal_triggers(customer_message: str, order_data: Optional[Dict[str, Any]] = None) -> Tuple[bool, Optional[str]]:
        """Check if an unpermitted customer request must be refused per policy (ESC-4, DEL-4, CAN-2)."""
        msg_lower = customer_message.lower()

        # Cancellation of already shipped order (CAN-2)
        if any(w in msg_lower for w in ["cancel", "radd", "कैंसिल", "रद्द"]):
            if order_data and (order_data.get("status") == "shipped" or order_data.get("shipped_on")):
                return True, "CAN-2: Shipped orders cannot be cancelled directly."

        # Compensation demand for delivery delay (DEL-4)
        if any(w in msg_lower for w in ["voucher", "compensation", "extra refund", "muavza", "harkat", "compensate", "penalty"]):
            return True, "DEL-4/ESC-4: Policy does not permit compensation for standard delivery delays."

        return False, None
