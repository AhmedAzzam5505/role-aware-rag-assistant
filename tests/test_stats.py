"""Checks the statistics helpers against values computed by hand / published tables."""
import pytest

from eval.stats import fmt_rate, mcnemar_exact, wilson


def test_wilson_matches_reference_values():
    lo, hi = wilson(2, 9)  # pilot leak rate, Version A mis-tagged
    assert lo == pytest.approx(0.0632, abs=1e-3) and hi == pytest.approx(0.5474, abs=1e-3)
    lo, hi = wilson(0, 9)
    assert lo == 0.0 and hi == pytest.approx(0.2991, abs=1e-3)


def test_mcnemar_exact():
    assert mcnemar_exact(0, 0) == 1.0
    assert mcnemar_exact(2, 0) == pytest.approx(0.5)       # 2 discordant pairs can never be significant
    assert mcnemar_exact(9, 0) == pytest.approx(2 / 512)   # 0.0039
    assert mcnemar_exact(3, 3) == 1.0


def test_fmt_rate():
    assert fmt_rate(2, 9) == "22.2% [6.3, 54.7]"
    assert fmt_rate(0, 0) == "n/a"
