# ZentroMart VoiceOps 2026 — Exact Demo Recording Guide

This is the step-by-step recording guide for producing the mandatory, verified 2-minute demonstration video (`demo.mp4`) for the VoiceOps 2026 capstone submission.

---

## 1. Video Specifications & Setup Checklist

- **Target Duration:** 1 minute 45 seconds to 1 minute 55 seconds (Strict Cap: **120 seconds / 2 minutes**).
- **Target Filename:** `C:\Users\Himani Thakur\Desktop\VoiceOps\demo.mp4`
- **Resolution:** 1080p (1920x1080) at 30 or 60 fps.
- **Recording Tools:**
  - **Option A (Built-in Windows):** Press `Win + Alt + R` (Xbox Game Bar) to start and stop recording. Ensure system audio recording is turned ON.
  - **Option B (Recommended):** **OBS Studio** recording the display or terminal window with Desktop Audio captured.
- **Important Interface Note:**  
  `python run.py --chat` is the **text-based interactive terminal interface** for testing and demonstrating the Step 3 stateful agent, dialogue context, verification gating, and tool execution. Voice capabilities (STT/TTS) are demonstrated in Step 4 via the batch audio processor and the verified playback of the live Gnani audio artifact (`sample_outputs/live_gnani_tts_test.wav`).

---

## 2. Timed Scene-by-Scene Storyboard & Narration

### Scene 1: Dataset Validation & Reference Date Integrity [0:00 – 0:20]

**On-Screen Action:**  
Open PowerShell in `C:\Users\Himani Thakur\Desktop\VoiceOps` and run:
```powershell
python Capstone_Project_Dataset_FTTT_2026/validate_dataset.py
```

**Expected Terminal Output:**
```
PASS — all 9 CSVs, 21 KB documents, primary/foreign keys, order math, practice evidence, verification gates and company naming validated.
```

**Spoken Narration (approx. 18 seconds):**  
> *"Welcome to the ZentroMart VoiceOps 2026 capstone presentation for IIT Guwahati and Gnani.ai. I am Himani Thakur, presenting my individual capstone implementation. We anchor all operational logic on our fixed reference date of 20 October 2026. Running our dataset validator confirms all 9 relational tables, 21 policy documents, and data integrity constraints pass structural validation with zero errors."*

---

### Scene 2: Grounded Knowledge RAG (Step 2 vs Step 1 Baseline) [0:20 – 0:45]

**On-Screen Action:**  
In the terminal, run the Step 2 evaluation suite:
```powershell
python run.py --eval step2
```

**Expected Terminal Output:**  
Shows 52/52 passing benchmark queries with 100% Decision Accuracy and 100% Fact Score:
```
Accuracy: 52/52 (100.0%)
Policy Precedence Enforced (REF-2 over FAQ-1)
Hard Negative & Outdated Policy Suppression: 100%
```

**Spoken Narration (approx. 22 seconds):**  
> *"In Step 2, our hybrid BM25 retriever indexes 21 knowledge base sections and the full product catalog. Crucially, it strictly enforces document precedence: active policy supersedes obsolete drafts and FAQs. For instance, wallet refunds correctly resolve to instant credit within 2 hours under REF-2, while out-of-scope questions trigger safe, grounded abstention."*

---

### Scene 3: Multi-Turn Agent — Identity Gating & Safe Handover [0:45 – 1:20]

**On-Screen Action:**  
Launch the interactive agent CLI:
```powershell
python run.py --chat
```

Copy and paste each turn prompt consecutively:

#### **Turn 1: Greeting & AI Self-Disclosure**
- **You Type:**
  ```text
  Hello, mujhe mere order ke baare mein help chahiye.
  ```
- **Terminal Displays:**
  ```
  Assistant: Namaste! I am the ZentroMart AI customer service assistant. I would be glad to help you with your order. Could you please provide your 8-digit order number?
  ```

#### **Turn 2: Order Lookup & Identity Protection Gate**
- **You Type:**
  ```text
  Order number hai 8978 2837
  ```
- **Terminal Displays:**
  ```
  Assistant: Thank you. For your security and to protect your account details, could you please confirm the last 4 digits of your registered phone number or your delivery pincode?
    [Tool Calls Executed]: [{'tool': 'lookup_order', 'args': {'order_id': 89782837}, 'result': 'UNVERIFIED'}]
  ```
- *(Point cursor to show that customer name, address, and item list are strictly locked.)*

#### **Turn 3: Verification Unlock**
- **You Type:**
  ```text
  Last four digits 4533 hain
  ```
- **Terminal Displays:**
  ```
  Assistant: Thank you Kabir, your verification is successful! How can I help you with order 89782837 today?
    [Tool Calls Executed]: [{'tool': 'lookup_order', 'args': {'order_id': 89782837, 'verification_value': '4533'}, 'result': 'VERIFIED'}]
  ```

#### **Turn 4: Contextual Follow-up (Delivery Status)**
- **You Type:**
  ```text
  Is order ka delivery status kya hai?
  ```
- **Terminal Displays:**
  ```
  Assistant: Your order was successfully delivered on 15 October 2026.
    [Tool Calls Executed]: []
  ```
- *(Notice: Customer does not repeat order number, customer name, or item name; agent answers directly from the verified session context.)*

#### **Turn 5: Damaged High-Value Product Escalation**
- **You Type:**
  ```text
  mere Tv ka screen tuta hua h please replacement krdo
  ```
  *(Natural variations like "My TV screen arrived broken. Please replace it." or "Mere TV ka screen toot gaya hai" also fully supported)*
- **Terminal Displays:**
  ```
  Assistant: Damage claims for items exceeding ₹10,000 require review and cannot be immediately approved per policy (DWM-3, ESC-4). I have created a priority ticket (TKT...) for our Priority Resolution team, and a colleague will contact you to resolve this.
    [Tool Calls Executed]: ['create_ticket()']
  ```
- **You Type:**
  ```text
  exit
  ```

**Spoken Narration (approx. 33 seconds):**  
> *"In Step 3, our stateful agent manages dialogue state and caller identity gating. When order 89782837 is entered, private account details remain locked until the caller authenticates with their phone suffix '4533'. Once authenticated as Kabir Mehta, a follow-up inquiry on delivery status resolves seamlessly from session context. When the caller reports damage on a ₹31,649 television, the agent enforces policy: it denies unapproved compensation, invokes create_ticket, and routes the issue to our human escalation team."*

---

### Scene 4: Voice Pipeline via Gnani.ai & Speech Normalization [1:20 – 1:40]

**On-Screen Action:**  
Demonstrate the voice pipeline speech normalizer and play the verified live Gnani TTS synthesis:
```powershell
powershell -Command "(New-Object System.Media.SoundPlayer ((Resolve-Path 'sample_outputs\live_gnani_tts_playback.wav').Path)).PlaySync()"
```
*(Or run the batch voice processor)*:
```powershell
python run.py --voice-batch --input-dir sample_inputs/audio_sample/
```

**What the Audience Hears / Sees:**
- The clear Hindi speech audio synthesized directly by Gnani's `timbre-v2.5` model (Voice: Kaveri, Request ID: `req_239a47818eaa`).
- The speech normalizer converting raw dates (`24/10/2026` -> `"the 24th of October 2026"`), currency (`₹31,649` -> `"thirty-one thousand six hundred forty-nine rupees"`), and order IDs (`8978 2837` -> `"8 9 7 8, 2 8 3 7"`).

**Spoken Narration (approx. 18 seconds):**  
> *"Step 4 integrates Gnani.ai speech recognition and text-to-speech. Our pipeline normalizes currency, dates, and segmented digits for natural Hindi-English acoustics, as heard in this live audio synthesized using Gnani's timbre-v2.5 engine."*

---

### Scene 5: Automated Test Suite & Packaging [1:40 – 2:00]

**On-Screen Action:**  
Run the complete automated test suite:
```powershell
python run.py --test
```

**Expected Terminal Output:**
```
============================= 57 passed in 1.14s ==============================
```

Quickly show that `report.pdf` is present and exactly 4 pages.

**Spoken Narration (approx. 15 seconds):**  
> *"All 57 unit tests pass in one second across business rules, retrieval grounding, verification security, and voice normalization. The packaging tool creates himani_thakur_voiceops.zip, and my four-page technical report and submission archive are fully verified. Thank you."*

---

## 3. Quick Copy-Paste Reference for Recording

Keep these exact lines ready on a second screen or notepad to copy-paste quickly during the recording:

| Turn | Copy-Paste Text |
|---|---|
| **Turn 1** | `Hello, mujhe mere order ke baare mein help chahiye.` |
| **Turn 2** | `Order number hai 8978 2837` |
| **Turn 3** | `Last four digits 4533 hain` |
| **Turn 4** | `Is order ka delivery status kya hai?` |
| **Turn 5** | `mere Tv ka screen tuta hua h please replacement krdo` |
| **Exit** | `exit` |

**Live TTS Playback Command:**
```powershell
(New-Object System.Media.SoundPlayer "$PWD\sample_outputs\live_gnani_tts_playback.wav").PlaySync()
```

---

## 4. Verification Check Before Video Export

1. Check video duration: Must be **<= 120 seconds** (e.g., 01:48).
2. Check audio track: Ensure both your voiceover and the live Gnani audio sample are audible.
3. Save output file as:
   `C:\Users\Himani Thakur\Desktop\VoiceOps\demo.mp4`
4. Confirm file size is under 50 MB for easy upload/submission.

