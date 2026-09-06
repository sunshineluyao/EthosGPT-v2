from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "experiments/gpt55_gpt56_64country/results"


def test_joint_item_family_preserves_only_three_corrected_improvements():
    table = pd.read_csv(RESULTS / "joint_item_inference.csv")
    significant = table[table["joint_max_t_p_fwer"] <= .05]
    observed = set(zip(significant["metric"], significant["question_id"]))
    assert observed == {("W1", "Q108"), ("TVD", "Q106"), ("TVD", "Q108")}
    assert (significant["delta_56_minus_55"] < 0).all()


def test_composition_identity_and_five_run_residual():
    cells = pd.read_csv(RESULTS / "composition_cell_curves.csv")
    assert cells["finite_population_identity_error"].abs().max() < 1e-12
    summary = pd.read_csv(RESULTS / "composition_summary.csv")
    shares = summary[
        summary["component"] == "share_of_individual_error_removed_by_five_generation_average"
    ]
    assert shares["estimate"].between(.005, .03).all()
    residuals = summary[
        (summary["component"] == "five_run_residual")
        & summary["comparison"].isin(["GPT-5.5", "GPT-5.6 Sol"])
    ]
    assert (residuals["ci_low_bca"] > 0).all()


def test_creative_destruction_sensitivity_is_not_uniform():
    margins = pd.read_csv(RESULTS / "economic_margin_results.csv").set_index("margin")
    distribution = margins.loc["Distribution and adjustment"]
    coordination = margins.loc["Coordination and legitimacy"]
    assert distribution["delta_ci_high_bca"] < 0
    assert coordination["delta_ci_low_bca"] <= 0 <= coordination["delta_ci_high_bca"]
    surface = pd.read_csv(RESULTS / "economic_weight_surface_summary.csv").iloc[0]
    assert .5 < surface["fraction_ci_favors_gpt56"] < 1
    assert surface["fraction_uncertain"] > 0


def test_primary_tvd_survives_spatial_robustness():
    sem = pd.read_csv(RESULTS / "spatial_error_models.csv")
    global_tvd = sem[(sem["metric"] == "TVD") & (sem["scope"] == "All six anchors")]
    assert set(global_tvd["knn_k"]) == {4, 6, 8}
    assert (global_tvd["ci_high_95"] < 0).all()
    assert (global_tvd["holm_p_fourteen_scopes"] < .001).all()

    hac = pd.read_csv(RESULTS / "spatial_hac_contrasts.csv")
    global_hac = hac[(hac["metric"] == "TVD") & (hac["scope"] == "All six anchors")]
    assert set(global_hac["cutoff_km"]) == {1000, 2000, 3000, 5000}
    assert (global_hac["ci_high_95"] < 0).all()


def test_tvd_direction_is_stable_to_region_and_cell_count_influence():
    region = pd.read_csv(RESULTS / "leave_one_region_out.csv")
    assert (region[region["metric"] == "TVD"]["estimate"] < 0).all()
    cell_count = pd.read_csv(RESULTS / "human_cell_count_quartile_sensitivity.csv")
    assert (cell_count[cell_count["metric"] == "TVD"]["estimate"] < 0).all()
