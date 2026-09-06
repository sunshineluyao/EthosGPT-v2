import numpy as np
import pytest

from experiments.gpt55_gpt56_64country.score_wave1 import support_probabilities


def test_incomplete_probability_support_fails_closed():
    with pytest.raises(ValueError, match="support differs"):
        support_probabilities({"1": 0.5, "2": 0.5}, 1, 3)


def test_probability_mass_violation_fails_closed():
    with pytest.raises(ValueError, match="sum to one"):
        support_probabilities({"1": 0.7, "2": 0.7}, 1, 2)


def test_nonfinite_probability_fails_closed():
    with pytest.raises(ValueError, match="finite"):
        support_probabilities({"1": np.nan, "2": 1.0}, 1, 2)
