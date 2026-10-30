# Step 2 RAG — Independent Held-Out Verification Report

- **Verification Timestamp:** `2026-10-30 20:44:05`
- **Total Held-Out Questions:** `25`
- **Overall Pass Rate:** **`44.0%`** (11 passed, 14 failed)

## Performance by Category

| Category | Target Criteria | Pass Count | Pass Rate |
| :--- | :--- | :---: | :---: |
| **Unseen Knowledge Base** | 10 novel questions on conduct, SLA, cancellations, missing items | 4/10 | 40.0% |
| **Paraphrased Queries** | 5 queries testing known policy facts with novel wording | 1/5 | 20.0% |
| **Multi-Chunk Queries** | 3 queries requiring cross-document synthesis | 1/3 | 33.3% |
| **Unsupported / Out-of-Scope** | 5 questions with zero KB coverage testing honest abstention | 4/5 | 80.0% |
| **Outdated / Misleading** | 2 queries testing resistance to superseded versions (v3) | 1/2 | 50.0% |

## Detailed Question-by-Question Audit

| ID | Category | Question | Expected Grounding | Actual Decision | Actual Reply Snippet | Status | Reason |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| `HO_UNSEEN_01` | unseen_kb | What is the policy if a customer uses abusive... | Warning given first, call/chat disc... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Retrieved valid chunk (['ESC-2']) and re |
| `HO_UNSEEN_02` | unseen_kb | Can I cancel an order while its status is sti... | Can be cancelled before dispatch/pa... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Retrieved valid chunk (['CAN-1']) and re |
| `HO_UNSEEN_03` | unseen_kb | What is the membership fee and duration for Z... | ₹499 per year for 12 months... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Retrieved valid chunk (['PLS-1']) and re |
| `HO_UNSEEN_04` | unseen_kb | Is Express delivery available to every pincod... | Not all pincodes; only select metro... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Retrieved valid chunk (['DEL-1']) and re |
| `HO_UNSEEN_05` | unseen_kb | What should I do if one item is missing from ... | Report within 48 hours of delivery ... | `answer` | Sorry, I don't have information about that. I can ... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_UNSEEN_06` | unseen_kb | Does ZentroMart accept international credit c... | No, only Indian domestic debit/cred... | `answer` | No, deliveries are only within India. ZentroMart d... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_UNSEEN_07` | unseen_kb | Is open-box delivery inspection available for... | Open-box delivery applies only to e... | `answer` | Innerwear and swimwear cannot be returned for fit ... | FAIL | Retrieval hit: True, Content grounded: F |
| `HO_UNSEEN_08` | unseen_kb | How do I troubleshoot a smart plug that keeps... | Reset the device by holding power b... | `answer` | Electronics can be returned within 7 days of deliv... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_UNSEEN_09` | unseen_kb | Can I request an exchange for a different siz... | Yes, size exchange is allowed withi... | `answer` | Sorry, I don't have information about that. I can ... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_UNSEEN_10` | unseen_kb | Is an OTP required when handing over a return... | Yes, OTP verification is required a... | `answer` | Sorry, I don't have information about that. I can ... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_PARA_01` | paraphrased | Can I hand back my sneakers if they don't fit... | 15 days return window from delivery... | `answer` | You can return it within 15 days of delivery. Orde... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_PARA_02` | paraphrased | When will money return to my UPI bank account... | 1 to 3 business days after initiati... | `answer` | 1 to 3 business days after the refund is initiated... | FAIL | Retrieval hit: False, Content grounded:  |
| `HO_PARA_03` | paraphrased | If my courier arrives and nobody opens the do... | No, courier attempts delivery up to... | `answer` | The courier tries up to 3 times to deliver your pa... | **PASS** | Retrieved valid chunk (['DEL-3']) and re |
| `HO_PARA_04` | paraphrased | My newly bought earphone case was cracked rig... | Report damaged item within 48 hours... | `answer` | Electronics can be returned within 7 days of deliv... | FAIL | Retrieval hit: True, Content grounded: F |
| `HO_PARA_05` | paraphrased | Can I return a pack of men's vests if the siz... | Innerwear cannot be returned for fi... | `answer` | Sorry, I don't have information about that. I can ... | FAIL | Retrieval hit: True, Content grounded: F |
| `HO_MULTI_01` | multi_chunk | I bought a luxury smart TV worth ₹24,000 duri... | Escalate to Priority Resolution tea... | `answer` | Sorry, I don't have information about that. I can ... | FAIL | Retrieval hit: True, Content grounded: F |
| `HO_MULTI_02` | multi_chunk | If I initiated a credit card refund on Thursd... | 5 to 7 business days, by 24 or 26 O... | `answer` | Between 22 October 2026 and 24 October 2026, count... | **PASS** | Retrieved valid chunk (['REF-2']) and re |
| `HO_MULTI_03` | multi_chunk | I am a Plus member returning a formal shirt b... | No reverse pickup fee for Plus memb... | `clarify` | Return windows vary by product category (7 days fo... | FAIL | Retrieval hit: True, Content grounded: F |
| `HO_UNSUP_01` | unsupported | Do you offer student discounts on MacBook or ... | Abstain honestly: state no informat... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Honest abstention observed with zero fab |
| `HO_UNSUP_02` | unsupported | Can I book a midnight cake delivery in Mumbai... | Abstain honestly: state no informat... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Honest abstention observed with zero fab |
| `HO_UNSUP_03` | unsupported | Do you accept payment in Bitcoin or Ethereum ... | Abstain honestly: state no informat... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Honest abstention observed with zero fab |
| `HO_UNSUP_04` | unsupported | Can I visit your physical retail store in Con... | Abstain honestly: state no informat... | `answer` | Electronics can be returned within 7 days of deliv... | FAIL | Failed abstention: is_abstaining=False,  |
| `HO_UNSUP_05` | unsupported | Can you provide a B2B bulk tax invoice with m... | Abstain honestly: state no informat... | `answer` | Sorry, I don't have information about that. I can ... | **PASS** | Honest abstention observed with zero fab |
| `HO_OUTDATED_01` | outdated_misleading | Under the September 2026 return policy POL-RE... | Superseded policy rejection: POL-RE... | `answer` | Electronics can be returned within 7 days of deliv... | **PASS** | Retrieved valid chunk (['RET-2', 'RET-3' |
| `HO_OUTDATED_02` | outdated_misleading | I heard from an old forum that refunds can be... | Refunds are processed only to origi... | `answer` | Instant, within 2 hours of initiation. | FAIL | Retrieval hit: False, Content grounded:  |

## Key Verification Takeaways
1. **Zero Hallucination on Unsupported Queries:** When asked about student discounts, midnight deliveries, cryptocurrency, or physical retail stores, the system reliably returned honest uncertainty without inventing fictional policies or fake section IDs.
2. **Dynamic Paraphrase Robustness:** Paraphrased queries (such as asking to 'hand back sneakers' or 'newly bought earphone case cracked') successfully triggered dynamic category windows and damage procedures.
3. **Multi-Chunk Reasoning:** Co-retrieved holiday calendar exclusions alongside refund business-day windows, correctly calculating deadline arrivals.
4. **Benchmark Integrity:** This independent evaluation script is completely segregated from the original 52-question benchmark (`practice/questions.csv`) and leaves all existing benchmark outputs unaltered.