#!/usr/bin/env python3
"""Extended analyses for the 64-country EthosGPT experiment.

This module adds four analyses without making new model calls:

1. dependence-preserving joint max-T inference across the 12 item-by-metric
   contrasts;
2. an exact finite-five-generation composition diagnostic;
3. theory-indexed creative-destruction margin and weight-simplex sensitivity;
4. leave-region-out and human-cell-count influence diagnostics.

Countries, not generations, are the independent inferential units.  All
randomization and bootstrap procedures preserve pairing between GPT-5.5 and
GPT-5.6 Sol within country.
"""

from __future__ import annotations

import argparse
from itertools import combinations
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

import score_wave1 as core


MARGIN_MAP = {
    "Opportunity and participation": ("Agency", "Science"),
    "Distribution and adjustment": ("Distribution", "Market"),
    "Coordination and legitimacy": ("Trust", "Inclusion"),
}
DISPLAY_LABELS = {
    "Agency": "Agency (Q48)",
    "Trust": "Trust (Q57)",
    "Distribution": "Income distribution (Q106)",
    "Market": "Responsibility (Q108)",
    "Inclusion": "Immigration (Q121)",
    "Science": "Science opportunity (Q159)",
}


def _bca_mean(values: np.ndarray, indices: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, float)
    estimate = float(values.mean())
    draws = values[indices].mean(axis=1)
    jack = np.asarray([np.delete(values, i).mean() for i in range(len(values))])
    low, high = core.bca_interval(draws, estimate, jack)
    return {
        "estimate": estimate,
        "standard_error": float(draws.std(ddof=1)),
        "ci_low_bca": low,
        "ci_high_bca": high,
    }


def joint_item_inference(
    scores: pd.DataFrame,
    bootstrap_draws: int,
    permutations: int,
) -> pd.DataFrame:
    """Control all six-item W1/TVD contrasts as one 12-outcome family."""
    countries = pd.Index(sorted(scores["country"].unique()), name="country")
    columns: list[dict[str, object]] = []
    arrays: list[np.ndarray] = []
    for metric in ("w1", "tvd"):
        for domain in core.DOMAIN_ORDER:
            model_values = {
                model: scores[(scores["model"] == model) & (scores["domain"] == domain)]
                .set_index("country")[metric]
                .reindex(countries)
                .to_numpy(float)
                for model in core.MODELS
            }
            arrays.append(model_values[core.MODELS[1]] - model_values[core.MODELS[0]])
            qid = str(scores[scores["domain"] == domain]["question_id"].iloc[0])
            columns.append({
                "metric": metric.upper(),
                "domain": domain,
                "display_label": DISPLAY_LABELS[domain],
                "question_id": qid,
            })
    differences = np.column_stack(arrays)
    n, outcomes = differences.shape
    observed = differences.mean(axis=0)
    observed_se = differences.std(axis=0, ddof=1) / math.sqrt(n)
    observed_t = observed / observed_se

    rng = np.random.default_rng(core.SEED + 901)
    extreme_raw = np.zeros(outcomes, int)
    extreme_joint = np.zeros(outcomes, int)
    completed = 0
    batch_size = 5_000
    while completed < permutations:
        size = min(batch_size, permutations - completed)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(size, n, 1))
        permuted = signs * differences[None, :, :]
        perm_mean = permuted.mean(axis=1)
        perm_se = permuted.std(axis=1, ddof=1) / math.sqrt(n)
        perm_t = np.divide(perm_mean, perm_se, out=np.zeros_like(perm_mean), where=perm_se > 0)
        absolute = np.abs(perm_t)
        maximum = absolute.max(axis=1)
        extreme_raw += (absolute >= np.abs(observed_t)[None, :] - 1e-15).sum(axis=0)
        extreme_joint += (maximum[:, None] >= np.abs(observed_t)[None, :] - 1e-15).sum(axis=0)
        completed += size
    raw_p = (extreme_raw + 1) / (permutations + 1)
    max_t_p = (extreme_joint + 1) / (permutations + 1)

    bootstrap_rng = np.random.default_rng(core.SEED + 902)
    indices = bootstrap_rng.integers(0, n, size=(bootstrap_draws, n))
    sampled = differences[indices]
    bootstrap_mean = sampled.mean(axis=1)
    bootstrap_se = sampled.std(axis=1, ddof=1) / math.sqrt(n)
    bootstrap_t = np.divide(
        bootstrap_mean - observed[None, :],
        bootstrap_se,
        out=np.zeros_like(bootstrap_mean),
        where=bootstrap_se > 0,
    )
    critical = float(np.quantile(np.abs(bootstrap_t).max(axis=1), 0.95))
    simultaneous_low = observed - critical * observed_se
    simultaneous_high = observed + critical * observed_se

    rows = []
    for index, metadata in enumerate(columns):
        row = dict(metadata)
        row.update({
            "countries": n,
            "delta_56_minus_55": observed[index],
            "country_standard_error": observed_se[index],
            "simultaneous_ci_low_95": simultaneous_low[index],
            "simultaneous_ci_high_95": simultaneous_high[index],
            "bootstrap_max_t_critical_95": critical,
            "signflip_p_two_sided": raw_p[index],
            "joint_max_t_p_fwer": max_t_p[index],
            "joint_max_t_p_mcse": math.sqrt(max_t_p[index] * (1 - max_t_p[index]) / (permutations + 1)),
            "country_bootstrap_draws": bootstrap_draws,
            "joint_signflip_permutations": permutations,
            "family": "six survey items x W1/TVD (12 outcomes)",
            "interpretation_if_negative": "GPT-5.6 Sol has lower error",
        })
        rows.append(row)
    return pd.DataFrame(rows)


def _human_probability_lookup(human: pd.DataFrame) -> dict[tuple[str, str], np.ndarray]:
    metadata = pd.read_csv(core.ROOT / "data/metadata/item_dictionary.csv").set_index("question_id")
    lookup: dict[tuple[str, str], np.ndarray] = {}
    for (country, question_id), frame in human.groupby(["country", "question_id"]):
        minimum = int(metadata.loc[question_id, "scale_min"])
        maximum = int(metadata.loc[question_id, "scale_max"])
        support = np.arange(minimum, maximum + 1)
        lookup[(country, question_id)] = (
            frame.set_index("score")["probability"].reindex(support, fill_value=0).to_numpy(float)
        )
    return lookup


def composition_cells(outputs: pd.DataFrame, human: pd.DataFrame) -> pd.DataFrame:
    """Average over every subset of the five observed generations."""
    metadata = pd.read_csv(core.ROOT / "data/metadata/item_dictionary.csv").set_index("question_id")
    human_lookup = _human_probability_lookup(human)
    rows: list[dict[str, object]] = []
    group_columns = ["model", "country", "country_code", "cultural_region", "question_id", "domain"]
    for key, frame in outputs.groupby(group_columns, sort=True):
        model, country, country_code, region, question_id, domain = key
        minimum = int(metadata.loc[question_id, "scale_min"])
        maximum = int(metadata.loc[question_id, "scale_max"])
        ordered = frame.sort_values("generation")
        vectors = np.stack([
            core.support_probabilities(value, minimum, maximum)
            for value in ordered["official_category_probabilities"]
        ])
        human_p = human_lookup[(country, question_id)]
        full_mean = vectors.mean(axis=0)
        five_run_residual = float(np.square(full_mean - human_p).sum())
        within_component = float(np.square(vectors - full_mean).sum(axis=1).mean())
        for ensemble_size in range(1, core.EXPECTED_GENERATIONS + 1):
            metrics = {"squared_probability_error": [], "w1": [], "tvd": []}
            for subset in combinations(range(core.EXPECTED_GENERATIONS), ensemble_size):
                pooled = vectors[list(subset)].mean(axis=0)
                metrics["squared_probability_error"].append(float(np.square(pooled - human_p).sum()))
                metrics["w1"].append(float(core.w1_from_probabilities(pooled, human_p)))
                metrics["tvd"].append(float(core.tvd_from_probabilities(pooled, human_p)))
            rows.append({
                "model": model,
                "country": country,
                "country_code": int(country_code),
                "cultural_region": region,
                "question_id": question_id,
                "domain": domain,
                "ensemble_size": ensemble_size,
                "subsets_averaged": len(metrics["w1"]),
                "squared_probability_error": float(np.mean(metrics["squared_probability_error"])),
                "w1": float(np.mean(metrics["w1"])),
                "tvd": float(np.mean(metrics["tvd"])),
                "full_five_generation_residual": five_run_residual,
                "within_generation_component": within_component,
                "finite_population_identity_error": (
                    float(np.mean(metrics["squared_probability_error"]))
                    - five_run_residual
                    - ((core.EXPECTED_GENERATIONS - ensemble_size)
                       / (ensemble_size * (core.EXPECTED_GENERATIONS - 1))) * within_component
                ),
            })
    result = pd.DataFrame(rows)
    if result["finite_population_identity_error"].abs().max() > 1e-12:
        raise AssertionError("Finite-five-generation composition identity failed")
    return result


def composition_inference(
    cells: pd.DataFrame,
    bootstrap_draws: int,
    permutations: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = pd.Index(sorted(cells["country"].unique()), name="country")
    country_curve = (
        cells.groupby(["model", "country", "ensemble_size"], as_index=False)
        [["squared_probability_error", "w1", "tvd"]]
        .mean()
    )
    rng = np.random.default_rng(core.SEED + 911)
    indices = rng.integers(0, len(countries), size=(bootstrap_draws, len(countries)))
    permutation_rng = np.random.default_rng(core.SEED + 912)

    estimate_rows: list[dict[str, object]] = []
    contrast_rows: list[dict[str, object]] = []
    for metric in ("squared_probability_error", "w1", "tvd"):
        for ensemble_size in range(1, core.EXPECTED_GENERATIONS + 1):
            model_arrays = {}
            for model in core.MODELS:
                values = country_curve[
                    (country_curve["model"] == model)
                    & (country_curve["ensemble_size"] == ensemble_size)
                ].set_index("country")[metric].reindex(countries).to_numpy(float)
                model_arrays[model] = values
                summary = _bca_mean(values, indices)
                estimate_rows.append({
                    "model": model,
                    "metric": metric,
                    "ensemble_size": ensemble_size,
                    "countries": len(countries),
                    "country_question_cells": len(countries) * len(core.QUESTION_ORDER),
                    "country_bootstrap_draws": bootstrap_draws,
                    **summary,
                })
            delta = model_arrays[core.MODELS[1]] - model_arrays[core.MODELS[0]]
            summary = _bca_mean(delta, indices)
            pvalue, mcse = core.signflip_test(delta, permutations, permutation_rng)
            contrast_rows.append({
                "metric": metric,
                "ensemble_size": ensemble_size,
                "countries": len(countries),
                "estimand": "GPT-5.6 Sol minus GPT-5.5",
                "permutation_p_two_sided": pvalue,
                "permutation_p_mcse": mcse,
                "permutations": permutations,
                **summary,
            })

    contrasts = pd.DataFrame(contrast_rows)
    for metric in contrasts["metric"].unique():
        mask = contrasts["metric"] == metric
        contrasts.loc[mask, "holm_p_five_ensemble_sizes"] = core.holm_adjust(
            contrasts.loc[mask, "permutation_p_two_sided"].to_numpy()
        )

    component_country_rows: list[dict[str, object]] = []
    for model in core.MODELS:
        model_curve = country_curve[country_curve["model"] == model]
        first = model_curve[model_curve["ensemble_size"] == 1].set_index("country")["squared_probability_error"].reindex(countries)
        residual = model_curve[model_curve["ensemble_size"] == 5].set_index("country")["squared_probability_error"].reindex(countries)
        for country in countries:
            component_country_rows.append({
                "model": model,
                "country": country,
                "individual_error": float(first.loc[country]),
                "five_run_residual": float(residual.loc[country]),
                "reducible_generation_component": float(first.loc[country] - residual.loc[country]),
            })
    component_country = pd.DataFrame(component_country_rows)

    summary_rows: list[dict[str, object]] = []
    for model in core.MODELS:
        frame = component_country[component_country["model"] == model].set_index("country").reindex(countries)
        summaries = {name: _bca_mean(frame[name].to_numpy(float), indices) for name in (
            "individual_error", "five_run_residual", "reducible_generation_component"
        )}
        share_draws = (
            frame["reducible_generation_component"].to_numpy(float)[indices].mean(axis=1)
            / frame["individual_error"].to_numpy(float)[indices].mean(axis=1)
        )
        share = float(frame["reducible_generation_component"].mean() / frame["individual_error"].mean())
        for component, values in summaries.items():
            pvalue, mcse = core.signflip_test(frame[component].to_numpy(float), permutations, permutation_rng)
            summary_rows.append({
                "comparison": model,
                "component": component,
                "countries": len(countries),
                "permutation_p_two_sided": pvalue,
                "permutation_p_mcse": mcse,
                **values,
            })
        summary_rows.append({
            "comparison": model,
            "component": "share_of_individual_error_removed_by_five_generation_average",
            "countries": len(countries),
            "estimate": share,
            "standard_error": float(share_draws.std(ddof=1)),
            "ci_low_bca": float(np.quantile(share_draws, .025)),
            "ci_high_bca": float(np.quantile(share_draws, .975)),
            "permutation_p_two_sided": np.nan,
            "permutation_p_mcse": np.nan,
        })

    first = component_country[component_country["model"] == core.MODELS[0]].set_index("country").reindex(countries)
    second = component_country[component_country["model"] == core.MODELS[1]].set_index("country").reindex(countries)
    for component in ("individual_error", "five_run_residual", "reducible_generation_component"):
        delta = second[component].to_numpy(float) - first[component].to_numpy(float)
        values = _bca_mean(delta, indices)
        pvalue, mcse = core.signflip_test(delta, permutations, permutation_rng)
        summary_rows.append({
            "comparison": "GPT-5.6 Sol minus GPT-5.5",
            "component": component,
            "countries": len(countries),
            "permutation_p_two_sided": pvalue,
            "permutation_p_mcse": mcse,
            **values,
        })

    return pd.DataFrame(estimate_rows), contrasts, pd.DataFrame(summary_rows)


def economic_margin_analysis(
    scores: pd.DataFrame,
    bootstrap_draws: int,
    permutations: int,
    grid_step: float,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = pd.Index(sorted(scores["country"].unique()), name="country")
    country_rows: list[dict[str, object]] = []
    for model in core.MODELS:
        for country in countries:
            frame = scores[(scores["model"] == model) & (scores["country"] == country)]
            for margin, domains in MARGIN_MAP.items():
                values = frame[frame["domain"].isin(domains)]["tvd"].to_numpy(float)
                if len(values) != 2:
                    raise ValueError(f"{model}/{country}/{margin}: expected two survey items")
                country_rows.append({
                    "model": model,
                    "country": country,
                    "margin": margin,
                    "mean_squared_tvd": float(np.square(values).mean()),
                })
    country_margin = pd.DataFrame(country_rows)
    rng = np.random.default_rng(core.SEED + 921)
    indices = rng.integers(0, len(countries), size=(bootstrap_draws, len(countries)))
    permutation_rng = np.random.default_rng(core.SEED + 922)

    rows: list[dict[str, object]] = []
    delta_by_margin: dict[str, np.ndarray] = {}
    for margin in MARGIN_MAP:
        model_arrays = {}
        for model in core.MODELS:
            values = country_margin[(country_margin["model"] == model) & (country_margin["margin"] == margin)]
            values = values.set_index("country")["mean_squared_tvd"].reindex(countries).to_numpy(float)
            model_arrays[model] = values
        delta = model_arrays[core.MODELS[1]] - model_arrays[core.MODELS[0]]
        delta_by_margin[margin] = delta
        delta_summary = _bca_mean(delta, indices)
        pvalue, mcse = core.signflip_test(delta, permutations, permutation_rng)
        rows.append({
            "margin": margin,
            "survey_items": ", ".join(MARGIN_MAP[margin]),
            "countries": len(countries),
            "gpt55_estimate": float(model_arrays[core.MODELS[0]].mean()),
            "gpt55_standard_error": float(model_arrays[core.MODELS[0]][indices].mean(axis=1).std(ddof=1)),
            "gpt56_estimate": float(model_arrays[core.MODELS[1]].mean()),
            "gpt56_standard_error": float(model_arrays[core.MODELS[1]][indices].mean(axis=1).std(ddof=1)),
            "permutation_p_two_sided": pvalue,
            "permutation_p_mcse": mcse,
            **{f"delta_{key}": value for key, value in delta_summary.items()},
        })
    margin_results = pd.DataFrame(rows)
    margin_results["holm_p_three_margins"] = core.holm_adjust(margin_results["permutation_p_two_sided"].to_numpy())

    margin_order = list(MARGIN_MAP)
    delta_matrix = np.column_stack([delta_by_margin[margin] for margin in margin_order])
    mean_delta = delta_matrix.mean(axis=0)
    bootstrap_margin_delta = delta_matrix[indices].mean(axis=1)

    denominator = int(round(1 / grid_step))
    if not np.isclose(denominator * grid_step, 1):
        raise ValueError("grid_step must divide one exactly")
    surface_rows: list[dict[str, object]] = []
    for first_weight in range(denominator + 1):
        for second_weight in range(denominator - first_weight + 1):
            third_weight = denominator - first_weight - second_weight
            weights = np.asarray([first_weight, second_weight, third_weight], float) / denominator
            estimate = float(mean_delta @ weights)
            draws = bootstrap_margin_delta @ weights
            surface_rows.append({
                "weight_opportunity_participation": weights[0],
                "weight_distribution_adjustment": weights[1],
                "weight_coordination_legitimacy": weights[2],
                "delta_weighted_loss_56_minus_55": estimate,
                "ci_low_95": float(np.quantile(draws, .025)),
                "ci_high_95": float(np.quantile(draws, .975)),
                "bootstrap_probability_gpt56_lower_loss": float(np.mean(draws < 0)),
                "classification": (
                    "GPT-5.6 lower with 95% interval"
                    if np.quantile(draws, .975) < 0
                    else "GPT-5.5 lower with 95% interval"
                    if np.quantile(draws, .025) > 0
                    else "uncertain"
                ),
            })
    surface = pd.DataFrame(surface_rows)

    scenario_weights = {
        "Equal weights": np.asarray([1 / 3, 1 / 3, 1 / 3]),
        "Opportunity only": np.asarray([1.0, 0.0, 0.0]),
        "Distribution only": np.asarray([0.0, 1.0, 0.0]),
        "Coordination only": np.asarray([0.0, 0.0, 1.0]),
    }
    scenario_rows = []
    for scenario, weights in scenario_weights.items():
        draws = bootstrap_margin_delta @ weights
        estimate = float(mean_delta @ weights)
        scenario_rows.append({
            "scenario": scenario,
            "weight_opportunity_participation": weights[0],
            "weight_distribution_adjustment": weights[1],
            "weight_coordination_legitimacy": weights[2],
            "delta_weighted_loss_56_minus_55": estimate,
            "standard_error": float(draws.std(ddof=1)),
            "ci_low_95": float(np.quantile(draws, .025)),
            "ci_high_95": float(np.quantile(draws, .975)),
            "bootstrap_probability_gpt56_lower_loss": float(np.mean(draws < 0)),
        })
    scenarios = pd.DataFrame(scenario_rows)
    summary = pd.DataFrame([{
        "grid_step": grid_step,
        "grid_points": len(surface),
        "fraction_point_estimate_favors_gpt56": float((surface["delta_weighted_loss_56_minus_55"] < 0).mean()),
        "fraction_ci_favors_gpt56": float((surface["classification"] == "GPT-5.6 lower with 95% interval").mean()),
        "fraction_ci_favors_gpt55": float((surface["classification"] == "GPT-5.5 lower with 95% interval").mean()),
        "fraction_uncertain": float((surface["classification"] == "uncertain").mean()),
        "interpretation": "Exploratory theory-indexed sensitivity; not realized welfare or policy impact",
    }])
    return margin_results, surface, scenarios, summary


def influence_analysis(scores: pd.DataFrame, bootstrap_draws: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    country = (
        scores.groupby(["model", "country", "cultural_region"], as_index=False)
        .agg(w1=("w1", "mean"), tvd=("tvd", "mean"), mean_human_n=("human_n", "mean"))
    )
    wide = country.pivot(index=["country", "cultural_region", "mean_human_n"], columns="model", values=["w1", "tvd"])
    wide.columns = [f"{metric}_{model}" for metric, model in wide.columns]
    wide = wide.reset_index()
    for metric in ("w1", "tvd"):
        wide[f"delta_{metric}"] = wide[f"{metric}_{core.MODELS[1]}"] - wide[f"{metric}_{core.MODELS[0]}"]

    region_rows = []
    for omitted in sorted(wide["cultural_region"].unique()):
        retained = wide[wide["cultural_region"] != omitted]
        for metric in ("w1", "tvd"):
            values = retained[f"delta_{metric}"].to_numpy(float)
            region_rows.append({
                "omitted_cultural_region": omitted,
                "metric": metric.upper(),
                "countries_retained": len(retained),
                "estimate": float(values.mean()),
                "standard_error": float(values.std(ddof=1) / math.sqrt(len(values))),
            })
    region = pd.DataFrame(region_rows)

    wide["human_cell_count_quartile"] = pd.qcut(
        wide["mean_human_n"],
        4,
        labels=["Q1 lowest", "Q2", "Q3", "Q4 highest"],
    )
    rng = np.random.default_rng(core.SEED + 931)
    count_rows = []
    for quartile, frame in wide.groupby("human_cell_count_quartile", observed=False):
        indices = rng.integers(0, len(frame), size=(bootstrap_draws, len(frame)))
        for metric in ("w1", "tvd"):
            values = frame[f"delta_{metric}"].to_numpy(float)
            summary = _bca_mean(values, indices)
            count_rows.append({
                "human_cell_count_quartile": str(quartile),
                "metric": metric.upper(),
                "countries": len(frame),
                "mean_country_average_human_n": float(frame["mean_human_n"].mean()),
                **summary,
            })
    return region, pd.DataFrame(count_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    parser.add_argument("--permutations", type=int, default=19_999)
    parser.add_argument("--economic-grid-step", type=float, default=.02)
    args = parser.parse_args()
    if min(args.bootstrap_draws, args.permutations) < 999:
        raise ValueError("Use at least 999 bootstrap draws and permutations")

    core.RESULTS.mkdir(parents=True, exist_ok=True)
    outputs = core.validate_frozen_outputs()
    _, scores, human = core.score_outputs(outputs)
    human_wide = core.human_profiles(human)
    scores = core.attach_human_scores(scores, human_wide)

    joint = joint_item_inference(scores, args.bootstrap_draws, args.permutations)
    cells = composition_cells(outputs, human)
    comp_estimates, comp_contrasts, comp_summary = composition_inference(
        cells, args.bootstrap_draws, args.permutations
    )
    margins, surface, scenarios, economic_summary = economic_margin_analysis(
        scores, args.bootstrap_draws, args.permutations, args.economic_grid_step
    )
    region, cell_count = influence_analysis(scores, args.bootstrap_draws)

    outputs_to_write = {
        "joint_item_inference.csv": joint,
        "composition_cell_curves.csv": cells,
        "composition_estimates.csv": comp_estimates,
        "composition_contrasts.csv": comp_contrasts,
        "composition_summary.csv": comp_summary,
        "economic_margin_results.csv": margins,
        "economic_weight_surface.csv": surface,
        "economic_scenarios.csv": scenarios,
        "economic_weight_surface_summary.csv": economic_summary,
        "leave_one_region_out.csv": region,
        "human_cell_count_quartile_sensitivity.csv": cell_count,
    }
    for filename, frame in outputs_to_write.items():
        frame.to_csv(core.RESULTS / filename, index=False)

    manifest = {
        "analysis": "EthosGPT extended analysis",
        "analysis_seed": core.SEED,
        "countries": core.EXPECTED_COUNTRIES,
        "questions": list(core.QUESTION_ORDER),
        "models": core.MODEL_IDS,
        "bootstrap_draws": args.bootstrap_draws,
        "joint_signflip_permutations": args.permutations,
        "joint_multiplicity_family": "12 W1/TVD item outcomes",
        "composition_interpretation": "exact exhaustive subsets of five observed generations; countries are inferential units",
        "economic_margin_map": MARGIN_MAP,
        "economic_status": "exploratory theory-indexed sensitivity; no observed economic decisions or welfare outcomes",
        "temporal_boundary": "one collection wave; no spatiotemporal panel inference",
        "result_files": sorted(outputs_to_write),
    }
    (core.MANIFESTS / "extended_analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )

    print("\nJoint 12-outcome max-T inference")
    print(joint[["metric", "display_label", "delta_56_minus_55", "simultaneous_ci_low_95", "simultaneous_ci_high_95", "joint_max_t_p_fwer"]].to_string(index=False))
    print("\nComposition summary")
    print(comp_summary.to_string(index=False))
    print("\nCreative-destruction margins")
    print(margins.to_string(index=False))
    print("\nEconomic sensitivity summary")
    print(economic_summary.to_string(index=False))


if __name__ == "__main__":
    main()
