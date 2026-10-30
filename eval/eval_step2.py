"""Evaluation script for Step 2: Knowledge RAG across all 52 practice questions."""
import csv
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config import PRACTICE_DIR, RESULTS_DIR
from src.step2_rag.generator import Step2RAG
from eval.metrics import evaluate_decision, evaluate_must_include, evaluate_must_not_include, evaluate_retrieval


def run_eval_step2(output_file: Optional[Path] = None, top_k: int = 5) -> Dict[str, Any]:
    """Run Step 2 Knowledge RAG evaluation on all 52 practice questions."""
    questions_file = PRACTICE_DIR / "questions.csv"
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = list(csv.DictReader(f))

    rag = Step2RAG()
    results = []

    total_decision_correct = 0
    total_fact_score = 0.0
    total_trap_clean = 0
    total_hit_1 = 0.0
    total_hit_3 = 0.0
    total_hit_5 = 0.0
    total_mrr = 0.0
    total_hn_avoided = 0

    print(f"Starting Step 2 Knowledge RAG Evaluation on {len(questions)} questions (top_k={top_k})...")
    start_time = time.time()

    for idx, q in enumerate(questions, 1):
        q_id = q["id"]
        q_text = q["question"]
        lang = q["language"]
        exp_dec = q["expected_decision"]
        acc_dec = q.get("acceptable_decisions")
        gold_ev = q.get("gold_evidence", "")
        hard_neg = q.get("hard_negatives", "")
        must_inc = q.get("must_include", "")
        must_not_inc = q.get("must_not_include", "")

        out = rag.process_query(q_text, language=lang, top_k=top_k)

        # Retrieval metrics
        ret_metrics = evaluate_retrieval(out["retrieved_evidence"], gold_ev, hard_neg)
        total_hit_1 += ret_metrics["hit_at_1"]
        total_hit_3 += ret_metrics["hit_at_3"]
        total_hit_5 += ret_metrics["hit_at_5"]
        total_mrr += ret_metrics["mrr"]
        if ret_metrics["avoided_hard_negatives"]:
            total_hn_avoided += 1

        # Response metrics
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
            "retrieved_evidence": out["retrieved_evidence"],
            "sections_used": out.get("sections_used", []),
            "hit_at_1": ret_metrics["hit_at_1"],
            "hit_at_3": ret_metrics["hit_at_3"],
            "hit_at_5": ret_metrics["hit_at_5"],
            "mrr": ret_metrics["mrr"],
            "avoided_hard_negatives": ret_metrics["avoided_hard_negatives"],
            "reply": out["reply"],
            "fact_score": fact_score,
            "missing_facts": missing,
            "trap_clean": trap_clean,
            "trap_violations": violations,
            "gold_evidence": gold_ev
        }
        results.append(record)
        print(f"[{idx}/{len(questions)}] {q_id} | Dec: {'OK' if dec_ok else 'FAIL'} | Fact: {fact_score:.2f} | Hit@1: {ret_metrics['hit_at_1']} | Hit@3: {ret_metrics['hit_at_3']} | MRR: {ret_metrics['mrr']:.2f}")

    n = len(questions)
    elapsed = round(time.time() - start_time, 2)
    summary = {
        "step": "step2_rag",
        "total_questions": n,
        "decision_accuracy": round(total_decision_correct / n, 4),
        "mean_fact_score": round(total_fact_score / n, 4),
        "trap_safety_rate": round(total_trap_clean / n, 4),
        "hit_at_1": round(total_hit_1 / n, 4),
        "hit_at_3": round(total_hit_3 / n, 4),
        "hit_at_5": round(total_hit_5 / n, 4),
        "mrr": round(total_mrr / n, 4),
        "hard_negative_avoidance_rate": round(total_hn_avoided / n, 4),
        "elapsed_seconds": elapsed,
        "results": results
    }

    dest = output_file or (RESULTS_DIR / "results_step2.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== STEP 2 RAG RESULTS ===")
    print(f"Decision Accuracy:  {summary['decision_accuracy'] * 100:.1f}%")
    print(f"Mean Fact Score:    {summary['mean_fact_score'] * 100:.1f}%")
    print(f"Trap Safety Rate:   {summary['trap_safety_rate'] * 100:.1f}%")
    print(f"Retrieval Hit@1:    {summary['hit_at_1'] * 100:.1f}%")
    print(f"Retrieval Hit@3:    {summary['hit_at_3'] * 100:.1f}%")
    print(f"Retrieval Hit@5:    {summary['hit_at_5'] * 100:.1f}%")
    print(f"Retrieval MRR:      {summary['mrr']:.3f}")
    print(f"Hard Negative Avoid:{summary['hard_negative_avoidance_rate'] * 100:.1f}%")
    print(f"Saved results to:   {dest}")
    return summary


if __name__ == "__main__":
    run_eval_step2()
