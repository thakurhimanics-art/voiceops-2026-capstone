"""Unified CLI entry point for ZentroMart VoiceOps 2026.

Supports:
- Evaluation: --eval [all|step1|step2|step3]
- Interactive Chat: --chat
- Voice Batch Processing: --voice-batch --input-dir <dir> [--output-dir <dir>]
- Testing: --test
- Packaging: --package [--name <name>]
"""
import argparse
import sys
import os
import shutil
import zipfile
from pathlib import Path

from src.config import PROJECT_ROOT, RESULTS_DIR, PRACTICE_DIR, DATASET_ROOT


def run_evaluation(step: str):
    """Run evaluation for specified step or all."""
    from eval.eval_step1 import run_eval_step1
    from eval.eval_step2 import run_eval_step2
    from eval.eval_step3 import run_eval_step3

    step = step.lower()
    if step in ("step1", "all"):
        print("\n================== STEP 1: BASELINE EVALUATION ==================")
        run_eval_step1()

    if step in ("step2", "all"):
        print("\n================== STEP 2: KNOWLEDGE RAG EVALUATION ==============")
        run_eval_step2()

    if step in ("step3", "all"):
        print("\n================== STEP 3: MULTI-TURN AGENT EVALUATION ==========")
        run_eval_step3()


def run_interactive_chat():
    """Start an interactive multi-turn chat session."""
    from src.step3_agent.agent import ZentroMartAgent
    agent = ZentroMartAgent()
    cid = "chat_cli_session"
    turn = 1
    print("\n========================================================")
    print(" ZentroMart AI Support Assistant — Interactive Chat")
    print(" Type 'exit' or 'quit' to end the session.")
    print("========================================================\n")

    while True:
        try:
            user_msg = input(f"\nCustomer (Turn {turn}): ").strip()
            if not user_msg:
                continue
            if user_msg.lower() in ("exit", "quit", "q"):
                print("Ending support session. Goodbye!")
                break

            res = agent.process_turn(cid, user_msg, turn_number=turn)
            print(f"\nAssistant: {res['reply']}")
            if res.get("tool_calls"):
                print(f"  [Tool Calls Executed]: {res['tool_calls']}")
            if res.get("gold_evidence"):
                print(f"  [Policies Cited]: {res['gold_evidence']}")
            turn += 1
        except (KeyboardInterrupt, EOFError):
            print("\nSession interrupted. Goodbye!")
            break


def run_voice_batch(input_dir: str, output_dir: str = None, lang: str = "hi-IN"):
    """Execute batch audio processing on an input folder."""
    from src.step4_voice.batch_processor import VoiceBatchProcessor
    processor = VoiceBatchProcessor()
    processor.process_folder(input_dir=input_dir, output_dir=output_dir, language_code=lang)


def run_tests():
    """Run pytest suite."""
    import pytest
    print("\nRunning test suite...")
    code = pytest.main(["-v", "tests/"])
    return code


def build_submission_zip(submission_name: str = "himani_thakur"):
    """Create clean submission zip excluding dataset, pycache, venv, and secrets."""
    clean_name = "".join(c for c in submission_name if c.isalnum() or c in ("_", "-")).lower()
    zip_name = f"{clean_name}_voiceops.zip"
    zip_path = PROJECT_ROOT / zip_name

    print(f"\nPackaging clean submission archive: {zip_name}...")

    # Excluded directories and patterns
    EXCLUDE_DIRS = {
        "Capstone_Project_Dataset_FTTT_2026",
        ".git",
        ".gemini",
        "__pycache__",
        ".pytest_cache",
        "venv",
        ".venv",
        "env",
    }
    EXCLUDE_EXTS = {".pyc", ".pyo", ".pyd", ".env", ".zip"}

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PROJECT_ROOT):
            # Prune excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.endswith(".egg-info")]

            rel_root = Path(root).relative_to(PROJECT_ROOT)
            if any(part in EXCLUDE_DIRS for part in rel_root.parts):
                continue

            for file in files:
                if file.startswith(".env") and file != ".env.example":
                    continue
                if any(file.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue

                full_path = Path(root) / file
                rel_path = full_path.relative_to(PROJECT_ROOT)
                arcname_str = str(rel_path).replace("\\", "/")
                if arcname_str.lower() == "report.pdf":
                    arcname_str = "report.pdf"
                zipf.write(full_path, arcname_str)

    print(f"Submission archive created successfully: {zip_path}")
    print(f"Archive size: {zip_path.stat().st_size / 1024:.1f} KB")

    # Verify no dataset or secrets in ZIP
    with zipfile.ZipFile(zip_path, "r") as z:
        names = z.namelist()
        has_dataset = any("Capstone_Project_Dataset_FTTT_2026" in n for n in names)
        has_secret = any(".env" in n and ".env.example" not in n for n in names)
        assert not has_dataset, "Security check failed: Dataset present in zip!"
        assert not has_secret, "Security check failed: Secret .env file present in zip!"
    print("Verification check passed: Archive is clean and compliant with rules.")


def main():
    parser = argparse.ArgumentParser(
        description="ZentroMart VoiceOps 2026 Capstone Submission Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--eval", choices=["step1", "step2", "step3", "all"], help="Run evaluation for Step 1, 2, 3, or all")
    parser.add_argument("--chat", action="store_true", help="Start interactive CLI support chat")
    parser.add_argument("--voice-batch", action="store_true", help="Process folder of customer audio files")
    parser.add_argument("--input-dir", type=str, help="Input directory containing customer audio files")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory for transcriptions and audio replies")
    parser.add_argument("--language", type=str, default="hi-IN", help="Audio language code (default: hi-IN)")
    parser.add_argument("--test", action="store_true", help="Run pytest unit test suite")
    parser.add_argument("--package", action="store_true", help="Create clean submission ZIP")
    parser.add_argument("--submission-name", "--name", "--team-name", dest="submission_name", type=str, default="himani_thakur", help="Submission name prefix for ZIP (default: himani_thakur)")

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    args = parser.parse_args()

    if args.eval:
        run_evaluation(args.eval)
    elif args.chat:
        run_interactive_chat()
    elif args.voice_batch:
        if not args.input_dir:
            print("Error: --input-dir is required when using --voice-batch")
            sys.exit(1)
        run_voice_batch(args.input_dir, args.output_dir, args.language)
    elif args.test:
        code = run_tests()
        sys.exit(code)
    elif args.package:
        build_submission_zip(args.submission_name)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
