import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
RESULTS_DIR = Path("results")

def analyze_step2():
    path = RESULTS_DIR / "results_step2.json"
    if not path.exists():
        print(f"File {path} does not exist")
        return
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"=== STEP 2 SUMMARY ===")
    print(f"Total Questions: {data.get('total_questions')}")
    print(f"Decision Accuracy: {data.get('decision_accuracy') * 100:.2f}%")
    print(f"Mean Fact Score: {data.get('mean_fact_score') * 100:.2f}%")
    print(f"Trap Safety Rate: {data.get('trap_safety_rate') * 100:.2f}%")
    print(f"Hit@1: {data.get('hit_at_1') * 100:.2f}%")
    print(f"Hit@3: {data.get('hit_at_3') * 100:.2f}%")
    print(f"Hit@5: {data.get('hit_at_5') * 100:.2f}%")
    print(f"MRR: {data.get('mrr'):.4f}")
    print(f"Hard Negative Avoidance Rate: {data.get('hard_negative_avoidance_rate') * 100:.2f}%")
    
    results = data.get("results", [])
    print(f"\n--- Questions with Fact Score < 1.0 or Decision Incorrect ---")
    imperfect = []
    for r in results:
        fact = r.get("fact_score", 0.0)
        dec_ok = r.get("decision_correct", False)
        if fact < 1.0 or not dec_ok:
            imperfect.append(r)
            print(f"ID: {r.get('id')} | DecOK: {dec_ok} (Act: {r.get('actual_decision')} vs Exp: {r.get('expected_decision')}) | Fact Score: {fact:.2f}")
            print(f"  Question: {r.get('question')}")
            print(f"  Missing Facts: {r.get('missing_facts')}")
            print(f"  Reply snippet: {r.get('reply', '')[:120]}...")
            print(f"  Retrieved: {r.get('retrieved_evidence')[:4]}")
            print()
            
    print(f"\nTotal imperfect: {len(imperfect)} / {len(results)}")
    return imperfect

def analyze_step3():
    path = RESULTS_DIR / "results_step3.json"
    if not path.exists():
        print(f"File {path} does not exist")
        return []
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    print(f"\n=== STEP 3 SUMMARY ===")
    print(f"Total Conversations: {data.get('total_conversations')}")
    print(f"Total Turns: {data.get('total_turns')}")
    print(f"Completed Conversations: {data.get('completed_conversations')} / {data.get('total_conversations')} ({data.get('conversation_pass_rate') * 100:.2f}%)")
    print(f"Turn Decision Accuracy: {data.get('turn_decision_accuracy') * 100:.2f}%")
    print(f"Tool Call Accuracy: {data.get('tool_call_accuracy') * 100:.2f}%")
    print(f"Mean Turn Fact Score: {data.get('mean_turn_fact_score') * 100:.2f}%")
    print(f"Turn Trap Safety Rate: {data.get('turn_trap_safety_rate') * 100:.2f}%")
    
    convs = data.get("conversations", [])
    imperfect = []
    for c in convs:
        for t in c.get("turns", []):
            dec_ok = t.get("decision_correct", False)
            tools_ok = t.get("tools_correct", False)
            fact = t.get("fact_score", 0.0)
            if not dec_ok or not tools_ok or fact < 1.0:
                imperfect.append((c.get("conversation_id"), t))
                print(f"Conv: {c.get('conversation_id')} | Turn {t.get('turn')} | DecOK: {dec_ok} | ToolsOK: {tools_ok} | Fact: {fact:.2f}")
                print(f"  Cust: {t.get('customer_message')}")
                print(f"  Missing: {t.get('missing_facts')}")
                print(f"  Reply: {t.get('reply')[:120]}...")
                print()
                
    print(f"Total imperfect turns: {len(imperfect)}")
    return imperfect

if __name__ == "__main__":
    analyze_step2()
    analyze_step3()

