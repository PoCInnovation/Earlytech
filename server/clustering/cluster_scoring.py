from typing import Dict, List

def compute_entity_similarity(a: Dict, b: Dict) -> float:
    score = 0.0

    if a["subject"] and a["subject"] == b["subject"]:
        score += 1.0

    if a["event"] and a["event"] == b["event"]:
        score += 0.5

    orgs_a = set(a.get("orgs", []))
    orgs_b = set(b.get("orgs", []))

    if orgs_a and orgs_b:
        score += 0.2 * len(orgs_a & orgs_b)

    return score

def compute_final_score(
    semantic_score: float,
    entity_score: float,
    w_sem: float = 0.6,
    w_ent: float = 0.4,
) -> float:
    return w_sem * semantic_score + w_ent * entity_score
