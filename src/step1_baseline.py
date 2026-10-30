"""Step 1: Prompt-Only LLM Baseline (No policy retrieval)."""
from typing import Dict, Any, Optional
from src.llm_client import LLMClient
from src.config import REFERENCE_DATE_STR

STEP1_SYSTEM_PROMPT = f"""You are ZentroMart's AI support assistant. ZentroMart is an Indian e-commerce platform.
Today's date is {REFERENCE_DATE_STR}.
Rules:
1. Always maintain a helpful, polite, and professional tone.
2. In your opening or first reply, acknowledge yourself as ZentroMart's AI support assistant.
3. Keep chat replies concise (2-3 short sentences).
4. Reply in the exact language used by the customer (English, Hindi, or Hinglish).
5. You have NO access to internal policy documents, databases, or live tools in this baseline mode. Answer solely from your general knowledge.
6. If you do not have sufficient information to answer or if the query involves specific account/order actions or unknown policies, state that you do not have this information and offer to connect the customer with a human colleague.

Classify your decision as one of:
- 'answer': If providing an answer or assistance
- 'clarify': If asking the user for required clarification
- 'escalate': If handing over to a human colleague or priority team
- 'refuse': If refusing an unpermitted request
"""


class Step1Baseline:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient()

    def process_query(self, question: str, language: str = "en") -> Dict[str, Any]:
        """Process a single-turn question using prompt-only baseline."""
        user_prompt = f"""Customer query: "{question}"
Language: {language}

Provide your response. First indicate your DECISION on a single line as: DECISION: <answer|clarify|escalate|refuse>
Followed by your REPLY:
REPLY: <your concise 2-3 sentence response>"""

        messages = [
            {"role": "system", "content": STEP1_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        raw_output = self.llm.chat(messages, temperature=0.1)

        decision = "answer"
        reply = raw_output

        lines = raw_output.split("\n")
        reply_lines = []
        found_reply_tag = False

        for line in lines:
            trimmed = line.strip()
            if trimmed.upper().startswith("DECISION:"):
                dec_val = trimmed.split(":", 1)[1].strip().lower()
                for valid_dec in ("answer", "clarify", "escalate", "refuse"):
                    if valid_dec in dec_val:
                        decision = valid_dec
                        break
            elif trimmed.upper().startswith("REPLY:"):
                found_reply_tag = True
                content = trimmed.split(":", 1)[1].strip()
                if content:
                    reply_lines.append(content)
            elif found_reply_tag:
                reply_lines.append(line)

        if reply_lines:
            reply = "\n".join(reply_lines).strip()
        else:
            # Clean decision line if included
            cleaned = []
            for line in lines:
                if not line.strip().upper().startswith("DECISION:"):
                    cleaned.append(line)
            reply = "\n".join(cleaned).strip()

        return {
            "decision": decision,
            "reply": reply,
            "retrieved_evidence": [],
            "raw_output": raw_output
        }
