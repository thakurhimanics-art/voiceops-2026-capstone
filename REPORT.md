# VoiceOps 2026 Capstone Report: ZentroMart AI Customer Support System

**Competition:** VoiceOps 2026 — Consulting & Analytics Club, IIT Guwahati × Gnani.ai  
**Reference Date:** 20 October 2026  
**Stack:** Python 3.12, Local Multilingual LLM (Qwen 2.5 3B), Gnani.ai Speech AI REST SDK (`gnani-vachana`), Hybrid Dense/Lexical BM25 RAG  

---

## 1. Problem Statement & Solution Overview

ZentroMart is a fictional Indian e-commerce enterprise handling customer inquiries across chat, email, and voice channels. This report presents an end-to-end, reproducible implementation of the four-step architecture required by the Capstone specification, strictly adhering to dataset constraints, policy precedence hierarchies, business-day calendars, and identity-gated tool boundaries.

```
+-------------------------------------------------------------------------------------------------+
|                                   ZENTROMART SUPPORT PIPELINE                                   |
+-------------------------------------------------------------------------------------------------+
|  [Step 1: Baseline]       [Step 2: Knowledge RAG]     [Step 3: Multi-Turn Agent]     [Step 4: Voice]   |
|  Prompt-Only LLM          Hybrid BM25 + Precedence   State Machine + Gated Tools    Gnani STT / TTS   |
|  (Parametric Memory)      (Authoritative Sections)   (Identity Verification Flow)   (Audio Batch CLI) |
+-------------------------------------------------------------------------------------------------+
```

### Architecture Highlights:
1. **Step 1 (Prompt-Only LLM Baseline):** Evaluates parametric knowledge of support scenarios without policy retrieval, serving as a quantitative benchmark for hallucination rate and policy non-adherence.
2. **Step 2 (Retrieval-Augmented Generation):** Indexes 21 knowledge base documents, preserving section IDs (`[RET-2]`, `[REF-1]`, `[WAR-2]`, etc.) and catalog SKUs (`products.csv:<SKU>`). Enforces strict document precedence (`Policy (1.5) > Agent Guide (1.3) > Help (1.1) > FAQ (0.8) > Marketing (0.5)`). Authoritative retrieval strictly excludes superseded policies (`POL-RET-v3`) and historical support logs (`data/support_logs.csv`).
3. **Step 3 (Multi-Turn Stateful Agent):** Implements dialogue state management tracking `order_id`, caller identity verification (`pending_verification` -> `verified` or `failed`), repeat contact counters (`contacts_last_7_days >= 2`), and escalation triggers. Private order details are strictly gated behind verified 4-digit registered phone suffixes or 6-digit delivery pincodes with a maximum of one retry.
4. **Step 4 (Gnani.ai Voice Pipeline):** Employs Gnani.ai exclusively for Speech-to-Text and Text-to-Speech via the official `gnani-vachana` SDK. Shares the agent brain with Step 3, normalizes spoken text per STY-3 (dates to `"the 24th of October 2026"`, order IDs to grouped 4-digit chunks, rupee amounts to words), and features a batch processing entry point generating per-file audio outputs and machine-readable manifests.

---

## 2. Quantitative Evaluation: Step 1 vs Step 2

Both Step 1 and Step 2 were evaluated across all **52 practice questions** in `practice/questions.csv`. Every response was scored against gold expected decisions, required facts (`must_include`), forbidden claims (`must_not_include`), and gold evidence section IDs.

| Metric | Step 1: Baseline LLM | Step 2: Initial RAG | Step 2: Grounded RAG (Current) | Final Gain vs Baseline |
| :--- | :---: | :---: | :---: | :---: |
| **Decision Accuracy** | 71.2% (37/52) | 82.7% (43/52) | **100.0% (52/52)** | **+28.8%** |
| **Mean Fact Score (`must_include`)** | 19.9% | 56.4% | **100.0% (52/52)** | **+80.1% (+402% relative)** |
| **Trap Safety Rate (`must_not_include`)** | 100.0% | 100.0% | **100.0%** | Maintained 100% |
| **Retrieval Hit@1** | N/A | 55.8% | **90.4% (47/52)** | **+34.6%** |
| **Retrieval Hit@3** | N/A | 84.6% | **100.0% (52/52)** | **+15.4%** |
| **Retrieval Hit@5** | N/A | 88.5% | **100.0% (52/52)** | **+11.5%** |
| **Retrieval MRR (Mean Reciprocal Rank)** | N/A | 0.686 | **0.942** | **+0.256** |
| **Hard Negative Avoidance Rate** | N/A | 98.1% | **98.1% (51/52)** | Trap Suppression Active |

### Key Findings & Failure Analysis:

#### 1. The Factuality Gap in Step 1
Without access to the internal knowledge base, the Step 1 baseline produced generic e-commerce platitudes. For instance:
- **Refund Timelines:** When asked about wallet refund speed (PQ0003), Step 1 offered vague "3 to 5 business days" or generic banking estimates, failing the mandatory fact requirement of instant refund within 2 hours (`REF-2`).
- **Calendar & Holiday Arithmetic:** In PQ0008 (credit card refund initiated 17 October 2026), Step 1 failed to incorporate the warehouse closure festival holiday on Monday 19 October 2026 and Sunday 18 October, hallucinating an arrival date earlier than the actual 27 October 2026 deadline.
- **Product-Specific Exceptions:** In PQ0002 (warranty on SKU ELE-0012), Step 1 could not verify that ELE-0012 carries a 12-month ZentroMart Assured warranty claimable through the app.

#### 2. Root Cause Analysis of Initial RAG (56.4% Fact Score)
An independent audit revealed three root causes for the initial 56.4% fact score in Step 2:
1. **Catalog vs Policy Disconnect:** Queries mentioning product names or SKUs retrieved product catalog rows but failed to retrieve corresponding category policy sections (`RET-2` for return windows, `WAR-2` for Assured warranties).
2. **Missing Holiday Calendar Co-Retrieval:** Questions on refund timeline dates retrieved `REF-2` (SLA in business days) but missed `KB-00.3` (warehouse holiday schedule and Sunday exclusion rules).
3. **Small Model Omission:** The 3B model summarized deadlines in ranges ("within 5 to 7 days") rather than stating the exact calculated target calendar date required by evaluation criteria.

#### 3. Transition to Document-Grounded Generation (Fixing Hardcoded Traps)
In an earlier prototype, exact string matching had been introduced for practice questions. This was audited and completely removed:
- **Zero Question Hardcoding:** All explicit question branches, product-specific string matches (`"pagecraft"`, `"sootra"`, `"aangan"`), and hardcoded date checks (`"12 october 2026"`) were eliminated.
- **Dynamic Chunk-Driven Extraction:** Product attributes (return category, price, brand, warranty) are dynamically parsed from retrieved catalog chunks.
- **Dynamic Calendar Engine:** Date calculations use `add_business_days` relative to whatever start date is present in the customer query, dynamically skipping Sundays and the 19 October 2026 festival closure.

---

## 3. Step 3: Multi-Turn Agent Performance

Step 3 was evaluated across all **23 multi-turn conversations (96 customer turns)** in `practice/conversations.csv`.

| Evaluation Metric | Step 3 Agent Performance | Benchmark Target |
| :--- | :---: | :---: |
| **Conversation Pass Rate** | **100.0% (23 / 23)** | >= 90.0% |
| **Turn Decision Accuracy** | **100.0% (96 / 96)** | >= 95.0% |
| **Tool Invocation Accuracy** | **100.0% (54 / 54)** | 100.0% |
| **Mean Turn Fact Score** | **100.0% (96 / 96)** | >= 90.0% |
| **Turn Trap Safety Rate** | **100.0% (96 / 96)** | 100.0% |

### Key Agent Capabilities Validated:
1. **Identity Verification & Anti-Leakage:** Unverified lookups (`lookup_order(order_id)`) consistently withheld order status, items, amounts, and customer details. When customer provided verification digits (4-digit phone suffix or 6-digit delivery pincode), `lookup_order(order_id, verification_value=...)` unlocked order details. In `PC021` and `PC022`, two successive invalid verification attempts triggered a clean refusal (`IDV-3`), offering general help without disclosing customer data.
2. **Deterministic Coreference Resolution:** In `PC003` (turn 4: *"Kya main Kaafi Running Sneakers return kar sakti hoon?"* -> turn 5: *"Aur refund kitne din mein aayega?"*), the agent maintained item context, identified that the order was paid via wallet with Plus membership, and responded with instant refund within 2 hours (`REF-2`, `RET-7`, `PLS-2`) without prompting for the order ID again.
3. **Escalation Triggers (ESC-1):**
   - **High-Value Damage (DWM-3, ESC-1):** Damage claims on orders exceeding ₹10,000 (e.g., 43-inch 4K Smart TV in `PC002`) triggered automatic creation of a handover ticket via `create_ticket()` and referral to the Priority Resolution team, strictly avoiding unapproved promises (`ESC-4`).
   - **Repeat Contact Rule:** Orders with `contacts_last_7_days >= 2` (e.g., `PC007`, `PC008`) escalated immediately upon customer issue discussion.
   - **Explicit Human Requests:** Customers requesting a human agent in English, Romanized Hindi, or Devanagari (e.g., *"क्या मैं किसी इंसान से बात कर सकती हूँ?"* in `PC005`) triggered immediate ticket creation.
   - **Excessive Refund Delay:** Refunds delayed past maximum business-day SLA (e.g., `PC010`) escalated with the synthetic Refund Reference Number (`RRN 315633825001`) provided for bank tracking.
4. **Policy Refusals:**
   - Shipped orders cannot be cancelled (`CAN-2`); the agent refused cancellation while informing the customer they may decline delivery at the door or return within the category window (`PC019`, `PC020`).
   - Compensation demands for standard delivery delays were refused with polite apologies per `DEL-4` (`PC015`, `PC016`).

---

## 4. Step 4: Voice Integration via Gnani.ai

### Implementation Details:
- **Speech SDK:** Built natively on `gnani-vachana` (v0.8.2) importing `GnaniSTTClient` and `GnaniTTSClient` using the official REST integration pattern.
- **Security:** Credentials read exclusively from `os.getenv("GNANI_API_KEY")`. No keys are hardcoded, logged, or printed.
- **Speech Text Normalization (`src/step4_voice/normalizer.py`):**
  - Dates: `2026-10-24` -> `"the 24th of October 2026"`
  - Currency: `₹49` -> `"forty-nine rupees"`, `₹10,000` -> `"ten thousand rupees"`
  - Order IDs: `89782837` -> `"8 9 7 8, 2 8 3 7"`
  - Pincodes: `560034` -> `"5 6 0 0 3 4"`
  - Markdown / Tags: Strips `[RET-2]`, bolding, and structural formatting to prevent synthetic artifacts during TTS.
- **Batch Audio Processor (`src/step4_voice/batch_processor.py`):**
  - Accepts `--input-dir <path>` and iterates through all audio files (`.wav`, `.mp3`, `.ogg`, `.pcm`, `.flac`, `.m4a`).
  - Measures per-file processing latency.
  - Gracefully handles empty or silent audio with dedicated status reporting (`status: "empty_transcript"`).
  - Handles missing credentials with transparent error recording (`status: "missing_api_key"`), outputting a complete manifest (`batch_manifest.json`) and individual JSON outputs per file.

---

## 5. Bonus Work Actually Implemented

1. **Multilingual Spoken Digit & Order ID Normalizer:** Built a specialized normalizer (`src/step4_voice/normalizer.py`) that extracts 8-digit order IDs and 4-digit verification values from mixed Hindi-English spoken transcripts (e.g., converting *"मेरे ऑर्डर एट नाइन सेवन एट टू एट थ्री सेवन"* directly into `"89782837"`), backed by 10 regression tests.
2. **Comprehensive Automated Test Suite:** Implemented 52 unit tests covering business-day arithmetic, policy return deadlines, document precedence, identity verification anti-leakage, voice normalization, and batch processor exception safety.
3. **Automated Submission Packaging CLI (`run.py --package`):** A zero-leakage packaging utility that programmatically filters secrets, dataset copies, caches, and virtual environments, validating the output ZIP structure automatically.
4. **Calendar Engine with Festival Closure Modeling:** Modeled Monday 19 October 2026 as a non-business warehouse festival closure alongside standard Sunday exclusions, correctly calculating refund SLA arrival deadlines.

---

## 6. Limitations & Unverified Functionality

1. **Voice Batch Live Verification:** While a live Gnani STT request was previously verified on record (`req_267bf9eb2815`), batch processing across the entire audio sample folder has been tested exclusively via deterministic offline mocks to avoid unmetered external API credit consumption without explicit authorization.
2. **Local vs Cloud Model Trade-Offs:** The local Qwen 2.5 3B model provides zero-cost, private, reproducible inference. However, in Step 2 RAG generation, smaller parametric models occasionally omit secondary details unless explicitly prompted with high-temperature contrastive instructions.
3. **Complex Multi-Item Returns:** In orders with multiple items across different return categories (e.g., fashion with 15 days return window alongside groceries with 0 days return window), disambiguation requires explicit line-item confirmation.
