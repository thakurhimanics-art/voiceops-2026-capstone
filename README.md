# ZentroMart VoiceOps 2026 — Capstone Project

Comprehensive AI Customer Support Agent with Policy-Grounded RAG, Identity-Gated Multi-Turn Dialogue, and Gnani.ai Voice Capabilities.

Built for **VoiceOps 2026** by Consulting & Analytics Club, IIT Guwahati × Gnani.ai.

---

## 1. System Overview

ZentroMart is an educational, synthetic customer support AI system for an Indian e-commerce platform. The system operates on a fixed reference date of **20 October 2026** and implements a four-step pipeline:

- **Step 1 (Prompt-Only Baseline):** Establishes the ZentroMart AI support assistant role without policy retrieval, serving as a baseline for hallucination analysis.
- **Step 2 (Knowledge RAG):** Hybrid lexical (BM25) and semantic retrieval indexing 21 knowledge base documents and product catalog entries. Enforces document precedence (`Policy > Agent Guide > Help > FAQ > Marketing`) and filters out superseded documents (`POL-RET-v3`) and historical support logs (`support_logs.csv`). Answers are dynamically grounded in retrieved section text without test-case hardcoding.
- **Step 3 (Multi-Turn Stateful Agent):** Tracks conversation context, enforces caller identity verification (4-digit phone suffix or 6-digit delivery pincode), prevents data leaks to unverified callers, handles coreference resolution, and manages policy-mandated escalations and refusals.
- **Step 4 (Gnani.ai Voice Pipeline):** Powered exclusively by Gnani.ai (`gnani-vachana` SDK) using the official REST integration pattern for STT and TTS, featuring speech text normalization per STY-3 and batch processing of customer audio folders.

---

## 2. Directory Structure

```text
VoiceOps/
├── Capstone_Project_Dataset_FTTT_2026/   # Source of truth dataset (untouched)
├── src/
│   ├── config.py                         # Reference date (2026-10-20), holidays, return windows
│   ├── llm_client.py                     # Unified client (local Ollama default, API compatible)
│   ├── step1_baseline.py                 # Step 1: Prompt-only assistant
│   ├── step2_rag/
│   │   ├── parser.py                     # Markdown frontmatter, section parser & product catalog parser
│   │   ├── indexer.py                    # Precedence engine and anti-superseded filter
│   │   ├── retriever.py                  # Hybrid BM25 with Hindi/English synonyms & trap suppression
│   │   └── generator.py                  # Grounded generation citing section IDs & dynamic date math
│   ├── step3_agent/
│   │   ├── state.py                      # Multi-turn conversation state manager
│   │   ├── tools_adapter.py              # Mock tools wrapper with verification guardrails
│   │   ├── rules.py                      # Escalation (ESC-1) and refusal logic (CAN-2, DEL-4)
│   │   └── agent.py                      # Multi-turn agent brain
│   └── step4_voice/
│       ├── normalizer.py                 # Speech normalizer (dates, rupees, 4-digit order IDs per STY-3)
│       ├── gnani_client.py               # Official Gnani.ai STT & TTS REST SDK integration
│       └── batch_processor.py            # Audio folder batch processor generating manifests & latency stats
├── eval/
│   ├── eval_step1.py                     # Evaluates 52 practice questions on Step 1 baseline
│   ├── eval_step2.py                     # Evaluates 52 practice questions on Step 2 RAG
│   ├── eval_step3.py                     # Evaluates 23 conversations (96 turns) on Step 3 agent
│   └── metrics.py                        # Factuality, decision, and retrieval metrics
├── tests/
│   ├── test_rules.py                     # Business-day calendar and return policy tests
│   ├── test_retrieval.py                 # Section IDs, precedence, and trap avoidance tests
│   ├── test_step2_rag_grounding.py       # Grounding, paraphrasing, unseen queries & unsupported checks
│   ├── test_verification.py              # Identity verification and data leakage tests
│   ├── test_tools.py                     # Mock tools adapter tests
│   ├── test_voice_batch.py               # Batch processor exception handling & mock tests
│   ├── test_voice_normalizer.py          # STY-3 text normalization unit tests
│   ├── test_voice_order_extraction.py    # Spoken Hindi-English order ID & digit extraction tests
│   └── test_submission_zip.py            # Automated submission archive verification
├── results/                              # Evaluation outputs and batch manifests (JSON)
├── sample_outputs/                       # Pre-generated sample outputs
├── sample_inputs/                        # Sample input audio for batch demonstration
├── run.py                                # Unified CLI entry point
├── generate_report_pdf.py                # Compiles report.pdf from REPORT.md
├── requirements.txt                      # Project dependencies
├── .env.example                          # Environment configuration template
├── report.pdf                            # 4-page final capstone report
├── REPORT.md                             # Editable source report
└── DEMO_SCRIPT.md                        # 2-minute video presentation storyboard and script
```

---

## 3. Installation & Setup

### Prerequisites
- Python 3.10, 3.11, or 3.12
- Optional: [Ollama](https://ollama.com/) with `qwen2.5:3b` pulled for zero-cost local LLM inference:
  ```bash
  ollama pull qwen2.5:3b
  ```

### Installation
1. Clone or extract the repository:
   ```bash
   cd VoiceOps
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows PowerShell:
   .\venv\Scripts\Activate.ps1
   # On Linux / macOS:
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure environment variables:
   ```bash
   copy .env.example .env
   ```
   Add your `GNANI_API_KEY` for Step 4 voice operations. For local LLM inference, default settings connect to `http://127.0.0.1:11434` with `qwen2.5:3b`.

---

## 4. Execution Commands (`run.py`)

`run.py` is the single CLI entry point for all operations.

### 1. Run Automated Test Suite
```bash
python run.py --test
```
Executes all **52 unit tests** verifying business rules, return windows, precedence filtering, identity gating, RAG grounding, voice normalization, and mock batch processing.

### 2. Run Dataset Validation
```bash
python Capstone_Project_Dataset_FTTT_2026/validate_dataset.py
```
Validates relational integrity, schema keys, and reference date rules across all 9 CSVs and 21 KB documents.

### 3. Run Evaluations
- **Step 1 Baseline (52 questions):**
  ```bash
  python run.py --eval step1
  ```
- **Step 2 Knowledge RAG (52 questions):**
  ```bash
  python run.py --eval step2
  ```
- **Step 3 Multi-Turn Agent (23 conversations / 96 turns):**
  ```bash
  python run.py --eval step3
  ```
- **Run All Evaluations:**
  ```bash
  python run.py --eval all
  ```

### 4. Interactive CLI Support Chat
Test multi-turn customer dialogues interactively:
```bash
python run.py --chat
```

### 5. Step 4 Voice Batch Processing
Process an entire folder of audio files (`.wav`, `.mp3`, `.m4a`, etc.):
```bash
python run.py --voice-batch --input-dir sample_inputs/audio_sample/
```
Output files, synthesized audio responses, and `batch_manifest.json` are saved to `results/voice_batch_output/`.

### 6. Package Submission ZIP
Generate a clean, rubric-compliant submission archive:
```bash
python run.py --package --team-name zentromart
```
Automatically packages required deliverables and excludes the dataset, `.env` secrets, `.git`, cache folders, and virtual environments.

---

## 5. Verified Benchmark Results

| Stage / Component | Metric | Actual Score |
| :--- | :--- | :---: |
| **Dataset Validator** | Relational integrity & verification gates | **PASS (100%)** |
| **Step 1 Baseline** | Decision Accuracy<br>Mean Fact Score<br>Trap Safety Rate | 71.2%<br>19.9%<br>100.0% |
| **Step 2 Grounded RAG** | Retrieval Hit@1<br>Retrieval Hit@3<br>Retrieval Hit@5<br>Decision Accuracy<br>Mean Fact Score | **90.4%**<br>**100.0%**<br>**100.0%**<br>**100.0%**<br>**100.0%** |
| **Step 3 Multi-Turn Agent** | Conversation Pass Rate<br>Turn Decision Accuracy<br>Tool Invocation Accuracy<br>Fact Score | **100.0% (23/23)**<br>**100.0% (96/96)**<br>**100.0% (54/54)**<br>**100.0%** |
| **Unit Test Suite** | 52 unit tests passing | **100% (52 / 52)** |

---

## 6. Security & Policy Adherence
- **Data Protection:** Order items, delivery addresses, and payment amounts are strictly withheld until the customer verifies their identity.
- **Precedence Hierarchy:** Authoritative policy documents (`POL-*`) strictly supersede FAQs and marketing copy.
- **Reference Date Math:** All timelines strictly calculate business days (Monday–Saturday, excluding warehouse festival holidays like 19 October 2026) relative to **20 October 2026**.
