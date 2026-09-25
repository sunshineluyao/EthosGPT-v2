#!/usr/bin/env python3
"""Fail-closed checks for the 64-country data and code release."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import re

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"
RESULTS = EXP / "results"
FIGS = ROOT / "results/figures"
SOURCES = ROOT / "assets/figure_sources"
OUTPUT_HASHES = {
    "gpt-5.5_scores.jsonl": "cb35dea83bdc08e50d8d79d2760acb3b79e130c5c22e69c80bd7c5568d8ce729",
    "gpt-5.6-sol_scores.jsonl": "3c94ddebb870ded526ac99780c845cd5788c333e5fd34444c1cd0a5cae4d6a28",
}
EXPECTED_PROMPT_SET = "d8673796bd2bdb9e7259d1548287e988d010942c808aa8d5f555735ec4a0cc73"
EXPECTED_SOURCE_UPLOAD = "6d2631c6a10c1436aceaa6c441edc09f009c6fed637baa5ab5a8604c14c627a8"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def close(actual: float, expected: float, tolerance: float = 5e-7) -> None:
    assert abs(float(actual) - expected) <= tolerance, (actual, expected)


def main() -> None:
    required = [
        "metric_estimates.csv",
        "metric_comparisons.csv",
        "domain_comparisons.csv",
        "signed_bias_inference.csv",
        "country_question_scores.csv",
        "country_bootstrap_draws.parquet",
        "conditional_uncertainty_contrasts.csv",
        "conditional_uncertainty_draws.parquet",
        "five_anchor_metric_comparisons.csv",
        "q121_prompt_deviation_sensitivity.csv",
        "wording_omission_sensitivity.csv",
        "eight_region_sensitivity.csv",
        "leave_one_country_out.csv",
        "bootstrap_convergence.csv",
        "run_stability.csv",
        "spatial_diagnostics.csv",
        "spatial_error_models.csv",
        "spatial_hac_contrasts.csv",
        "token_usage.csv",
        "joint_item_inference.csv",
        "composition_cell_curves.csv",
        "composition_estimates.csv",
        "composition_contrasts.csv",
        "composition_summary.csv",
        "economic_margin_results.csv",
        "economic_scenarios.csv",
        "economic_weight_surface.csv",
        "economic_weight_surface_summary.csv",
        "leave_one_region_out.csv",
        "human_cell_count_quartile_sensitivity.csv",
    ]
    missing = [name for name in required if not (RESULTS / name).exists()]
    assert not missing, f"missing analysis outputs: {missing}"

    output_rows: dict[str, list[dict]] = {}
    for name, expected_hash in OUTPUT_HASHES.items():
        path = EXP / "outputs" / name
        assert sha256(path) == expected_hash, f"frozen output drift: {name}"
        rows = read_jsonl(path)
        assert len(rows) == 1_920
        assert len({row["record_key"] for row in rows}) == 1_920
        assert {row["generation"] for row in rows} == {1, 2, 3, 4, 5}
        assert len({row["country"] for row in rows}) == 64
        assert {row["question_id"] for row in rows} == {"Q48", "Q57", "Q106", "Q108", "Q121", "Q159"}
        assert all(row["status"] == "valid" and row["http_status"] == 200 for row in rows)
        assert all(abs(float(row["probability_sum"]) - 1) < 1e-9 for row in rows)
        output_rows[name] = rows

    assert {row["requested_model_id"] for row in output_rows["gpt-5.5_scores.jsonl"]} == {"gpt-5.5-2026-04-23"}
    assert {row["requested_model_id"] for row in output_rows["gpt-5.6-sol_scores.jsonl"]} == {"gpt-5.6-sol"}
    attempt_rows = read_jsonl(EXP / "outputs/attempt_ledger.jsonl")
    assert len(attempt_rows) == 3_850
    attempt_counts = Counter((row["model_tag"], int(row["attempt"])) for row in attempt_rows)
    assert attempt_counts == Counter({("gpt55", 0): 1_920, ("gpt56", 0): 1_920, ("gpt55", 1): 7, ("gpt56", 1): 3})
    assert (EXP / "outputs/failed_records.jsonl").read_bytes() == b""
    paired = {
        (row["country"], row["question_id"], row["generation"])
        for rows in output_rows.values() for row in rows
    }
    assert len(paired) == 1_920

    prompt_ledger = pd.read_csv(EXP / "inputs/prompt_ledger.csv")
    assert len(prompt_ledger) == 384 and prompt_ledger["prompt_sha256"].nunique() == 384
    prompt_hashes = set(prompt_ledger["prompt_sha256"])
    for rows in output_rows.values():
        assert {row["prompt_sha256"] for row in rows} == prompt_hashes
    manifest = json.loads((EXP / "manifests/analysis_manifest.json").read_text())
    assert manifest["prompt_set_sha256"] == EXPECTED_PROMPT_SET
    assert manifest["countries"] == 64
    assert manifest["country_bootstrap_draws"] == 20_000
    assert manifest["randomization_permutations"] == 19_999
    assert manifest["spatial_permutations"] == 9_999
    assert (EXP / "manifests/source_upload.sha256").read_text(encoding="utf-8").split()[0] == EXPECTED_SOURCE_UPLOAD

    coverage = pd.read_csv(RESULTS / "country_coverage_and_human_cell_counts.csv")
    assert len(coverage) == 64 and coverage["six_anchor_complete"].all()
    assert "China" in set(coverage["country"])
    assert "Venezuela" not in set(coverage["country"])
    assert set(coverage["cultural_region"]) == {
        "African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
        "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia",
    }

    estimates = pd.read_csv(RESULTS / "metric_estimates.csv").set_index(["model", "metric"])
    assert len(estimates) == 10 and set(estimates["countries"]) == {64}
    close(estimates.loc[("GPT-5.5", "W1"), "estimate"], 0.128434)
    close(estimates.loc[("GPT-5.6 Sol", "TVD"), "estimate"], 0.304319)
    close(estimates.loc[("GPT-5.5", "VDR"), "estimate"], 0.587314)
    close(estimates.loc[("GPT-5.6 Sol", "CSR"), "estimate"], 0.287817)

    contrasts = pd.read_csv(RESULTS / "metric_comparisons.csv").set_index("metric")
    close(contrasts.loc["TVD", "estimate"], -0.008046)
    assert contrasts.loc["TVD", "ci_high_bca"] < 0
    assert contrasts.loc["TVD", "holm_p_five_metrics"] < .001
    assert set(contrasts.index[contrasts["holm_p_five_metrics"] <= .05]) == {"TVD"}
    for metric in ("W1", "CRG", "VDR", "CSR"):
        assert contrasts.loc[metric, "ci_low_bca"] <= 0 <= contrasts.loc[metric, "ci_high_bca"]

    domains = pd.read_csv(RESULTS / "domain_comparisons.csv")
    significant_w1 = set(domains[(domains.metric == "W1") & (domains.holm_p_within_metric <= .05)]["domain"])
    significant_tvd = set(domains[(domains.metric == "TVD") & (domains.holm_p_within_metric <= .05)]["domain"])
    assert significant_w1 == {"Distribution", "Market"}
    assert significant_tvd == {"Distribution", "Market", "Science"}

    joint = pd.read_csv(RESULTS / "joint_item_inference.csv")
    assert len(joint) == 12 and set(joint["countries"]) == {64}
    joint_significant = set(
        zip(
            joint.loc[joint.joint_max_t_p_fwer <= .05, "metric"],
            joint.loc[joint.joint_max_t_p_fwer <= .05, "question_id"],
        )
    )
    assert joint_significant == {("W1", "Q108"), ("TVD", "Q106"), ("TVD", "Q108")}
    assert (joint["country_bootstrap_draws"] == 20_000).all()
    assert (joint["joint_signflip_permutations"] == 19_999).all()

    composition = pd.read_csv(RESULTS / "composition_summary.csv").set_index(["comparison", "component"])
    close(composition.loc[("GPT-5.5", "share_of_individual_error_removed_by_five_generation_average"), "estimate"], .011798, 5e-7)
    close(composition.loc[("GPT-5.6 Sol", "share_of_individual_error_removed_by_five_generation_average"), "estimate"], .013131, 5e-7)
    residual_delta = composition.loc[("GPT-5.6 Sol minus GPT-5.5", "five_run_residual")]
    assert residual_delta.ci_high_bca < 0 and residual_delta.permutation_p_two_sided < .001
    varying_delta = composition.loc[("GPT-5.6 Sol minus GPT-5.5", "reducible_generation_component")]
    assert varying_delta.ci_low_bca < 0 < varying_delta.ci_high_bca
    cells = pd.read_csv(RESULTS / "composition_cell_curves.csv")
    assert len(cells) == 64 * 6 * 2 * 5
    assert cells["finite_population_identity_error"].abs().max() < 1e-12

    margins = pd.read_csv(RESULTS / "economic_margin_results.csv").set_index("margin")
    assert margins.loc["Distribution and adjustment", "holm_p_three_margins"] < .001
    assert margins.loc["Opportunity and participation", "holm_p_three_margins"] < .01
    assert margins.loc["Coordination and legitimacy", "delta_ci_low_bca"] <= 0 <= margins.loc["Coordination and legitimacy", "delta_ci_high_bca"]
    surface_summary = pd.read_csv(RESULTS / "economic_weight_surface_summary.csv").iloc[0]
    assert int(surface_summary.grid_points) == 1326
    close(surface_summary.fraction_ci_favors_gpt56, .887632, 5e-7)
    assert surface_summary.fraction_ci_favors_gpt55 == 0

    five = pd.read_csv(RESULTS / "five_anchor_metric_comparisons.csv").set_index("metric")
    assert five.loc["W1", "holm_p_five_metrics"] <= .05 and five.loc["W1", "ci_high_bca"] < 0
    assert five.loc["TVD", "holm_p_five_metrics"] < .001 and five.loc["TVD", "ci_high_bca"] < 0
    q121 = pd.read_csv(RESULTS / "q121_prompt_deviation_sensitivity.csv")
    assert (q121["holm_p_two_metrics"] > .05).all()

    wording = pd.read_csv(RESULTS / "wording_omission_sensitivity.csv")
    assert len(wording) == 12 and set(wording.countries) == {64}
    assert set(wording.country_bootstrap_draws) == {20_000}
    assert set(wording.permutations) == {19_999}
    omission = wording.set_index(["scenario", "metric"])
    close(omission.loc[("all six anchors", "TVD"), "delta_56_minus_55"],
          contrasts.loc["TVD", "estimate"], 1e-12)
    close(omission.loc[("exclude Q121", "TVD"), "delta_56_minus_55"],
          five.loc["TVD", "estimate"], 1e-12)
    close(omission.loc[("exclude Q106", "TVD"), "delta_56_minus_55"], -0.004332, 5e-7)
    close(omission.loc[("exclude Q106 and Q108", "TVD"), "delta_56_minus_55"], -0.000240, 5e-7)
    assert omission.loc[("exclude Q106", "TVD"), "delta_ci_high_bca"] < 0
    assert (omission.loc[("exclude Q106 and Q108", "TVD"), "delta_ci_low_bca"] < 0 <
            omission.loc[("exclude Q106 and Q108", "TVD"), "delta_ci_high_bca"])

    regions = pd.read_csv(RESULTS / "eight_region_sensitivity.csv")
    assert len(regions) == 16 and set(regions["metric"]) == {"W1", "TVD"}
    assert regions.groupby("metric").countries.sum().to_dict() == {"W1": 64, "TVD": 64}
    assert set(regions["cultural_region"]) == {
        "African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
        "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia",
    }
    by_region = regions[regions.metric == "TVD"].set_index("cultural_region")
    assert (by_region.drop(index="Confucian").delta_56_minus_55 < 0).all()
    assert by_region.loc["Confucian", "delta_ci_low_bca"] < 0 < by_region.loc["Confucian", "delta_ci_high_bca"]
    close(by_region.loc["Confucian", "delta_56_minus_55"], .002095250216, 1e-9)
    assert by_region.loc["Catholic Europe", "countries"] == 2
    assert by_region.loc["Protestant Europe", "countries"] == 4
    assert regions[regions.countries < 5][["delta_ci_low_bca", "delta_ci_high_bca"]].isna().all().all()
    assert regions[regions.countries >= 5][["delta_ci_low_bca", "delta_ci_high_bca"]].notna().all().all()
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    for metric in ("W1", "TVD"):
        grouped = regions[regions.metric == metric]
        pooled = np.average(grouped.delta_56_minus_55, weights=grouped.countries)
        by_country = scores.pivot_table(
            index="country", columns="model", values=metric.lower(), aggfunc="mean"
        )
        close(pooled, (by_country["GPT-5.6 Sol"] - by_country["GPT-5.5"]).mean(), 1e-12)

    conditional = pd.read_csv(RESULTS / "conditional_uncertainty_contrasts.csv")
    assert set(conditional["draws"]) == {5_000} and len(conditional) == 10
    stability = pd.read_csv(RESULTS / "run_stability.csv")
    overall_stability = stability[stability.scope == "All six anchors"]
    assert len(overall_stability) == 2
    assert (overall_stability["country_question_cells"] == 384).all()
    assert (overall_stability["generations_per_cell"] == 5).all()

    spatial = pd.read_csv(RESULTS / "spatial_diagnostics.csv")
    crg = spatial[
        (spatial.knn_k == 4)
        & (spatial.model_or_contrast == "GPT-5.6 Sol minus GPT-5.5")
        & (spatial.outcome == "CRG")
    ].iloc[0]
    close(crg["moran_i"], 0.224527)
    close(crg["geary_c"], 0.752115)
    assert crg["geary_bh_q_primary_family"] < .05
    assert crg["moran_bh_q_primary_family"] > .05
    sem = pd.read_csv(RESULTS / "spatial_error_models.csv")
    market_sem = sem[(sem.knn_k == 4) & (sem.scope == "Market")].iloc[0]
    overall_sem = sem[(sem.knn_k == 4) & (sem.scope == "All six anchors")].iloc[0]
    assert market_sem["holm_p_seven_scopes"] < .001
    assert overall_sem["ci_low_95"] < 0 < overall_sem["ci_high_95"]
    tvd_sem = sem[(sem.metric == "TVD") & (sem.scope == "All six anchors")]
    assert len(tvd_sem) == 3 and (tvd_sem.ci_high_95 < 0).all()
    hac = pd.read_csv(RESULTS / "spatial_hac_contrasts.csv")
    tvd_hac = hac[(hac.metric == "TVD") & (hac.scope == "All six anchors")]
    assert len(tvd_hac) == 4 and (tvd_hac.ci_high_95 < 0).all()

    expected_assets = [
        *[FIGS / f"{stem}{suffix}" for stem in (
            "fig1_spatial_story", "fig2_multiview_results", "fig3_economic_story",
            "figS1_uncertainty_sources", "figS2_study_design",
            "figS3_economic_sensitivity", "figS4_country_maps",
            "figS5_country_profiles",
        ) for suffix in (".pdf", ".svg")],
        FIGS / "fig1_spatial_story.drawio",
        FIGS / "figS2_study_design.drawio",
        SOURCES / "semantic_graphics_manifest.json",
        SOURCES / "data/prior_study_benchmark.csv",
        SOURCES / "data/archived_geometry_benchmark.csv",
        SOURCES / "data/figure1_error_type_examples.csv",
        SOURCES / "clip-art-set/clip-art-manifest.json",
        ROOT / "SUBMISSION_METADATA.md",
    ]
    assert all(path.exists() and path.stat().st_size > 0 for path in expected_assets)
    assert not (ROOT / "paper").exists(), "manuscript sources belong in the paper repository"
    forbidden = [path for path in ROOT.rglob("*") if path.is_file() and
                 (path.suffix.lower() in {".tex", ".sty", ".bib"} or path.name == "latexmkrc")]
    assert not forbidden, f"manuscript source files found in code release: {forbidden}"
    metadata = (ROOT / "SUBMISSION_METADATA.md").read_text(encoding="utf-8")
    for heading in ("## Title", "## Keywords", "## TL;DR", "## Abstract"):
        assert heading in metadata
    assert (ROOT / "requirements.txt").read_text(encoding="utf-8").strip().endswith("requirements.lock.txt")
    citation_cff = (ROOT / "CITATION.cff").read_text(encoding="utf-8")
    assert "version: 1.0.0" in citation_cff
    assert (
        "Whose Values Guide Technological Change? Cultural Representation, "
        "Language-Model Updates, and Creative Destruction"
    ) in citation_cff

    for path in [*EXP.rglob("*"), *SOURCES.rglob("*")]:
        if path.is_file() and path.stat().st_size < 50_000_000:
            data = path.read_bytes()
            assert not re.search(rb"sk-(?:proj-)?[A-Za-z0-9_-]{20,}", data), f"possible secret: {path}"

    print(
        "PASS: 3,840 versioned outputs, 64-country pairing, prompt hashes, full "
        "uncertainty, joint multiplicity, composition, economic margins, spatial diagnostics, "
        "eight-region results, vector assets, code-only boundary, metadata, and secret scan"
    )


if __name__ == "__main__":
    main()
