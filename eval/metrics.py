"""Scoring metrics for Decisions, Facts (must_include/must_not_include), and Retrieval Quality."""
import re
from typing import List, Dict, Any, Tuple, Optional


def normalize_text_for_eval(text: str) -> str:
    """Normalize text for evaluation: lowercase, collapse whitespace, standardize punctuation."""
    t = (text or "").lower()
    t = re.sub(r"\s+", " ", t).strip()
    return t


def check_fact_present(reply: str, fact_pattern: str) -> bool:
    """Check if a required fact (with ' / ' separated alternatives) is present in reply."""
    reply_norm = normalize_text_for_eval(reply)
    alternatives = [a.strip() for a in fact_pattern.split(" / ") if a.strip()]
    if not alternatives:
        return True

    for alt in alternatives:
        alt_norm = normalize_text_for_eval(alt)
        # Check direct substring
        if alt_norm in reply_norm:
            return True

        # Check numeric equivalence e.g. 49 vs ₹49 or 2 vs two
        cleaned_alt = re.sub(r"[^\w\s]", "", alt_norm)
        cleaned_reply = re.sub(r"[^\w\s]", "", reply_norm)
        if cleaned_alt and cleaned_alt in cleaned_reply:
            return True

    return False


def evaluate_must_include(reply: str, must_include_str: str) -> Tuple[float, List[str]]:
    """Evaluate all required facts separated by ' ; '. Returns (score_0_to_1, missing_facts)."""
    if not must_include_str or not must_include_str.strip():
        return 1.0, []

    facts = [f.strip() for f in must_include_str.split(" ; ") if f.strip()]
    if not facts:
        return 1.0, []

    missing = []
    for fact in facts:
        if not check_fact_present(reply, fact):
            missing.append(fact)

    score = (len(facts) - len(missing)) / len(facts)
    return round(score, 3), missing


def evaluate_must_not_include(reply: str, must_not_include_str: str) -> Tuple[bool, List[str]]:
    """Check for forbidden claims separated by ' ; '. Returns (passed_boolean, found_violations)."""
    if not must_not_include_str or not must_not_include_str.strip():
        return True, []

    forbidden_list = [f.strip() for f in must_not_include_str.split(" ; ") if f.strip()]
    violations = []
    reply_norm = normalize_text_for_eval(reply)

    for item in forbidden_list:
        # Check alternatives if any
        sub_items = [s.strip() for s in item.split(" / ") if s.strip()]
        for s in sub_items:
            s_norm = normalize_text_for_eval(s)
            if s_norm and s_norm in reply_norm:
                violations.append(s)
                break

    return (len(violations) == 0), violations


def evaluate_decision(actual: str, expected: str, acceptable: Optional[str] = None) -> bool:
    """Check if actual decision matches expected or acceptable decisions."""
    act = (actual or "").lower().strip()
    exp = (expected or "").lower().strip()
    if act == exp:
        return True

    if acceptable:
        acc_list = [a.strip().lower() for a in acceptable.split(" ; ") if a.strip()]
        if act in acc_list:
            return True

    return False


def evaluate_retrieval(retrieved_ids: List[str], gold_evidence_str: str, hard_negatives_str: Optional[str] = None) -> Dict[str, Any]:
    """Compute Hit@1, Hit@3, Hit@5, MRR, and trap avoidance against gold evidence."""
    golds = [g.strip() for g in (gold_evidence_str or "").split(" ; ") if g.strip()]
    if not golds:
        return {
            "hit_at_1": 1.0,
            "hit_at_3": 1.0,
            "hit_at_5": 1.0,
            "mrr": 1.0,
            "avoided_hard_negatives": True,
            "gold_evidence": []
        }

    retrieved_clean = [r.strip() for r in retrieved_ids]

    # Hit@K
    hit_1 = any(r in golds for r in retrieved_clean[:1])
    hit_3 = any(r in golds for r in retrieved_clean[:3])
    hit_5 = any(r in golds for r in retrieved_clean[:5])

    # MRR (Mean Reciprocal Rank)
    first_rank = 0
    for idx, r in enumerate(retrieved_clean, 1):
        if r in golds:
            first_rank = idx
            break
    rr = 1.0 / first_rank if first_rank > 0 else 0.0

    # Hard negatives check
    avoided_hn = True
    if hard_negatives_str:
        hns = [h.strip() for h in hard_negatives_str.split(" ; ") if h.strip()]
        for hn in hns:
            if hn in retrieved_clean[:3]:  # trapped in top-3
                avoided_hn = False
                break

    return {
        "hit_at_1": 1.0 if hit_1 else 0.0,
        "hit_at_3": 1.0 if hit_3 else 0.0,
        "hit_at_5": 1.0 if hit_5 else 0.0,
        "mrr": round(rr, 3),
        "avoided_hard_negatives": avoided_hn,
        "gold_evidence": golds
    }
