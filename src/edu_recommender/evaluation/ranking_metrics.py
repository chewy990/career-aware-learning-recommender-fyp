"""Own evaluation ranking metrics responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import math


def precision_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Return relevant recommendations divided by K, treating an empty relevant set as zero."""

    if k <= 0:
        return 0.0
    hits = sum(1 for resource_id in ranked_ids[:k] if resource_id in relevant_ids)
    return hits / k

def recall_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Return retrieved relevant items divided by all relevant items, or zero when none exist."""

    if not relevant_ids:
        return 0.0
    hits = sum(1 for resource_id in ranked_ids[:k] if resource_id in relevant_ids)
    return hits / len(relevant_ids)

def ndcg_at_k(ranked_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Return binary or graded-gain DCG normalised at the same cutoff."""

    if k <= 0:
        return 0.0
    grades = getattr(relevant_ids, "grades", {})
    if grades:
        gains = {
            resource_id: (2 ** int(grade)) - 1
            for resource_id, grade in grades.items()
        }
        ranked_gains = [gains.get(resource_id, 0) for resource_id in ranked_ids[:k]]
        ideal_gains = sorted(gains.values(), reverse=True)[:k]
    else:
        ranked_gains = [
            1 if resource_id in relevant_ids else 0
            for resource_id in ranked_ids[:k]
        ]
        ideal_gains = [1] * min(len(relevant_ids), k)
    dcg = sum(
        gain / math.log2(index + 1)
        for index, gain in enumerate(ranked_gains, start=1)
    )
    ideal_dcg = sum(
        gain / math.log2(index + 1)
        for index, gain in enumerate(ideal_gains, start=1)
    )
    if ideal_dcg == 0:
        return 0.0
    return dcg / ideal_dcg
