from typing import Dict, List

def compute_entity_similarity(a: Dict, b: Dict) -> float:
    """
    Compute entity similarity between two articles with primary/secondary importance weighting.
    
    Args:
        a: Entity dict with primary_subject, secondary_subject, primary_orgs, secondary_orgs, primary_event, secondary_event
        b: Entity dict with same structure
        
    Returns:
        Similarity score (0.0 to 1.0+)
    """
    score = 0.0

    # Primary subject match (highest weight)
    if a.get("primary_subject") and a["primary_subject"] == b.get("primary_subject"):
        score += 1.0
    # Secondary subject match with lower weight
    elif a.get("secondary_subject") and a["secondary_subject"] == b.get("secondary_subject"):
        score += 0.3
    # Cross-match (primary vs secondary)
    elif (a.get("primary_subject") and a["primary_subject"] == b.get("secondary_subject")) or \
         (a.get("secondary_subject") and a["secondary_subject"] == b.get("primary_subject")):
        score += 0.2

    # Primary event match (high weight)
    if a.get("primary_event") and a["primary_event"] == b.get("primary_event"):
        score += 0.5
    # Secondary event match (lower weight)
    elif a.get("secondary_event") and a["secondary_event"] == b.get("secondary_event"):
        score += 0.2
    # Cross-match
    elif (a.get("primary_event") and a["primary_event"] == b.get("secondary_event")) or \
         (a.get("secondary_event") and a["secondary_event"] == b.get("primary_event")):
        score += 0.15

    # Organization matching with primary/secondary distinction
    primary_orgs_a = set(a.get("primary_orgs", []))
    primary_orgs_b = set(b.get("primary_orgs", []))
    secondary_orgs_a = set(a.get("secondary_orgs", []))
    secondary_orgs_b = set(b.get("secondary_orgs", []))

    # Primary org matches (higher weight)
    if primary_orgs_a and primary_orgs_b:
        score += 0.3 * len(primary_orgs_a & primary_orgs_b)

    # Secondary org matches (lower weight)
    if secondary_orgs_a and secondary_orgs_b:
        score += 0.1 * len(secondary_orgs_a & secondary_orgs_b)

    # Cross-org matches (primary <-> secondary)
    if primary_orgs_a and secondary_orgs_b:
        score += 0.1 * len(primary_orgs_a & secondary_orgs_b)
    if secondary_orgs_a and primary_orgs_b:
        score += 0.1 * len(secondary_orgs_a & primary_orgs_b)

    return score

def compute_final_score(
    semantic_score: float,
    entity_score: float,
    cross_score: float = 0.5,
    w_sem: float = 0.3,
    w_ent: float = 0.4,
    w_cross: float = 0.3,
) -> float:
    """
    Compute final clustering score combining multiple signals.
    
    Args:
        semantic_score: Embedding-based similarity (0.0-1.0)
        entity_score: Entity matching score (0.0-1.0+)
        cross_score: Cross-encoder score (0.0-1.0)
        w_sem: Weight for semantic similarity
        w_ent: Weight for entity similarity
        w_cross: Weight for cross-encoder score
        
    Returns:
        Final combined score
    """
    # Normalize entity score to [0, 1] range
    normalized_entity = min(entity_score / 2.0, 1.0)
    
    return (w_sem * semantic_score + 
            w_ent * normalized_entity + 
            w_cross * cross_score)
