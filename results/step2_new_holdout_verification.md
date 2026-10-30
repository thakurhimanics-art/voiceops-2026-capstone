# Step 2 RAG — New Untouched Holdout Verification Report

- **Verification Timestamp:** `2026-10-30 23:12:07`
- **Total Untouched Holdout Questions:** `20`
- **Overall Pass Rate:** **`70.0%`** (14 passed, 6 failed)

## Performance by Category

| Category | Test Scope | Pass Count | Pass Rate |
| :--- | :--- | :---: | :---: |
| **Unseen Knowledge Base** | 8 queries on books, COD charges, address change, coupons, safety | 6/8 | 75.0% |
| **Paraphrased Queries** | 4 queries on jackets, net banking, courier attempts, broken glass | 2/4 | 50.0% |
| **Multi-Chunk Reasoning** | 3 queries on holiday arithmetic, luxury damage, Plus pickup | 3/3 | 100.0% |
| **Unsupported / Out-of-Scope** | 3 queries on PayPal USD, AC installation, wax gift wrap | 1/3 | 33.3% |
| **Outdated / Misleading** | 2 queries on opened cosmetics and September electronics rules | 2/2 | 100.0% |

## Question-by-Question Audit

| ID | Category | Question | Expected Grounding | Actual Decision | Status | Reason |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| `NH_UNSEEN_01` | unseen_kb | What is the return window for a hardcover tex... | 10 days from delivery for books and... | `clarify` | **PASS** | Retrieved valid chunk (['RET-2']) and re |
| `NH_UNSEEN_02` | unseen_kb | How much is the Cash on Delivery convenience ... | COD fee of ₹25 applies per order, f... | `answer` | **PASS** | Retrieved valid chunk (['PAY-2']) and re |
| `NH_UNSEEN_03` | unseen_kb | If an item is marked delivered by the courier... | Wait 24 hours, check with building ... | `answer` | FAIL | Retrieval hit: True, Content grounded: F |
| `NH_UNSEEN_04` | unseen_kb | Can I apply two coupon codes on a single fest... | Only 1 coupon can be applied per or... | `answer` | **PASS** | Retrieved valid chunk (['CPN-1']) and re |
| `NH_UNSEEN_05` | unseen_kb | What should I do if my phone is charging slow... | Use original charging brick and cab... | `answer` | FAIL | Retrieval hit: True, Content grounded: F |
| `NH_UNSEEN_06` | unseen_kb | Can I change my delivery address to a new fla... | Address cannot be changed once plac... | `answer` | **PASS** | Retrieved valid chunk (['DEL-6']) and re |
| `NH_UNSEEN_07` | unseen_kb | Can I cancel a 3-month-old ZentroMart Plus me... | Plus membership cannot be cancelled... | `answer` | **PASS** | Retrieved valid chunk (['PLS-3']) and re |
| `NH_UNSEEN_08` | unseen_kb | How does ZentroMart handle safety emergencies... | Immediate safety escalation to huma... | `escalate` | **PASS** | Retrieved valid chunk (['ESC-1']) and re |
| `NH_PARA_01` | paraphrased | Can I send back a winter jacket if the sleeve... | 15 days return window from delivery... | `answer` | FAIL | Retrieval hit: True, Content grounded: F |
| `NH_PARA_02` | paraphrased | How quickly will funds show in my net banking... | 3 to 5 business days for net bankin... | `answer` | **PASS** | Retrieved valid chunk (['REF-2']) and re |
| `NH_PARA_03` | paraphrased | If a courier delivery fails on Friday and Sat... | Courier attempts up to 3 times befo... | `answer` | **PASS** | Retrieved valid chunk (['DEL-3']) and re |
| `NH_PARA_04` | paraphrased | The glass screen protector I ordered arrived ... | Report damaged item within 48 hours... | `answer` | FAIL | Retrieval hit: False, Content grounded:  |
| `NH_MULTI_01` | multi_chunk | I initiated a credit card refund on Friday 16... | 5 to 7 business days, arriving by 2... | `answer` | **PASS** | Retrieved valid chunk (['REF-2']) and re |
| `NH_MULTI_02` | multi_chunk | I bought a luxury ₹15,000 gaming console in t... | Damage on item > ₹10,000 escalates ... | `escalate` | **PASS** | Retrieved valid chunk (['RET-8']) and re |
| `NH_MULTI_03` | multi_chunk | I am a Plus member who returned formal trouse... | No fee deducted; reverse pickup fee... | `answer` | **PASS** | Retrieved valid chunk (['PLS-2', 'RET-6' |
| `NH_UNSUP_01` | unsupported | Can I pay for my electronics order using PayP... | Abstain honestly: state no informat... | `answer` | FAIL | Failed abstention: is_abstaining=False,  |
| `NH_UNSUP_02` | unsupported | Do you provide on-site installation and wall-... | Abstain honestly: state no informat... | `answer` | **PASS** | Honest abstention observed with zero fab |
| `NH_UNSUP_03` | unsupported | Can I request premium gift wrapping with pers... | Abstain honestly: state no informat... | `answer` | FAIL | Failed abstention: is_abstaining=False,  |
| `NH_OUTDATED_01` | outdated_misleading | Under the older POL-RET-v3 policy, can I retu... | Cosmetics cannot be returned if ope... | `answer` | **PASS** | Retrieved valid chunk (['RET-4']) and re |
| `NH_OUTDATED_02` | outdated_misleading | I read online that ZentroMart allows 10 days ... | No, items delivered on or after 1 A... | `answer` | **PASS** | Retrieved valid chunk (['RET-3', 'RET-2' |

## Evaluation Integrity Principles
1. **Segregation:** This 20-question holdout dataset was created independently after retrieval improvements and was never used to tune or bias the retriever or generator.
2. **Transparency:** Every question's exact retrieved evidence, decision, and output snippet is recorded for auditability.
3. **Zero Fabrication:** The original 52-question benchmark results remain completely untouched and separate.