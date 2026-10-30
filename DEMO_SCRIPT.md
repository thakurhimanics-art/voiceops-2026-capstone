# ZentroMart VoiceOps 2026 — 2-Minute Video Demo Script & Recording Guide

This document provides the exact, timed storyboard, narration script, and recording instructions to produce the mandatory 2-minute (`demo.mp4`) video submission for VoiceOps 2026.

---

## Storyboard & Timing Breakdown (Total: 120 Seconds Max)

```
[0:00 - 0:20] Scene 1: Introduction & Source of Truth Integrity
[0:20 - 0:50] Scene 2: Grounded Knowledge RAG (Step 2 vs Step 1 Baseline)
[0:50 - 1:25] Scene 3: Multi-Turn Agent — Identity Gating, Context & Escalation (Step 3)
[1:25 - 1:45] Scene 4: Voice Pipeline via Gnani.ai & Speech Normalization (Step 4)
[1:45 - 2:00] Scene 5: Automated Test Suite, Package Integrity & Conclusion
```

---

### [0:00 – 0:20] Scene 1: Introduction & Source of Truth Integrity

**Visual:**  
Terminal opened at project root `VoiceOps/`. Run the dataset validator:
```bash
python Capstone_Project_Dataset_FTTT_2026/validate_dataset.py
```

**Action:**  
Point to the console output:
`PASS — all 9 CSVs, 21 KB documents, primary/foreign keys, order math, practice evidence, verification gates and company naming validated.`

**Voiceover Narration:**  
> *"Welcome to the ZentroMart VoiceOps 2026 capstone presentation for IIT Guwahati and Gnani.ai. We begin by verifying our source of truth on the fixed reference date of 20 October 2026: all 9 CSV tables, 21 policy documents, and relational keys pass full structural validation with zero errors."*

---

### [0:20 – 0:50] Scene 2: Grounded Knowledge RAG (Step 1 vs Step 2)

**Visual:**  
Terminal showing Step 2 evaluation execution:
```bash
python run.py --eval step2
```

**Action:**  
Highlight how the RAG system dynamically retrieves section `[REF-2]` and holiday calendar `[KB-00.3]`, suppressing the superseded `POL-RET-v3` and avoiding the `FAQ-1` trap:
- Query: *"How fast are refunds to ZentroMart Wallet?"* -> Grounded Answer: *"Instant, within 2 hours of initiation [REF-2]"*.
- Query: *"Can I schedule a delivery at midnight?"* -> Grounded Uncertainty: *"Sorry, I don't have information about that. I can connect you to a colleague who can help."*

**Voiceover Narration:**  
> *"In Step 2, we implement genuine retrieval-augmented generation. Rather than hardcoding responses, our hybrid BM25 retriever indexes 21 knowledge sections and catalog products, strictly enforcing document precedence: Policy over FAQ. For wallet refunds, it retrieves REF-2, correctly outputting instant refund within 2 hours. When an ungrounded query like midnight delivery is asked, it avoids hallucination and offers a colleague connection."*

---

### [0:50 – 1:25] Scene 3: Multi-Turn Agent — Identity Gating & Safe Handover

**Visual:**  
Start interactive CLI chat:
```bash
python run.py --chat
```

**Action / Turn Walkthrough:**  
1. **Turn 1 (Greeting & AI Disclosure):**  
   - Customer: `"Hello, mujhe mere order ke baare mein help chahiye."`  
   - Assistant: Identifies as AI assistant per STY-1 and asks for 8-digit order number.
2. **Turn 2 (Order ID & Verification Gate):**  
   - Customer: `"Order number hai 8978 2837"`  
   - Assistant: Calls `lookup_order(89782837)` without verification value. Private order details are strictly withheld: *"Suraksha ke liye, kripya apne registered phone number ke aakhri 4 digits ya delivery pincode share karein."*
3. **Turn 3 (Verification Success):**  
   - Customer: `"Last four digits 4533 hain"`  
   - Assistant: Validates identity, unlocks synthetic order data, and greets customer safely.
4. **Turn 4 (Contextual Follow-up & High-Value Damage Handover):**  
   - Customer: `"Is TV ka screen toota hua nikla, turant refund ya replacement approve kar do."`  
   - Assistant: Detects damaged item worth > ₹10,000 (`DWM-3`), creates ticket `create_ticket()` with summary, refuses unauthorized immediate payouts (`ESC-4`), and safely hands over to the Priority Resolution team.

**Voiceover Narration:**  
> *"In Step 3, our multi-turn stateful agent manages dialogue context and strict caller authentication. When the order number is first shared, zero private data is leaked until the caller provides their registered phone suffix or pincode. Once verified, when the caller reports damage on a television exceeding ₹10,000, the agent adheres to policy: it refuses unapproved compensation, raises a support ticket, and escalates directly to human colleagues."*

---

### [1:25 – 1:45] Scene 4: Voice Pipeline via Gnani.ai & Normalization

**Visual:**  
Show the batch voice CLI processing a customer audio folder:
```bash
python run.py --voice-batch --input-dir sample_inputs/audio_sample/
```

**Action:**  
Display the generated manifest and normalized speech text:
- Spoken order IDs grouped into 4-digit chunks (`"8 9 7 8, 2 8 3 7"`).
- Spoken dates (`"the 24th of October 2026"`).
- Spoken rupees (`"forty-nine rupees"`).

**Voiceover Narration:**  
> *"Step 4 integrates Gnani.ai's REST STT and TTS SDK. The voice pipeline shares the exact same agent brain, normalizes currency, dates, and order numbers into natural speech per STY-3, and batch-processes audio folders with per-file latency logging, exception recovery, and manifest generation."*

---

### [1:45 – 2:00] Scene 5: Test Suite, Packaging & Wrap-Up

**Visual:**  
Run test suite and packaging:
```bash
python run.py --test
python run.py --package --team-name zentromart
```

**Action:**  
Show all 52 unit tests passing, clean ZIP packaging with zero secret leaks, and display `report.pdf`.

**Voiceover Narration:**  
> *"All 52 unit tests pass across our business rules, retrieval engine, verification gates, and voice normalizer. The automated package command verifies zero credential or dataset leakage. Thank you."*

---

## How to Record This Video (Step-by-Step for the User)

1. **Tools:** Use **OBS Studio** or **Windows Game Bar** (`Win + Alt + R` to start/stop recording).
2. **Setup:** Set screen resolution to 1080p (1920x1080). Open PowerShell in `C:\Users\Himani Thakur\Desktop\VoiceOps`.
3. **Pacing:** Practice speaking with a timer to ensure the video finishes under **120 seconds** (1 minute 50 seconds is ideal).
4. **Save File:** Save the exported MP4 file directly to:  
   `C:\Users\Himani Thakur\Desktop\VoiceOps\demo.mp4`
