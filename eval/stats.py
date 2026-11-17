"""Small-sample statistics for the A vs B comparison (standard library only).

- wilson(k, n): 95% Wilson score interval for a proportion. With 9-20 restricted questions a
  plain percentage hides how uncertain the rate is; the interval makes that visible.
- mcnemar_exact(b, c): exact two-sided McNemar test for paired yes/no outcomes. A and B answer the
  same questions, so we compare them question by question: b = questions where only A leaked,
  c = questions where only B leaked.
"""
import math


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def mcnemar_exact(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def fmt_rate(k, n):
    """'22.2% [6.3, 54.7]' (percentage with 95% Wilson interval)."""
    if n == 0:
        return "n/a"
    lo, hi = wilson(k, n)
    return f"{100 * k / n:.1f}% [{100 * lo:.1f}, {100 * hi:.1f}]"
