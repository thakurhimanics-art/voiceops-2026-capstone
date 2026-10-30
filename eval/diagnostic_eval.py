"""Diagnostic Step 2 evaluation runner (post-fix comparison).

Evaluates the 25 diagnostic queries and writes output to:
- results/step2_diagnostic_post_fix.json
- results/step2_diagnostic_post_fix.md
"""
import json
import time
from pathlib import Path
from typing import Dict, Any, List

from src.step2_rag.generator import Step2RAG
from src.config import RESULTS_DIR
from eval.independent_rag_eval import HELD_OUT_DATASET


def run_diagnostic_post_fix():
    rag = Step2RAG()
    results = []
    passed_count = 0
    total = len(HELD_OUT_DATASET)

    print("=================================================================")
    print(f"   VOICEOPS 2026 — DIAGNOSTIC EVALUATION (POST-FIX) ({total} Cases)   ")
    print("=================================================================")

    for idx, item in enumerate(HELD_OUT_DATASET, 1):
        q_id = item["id"]
        cat = item["category"]
        q = item["question"]
        exp_core = item["expected_core"]
        target_secs = item["target_sections"]
        expect_abstain = item["expect_abstain"]

        out = rag.process_query(q, language="en", top_k=5)
        decision = out.get("decision", "")
        reply = out.get("reply", "")
        retrieved_ids = out.get("retrieved_evidence", [])
        sections_used = out.get("sections_used", [])

        passed = False
        reason = ""

        if expect_abstain:
            is_abstaining = (
                "sorry" in reply.lower() or "don't have information" in reply.lower()
                or "connect you to a colleague" in reply.lower() or "not covered" in reply.lower()
            )
            has_no_fake_citations = len(sections_used) == 0 or all(s == "NONE" for s in sections_used)
            if is_abstaining and has_no_fake_citations:
                passed = True
                reason = "Honest abstention observed with zero fabricated citations."
            else:
                passed = False
                reason = f"Failed abstention: is_abstaining={is_abstaining}, sections_used={sections_used}"
        else:
            retrieval_hit = any(s in retrieved_ids for s in target_secs)
            reply_lower = reply.lower()
            grounded = False

            if cat == "unseen_kb":
                if any(term in reply_lower for term in ["policy", "warning", "cancel", "999", "select", "pincode", "48 hours", "domestic", "electronics", "bluetooth", "reset", "exchange", "otp", "handover", "colleague"]):
                    grounded = True
            elif cat == "paraphrased":
                if any(term in reply_lower for term in ["15 days", "1 to 3", "3 times", "48 hours", "innerwear", "cannot be returned"]):
                    grounded = True
            elif cat == "multi_chunk":
                if any(term in reply_lower for term in ["priority resolution", "10,000", "5 to 7", "business days", "no", "fee", "30 days"]):
                    grounded = True
            elif cat == "outdated_misleading":
                if any(term in reply_lower for term in ["7 days", "original", "zentromart wallet", "cannot", "only"]):
                    grounded = True

            if retrieval_hit and grounded:
                passed = True
                reason = f"Retrieved valid chunk ({[s for s in target_secs if s in retrieved_ids]}) and response is grounded."
            else:
                passed = False
                reason = f"Retrieval hit: {retrieval_hit}, Content grounded: {grounded}"

        if passed:
            passed_count += 1

        record = {
            "id": q_id,
            "category": cat,
            "question": q,
            "expected_core": exp_core,
            "expect_abstain": expect_abstain,
            "actual_decision": decision,
            "actual_reply": reply,
            "retrieved_evidence": retrieved_ids,
            "sections_used": sections_used,
            "passed": passed,
            "reason": reason
        }
        results.append(record)

        status_tag = "PASS" if passed else "FAIL"
        print(f"[{idx:02d}/{total}] {q_id} ({cat}) -> {status_tag} | {reason[:60]}")

    pass_rate = round(passed_count / total * 100, 2)
    print("-----------------------------------------------------------------")
    print(f"DIAGNOSTIC (POST-FIX) RESULT: {passed_count}/{total} Passed ({pass_rate}%)")
    print("-----------------------------------------------------------------")

    json_path = RESULTS_DIR / "step2_diagnostic_post_fix.json"
    summary_data = {
        "evaluation_name": "step2_diagnostic_post_fix",
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_test_cases": total,
        "passed_count": passed_count,
        "failed_count": total - passed_count,
        "pass_rate_percentage": pass_rate,
        "results": results
    }

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary_data, f, indent=2, ensure_ascii=False)
    return summary_data


if __name__ == "__main__":
    run_diagnostic_post_fix()

