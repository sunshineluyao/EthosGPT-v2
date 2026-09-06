from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments/gpt55_gpt56_64country/results"


def test_global_tvd_is_the_only_corrected_global_improvement():
    table = pd.read_csv(RESULTS / "metric_comparisons.csv").set_index("metric")
    assert table.loc["TVD", "estimate"] < 0
    assert table.loc["TVD", "ci_high_bca"] < 0
    assert table.loc["TVD", "holm_p_five_metrics"] < .001
    assert set(table.index[table["holm_p_five_metrics"] <= .05]) == {"TVD"}


def test_geometry_changes_remain_uncertain_under_country_resampling():
    table = pd.read_csv(RESULTS / "metric_comparisons.csv").set_index("metric")
    for metric in ("CRG", "VDR", "CSR"):
        assert table.loc[metric, "ci_low_bca"] <= 0 <= table.loc[metric, "ci_high_bca"]


def test_domain_results_are_model_version_specific():
    table = pd.read_csv(RESULTS / "domain_comparisons.csv")
    w1 = table[(table.metric == "W1") & (table.holm_p_within_metric <= .05)]
    tvd = table[(table.metric == "TVD") & (table.holm_p_within_metric <= .05)]
    assert set(w1.domain) == {"Distribution", "Market"}
    assert set(tvd.domain) == {"Distribution", "Market", "Science"}
    assert (w1.delta_56_minus_55 < 0).all()
    assert (tvd.delta_56_minus_55 < 0).all()
