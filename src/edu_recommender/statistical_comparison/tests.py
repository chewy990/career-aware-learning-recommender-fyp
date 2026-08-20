"""Own statistical comparison tests responsibilities.

This module is calculation-focused and must not absorb unrelated phase work.

"""

from __future__ import annotations

import itertools


def exact_paired_permutation_test(
    differences: list[float],
) -> float:
    """Compute an exact two-sided paired sign-permutation p-value."""

    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return 1.0
    observed = abs(sum(nonzero))
    extreme = 0
    total = 2 ** len(nonzero)
    for signs in itertools.product((-1, 1), repeat=len(nonzero)):
        statistic = abs(
            sum(sign * value for sign, value in zip(signs, nonzero))
        )
        if statistic >= observed - 1e-12:
            extreme += 1
    return extreme / total

def exact_wilcoxon_signed_rank_test(
    differences: list[float],
) -> tuple[float, float]:
    """Compute an exact two-sided Wilcoxon signed-rank p-value after removing zeros."""

    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return 0.0, 1.0
    ranks = _average_ranks([abs(value) for value in nonzero])
    observed_w_plus = sum(
        rank
        for rank, value in zip(ranks, nonzero)
        if value > 0
    )
    total_rank = sum(ranks)
    observed_t = min(
        observed_w_plus,
        total_rank - observed_w_plus,
    )
    extreme = 0
    total = 2 ** len(nonzero)
    for positive_flags in itertools.product(
        (False, True),
        repeat=len(nonzero),
    ):
        w_plus = sum(
            rank
            for rank, is_positive in zip(ranks, positive_flags)
            if is_positive
        )
        statistic = min(w_plus, total_rank - w_plus)
        if statistic <= observed_t + 1e-12:
            extreme += 1
    return observed_w_plus, extreme / total

def holm_adjust(p_values: list[float]) -> list[float]:
    """Apply Holm's step-down family-wise error correction to named p-values."""

    if not p_values:
        return []
    order = sorted(range(len(p_values)), key=lambda index: p_values[index])
    adjusted = [0.0] * len(p_values)
    running_max = 0.0
    count = len(p_values)
    for rank, original_index in enumerate(order):
        candidate = min(
            1.0,
            (count - rank) * p_values[original_index],
        )
        running_max = max(running_max, candidate)
        adjusted[original_index] = running_max
    return adjusted

def effect_magnitude(effect: float) -> str:
    """Map an absolute paired effect to its documented qualitative magnitude."""

    absolute = abs(effect)
    if absolute < 0.2:
        return "negligible"
    if absolute < 0.5:
        return "small"
    if absolute < 0.8:
        return "medium"
    return "large"

def _average_ranks(values: list[float]) -> list[float]:
    indexed = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    position = 0
    while position < len(indexed):
        end = position + 1
        while (
            end < len(indexed)
            and indexed[end][1] == indexed[position][1]
        ):
            end += 1
        average_rank = (
            (position + 1) + end
        ) / 2
        for index in range(position, end):
            ranks[indexed[index][0]] = average_rank
        position = end
    return ranks
