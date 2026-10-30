"""Evaluation script for Step 3: Multi-turn Agent across all 23 conversations (96 turns)."""
import csv
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.config import PRACTICE_DIR, RESULTS_DIR
from src.step3_agent.agent import ZentroMartAgent
from eval.metrics import evaluate_decision, evaluate_must_include, evaluate_must_not_include


def normalize_tool_call_for_eval(call_str: str) -> str:
    """Normalize tool call string for strict parameter comparison."""
    if not call_str:
        return ""
    # Remove spaces around '=' and ','
    cleaned = call_str.replace(" ", "").strip()
    return cleaned


def compare_tool_calls(actual_calls: List[str], expected_calls_str: str) -> bool:
    """Compare executed tool calls against expected tool call specification."""
    if not expected_calls_str or not expected_calls_str.strip():
        return len(actual_calls) == 0

    expected_list = [normalize_tool_call_for_eval(c) for c in expected_calls_str.split(" ; ") if c.strip()]
    actual_list = [normalize_tool_call_for_eval(c) for c in actual_calls if c.strip()]

    # Check if all expected calls are present
    for exp in expected_list:
        if exp not in actual_list:
            return False
    return True


def run_eval_step3(output_file: Optional[Path] = None) -> Dict[str, Any]:
    """Run Step 3 multi-turn evaluation on all 23 conversations (96 turns)."""
    conv_file = PRACTICE_DIR / "conversations.csv"
    with open(conv_file, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Group by conversation_id and sort by turn
    conversations = defaultdict(list)
    for r in rows:
        conversations[r["conversation_id"]].append(r)

    agent = ZentroMartAgent()
    total_turns = len(rows)
    turn_decision_correct = 0
    turn_tool_correct = 0
    turn_fact_score = 0.0
    turn_trap_clean = 0
    completed_conversations = 0

    results = []

    print(f"Starting Step 3 Multi-turn Agent Evaluation on {len(conversations)} conversations ({total_turns} turns)...")
    start_time = time.time()

    for cid in sorted(conversations.keys()):
        turn_rows = sorted(conversations[cid], key=lambda x: int(x["turn"]))
        agent.reset_session(cid)
        conv_turns_evaluated = []
        all_conv_turns_ok = True

        for r in turn_rows:
            turn_no = int(r["turn"])
            msg = r["customer_message"]
            lang = r["language"]
            scen = r["scenario"]
            oid = r["order_id"]
            exp_dec = r["expected_decision"]
            exp_tools = r.get("expected_tool_calls", "")
            must_inc = r.get("must_include", "")
            must_not_inc = r.get("must_not_include", "")

            out = agent.process_turn(
                conversation_id=cid,
                customer_message=msg,
                turn_number=turn_no,
                language=lang
            )

            dec_ok = evaluate_decision(out["decision"], exp_dec)
            tools_ok = compare_tool_calls(out["tool_calls"], exp_tools)
            fact_score, missing = evaluate_must_include(out["reply"], must_inc)
            trap_clean, violations = evaluate_must_not_include(out["reply"], must_not_inc)

            if dec_ok:
                turn_decision_correct += 1
            if tools_ok:
                turn_tool_correct += 1
            turn_fact_score += fact_score
            if trap_clean:
                turn_trap_clean += 1

            if not (dec_ok and tools_ok and fact_score >= 0.5):
                all_conv_turns_ok = False

            turn_rec = {
                "turn": turn_no,
                "customer_message": msg,
                "expected_decision": exp_dec,
                "actual_decision": out["decision"],
                "decision_correct": dec_ok,
                "expected_tool_calls": exp_tools,
                "actual_tool_calls": out["tool_calls"],
                "tools_correct": tools_ok,
                "reply": out["reply"],
                "fact_score": fact_score,
                "missing_facts": missing,
                "trap_clean": trap_clean,
                "trap_violations": violations,
                "session_state": out.get("session_state")
            }
            conv_turns_evaluated.append(turn_rec)

        if all_conv_turns_ok:
            completed_conversations += 1

        results.append({
            "conversation_id": cid,
            "scenario": turn_rows[0]["scenario"],
            "turns_count": len(turn_rows),
            "all_turns_passed": all_conv_turns_ok,
            "turns": conv_turns_evaluated
        })
        print(f"[{cid}] ({turn_rows[0]['scenario']}) - {len(turn_rows)} turns | Conv Passed: {all_conv_turns_ok}")

    elapsed = round(time.time() - start_time, 2)
    summary = {
        "step": "step3_agent",
        "total_conversations": len(conversations),
        "total_turns": total_turns,
        "completed_conversations": completed_conversations,
        "conversation_pass_rate": round(completed_conversations / len(conversations), 4),
        "turn_decision_accuracy": round(turn_decision_correct / total_turns, 4),
        "tool_call_accuracy": round(turn_tool_correct / total_turns, 4),
        "mean_turn_fact_score": round(turn_fact_score / total_turns, 4),
        "turn_trap_safety_rate": round(turn_trap_clean / total_turns, 4),
        "elapsed_seconds": elapsed,
        "conversations": results
    }

    dest = output_file or (RESULTS_DIR / "results_step3.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print("\n=== STEP 3 MULTI-TURN AGENT RESULTS ===")
    print(f"Conversations Passed:    {summary['completed_conversations']}/{summary['total_conversations']} ({summary['conversation_pass_rate'] * 100:.1f}%)")
    print(f"Turn Decision Accuracy:  {summary['turn_decision_accuracy'] * 100:.1f}%")
    print(f"Tool Invocation Accuracy:{summary['tool_call_accuracy'] * 100:.1f}%")
    print(f"Mean Fact Score:         {summary['mean_turn_fact_score'] * 100:.1f}%")
    print(f"Trap Safety Rate:        {summary['turn_trap_safety_rate'] * 100:.1f}%")
    print(f"Saved results to:        {dest}")
    return summary


if __name__ == "__main__":
    run_eval_step3()
