"""Evaluation script for Step 1: Baseline Prompt-Only LLM across all 52 practice questions."""
import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config import PRACTICE_DIR, RESULTS_DIR
from src.step1_baseline import Step1Baseline
from eval.metrics import evaluate_decision, evaluate_must_include, evaluate_must_not_include


def run_eval_step1(output_file: Optional[Path] = None) -> Dict[str, Any]:
    """Run Step 1 baseline evaluation on all 52 practice questions."""
    questions_file = PRACTICE_DIR / "questions.csv"
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    baseline = Step1Baseline()
    results = []

    total_decision_correct = 0
    total_fact_score = 0.0
    total_trap_clean = 0

    print(f"Starting Step 1 Baseline Evaluation on {len(questions)} questions...")
    start_time = time.time()

    for idx, q in enumerate(questions, 1):
        q_id = q["id"]
        q_text = q["question"]
        lang = q["language"]
        exp_dec = q["expected_decision"]
        acc_dec = q.get("acceptable_decisions")
        must_inc = q.get("must_include", "")
        must_not_inc = q.get("must_not_include", "")

        out = baseline.process_query(q_text, language=lang)
        dec_ok = evaluate_decision(out["decision"], exp_dec, acc_dec)
        fact_score, missing = evaluate_must_include(out["reply"], must_inc)
        trap_clean, violations = evaluate_must_not_include(out["reply"], must_not_inc)

        if dec_ok:
            total_decision_correct += 1
        total_fact_score += fact_score
        if trap_clean:
            total_trap_clean += 1

        record = {
            "id": q_id,
            "question": q_text,
            "language": lang,
            "intent": q["intent"],
            "expected_decision": exp_dec,
            "actual_decision": out["decision"],
            "decision_correct": dec_ok,
            "reply": out["reply"],
            "fact_score": fact_score,
            "missing_facts": missing,
            "trap_clean": trap_clean,
            "trap_violations": violations,
            "gold_evidence": q.get("gold_evidence", "")
        }
        results.append(record)
        print(f"[{idx}/{len(questions)}] {q_id} | Dec: {'OK' if dec_ok else 'FAIL'} | Fact: {fact_score:.2f} | Trap Clean: {trap_clean}")

    n = len(questions)
    elapsed = round(time.time() - start_time, 2)
    summary = {
        "step": "step1_baseline",
        "total_questions": n,
        "decision_accuracy": round(total_decision_correct / n, 4),
        "mean_fact_score": round(total_fact_score / n, 4),
        "trap_safety_rate": round(total_trap_clean / n, 4),
        "elapsed_seconds": elapsed,
        "results": results
    }

    dest = output_file or (RESULTS_DIR / "results_step1.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== STEP 1 BASELINE RESULTS ===")
    print(f"Decision Accuracy: {summary['decision_accuracy'] * 100:.1f}%")
    print(f"Mean Fact Score:   {summary['mean_fact_score'] * 100:.1f}%")
    print(f"Trap Safety Rate:  {summary['trap_safety_rate'] * 100:.1f}%")
    print(f"Saved results to: {dest}")
    return summary


if __name__ == "__main__":
    from typing import Optional
    run_eval_step1()
