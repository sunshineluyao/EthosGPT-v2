#!/usr/bin/env python3
"""Sensitivity analyses for the six-anchor Wave 1 protocol.

The primary protocol contains a disclosed response-label inconsistency for
Q121: the stem calls category 1 ``Very bad`` while the enumerated response
list calls it ``Rather bad``.  This script reports (i) the complete five-anchor
analysis after excluding Q121/Inclusion and (ii) transparent Q121 relabeling
bounds that move 0%, 50%, or 100% of model probability mass from category 1
to category 2.  The 100% case is deliberately conservative; it does not claim
to reconstruct what an unambiguous prompt would have produced.
"""

from __future__ import annotations

import argparse
import json

import numpy as np
import pandas as pd

import score_wave1 as core


def question_arrays(
    scores: pd.DataFrame,
    human: pd.DataFrame,
    shift_fraction: float,
) -> tuple[dict[str, dict[str, np.ndarray]], list[str]]:
    """Return country-level Q121 losses after a category-1 to category-2 shift."""
    qid = "Q121"
    countries = sorted(scores["country"].unique())
    human_groups = {
        country: group.sort_values("score")
        for country, group in human[human["question_id"] == qid].groupby("country")
    }
    output: dict[str, dict[str, np.ndarray]] = {
        model: {"W1": np.empty(len(countries)), "TVD": np.empty(len(countries)), "p1": np.empty(len(countries))}
        for model in core.MODELS
    }
    for model in core.MODELS:
        frame = scores[(scores["model"] == model) & (scores["question_id"] == qid)].set_index("country")
        for index, country in enumerate(countries):
            model_p = np.asarray(list(json.loads(frame.loc[country, "model_probabilities"]).values()), float)
            # JSON keys are serialized in numeric order for the 1--5 support.
            moved = model_p[0] * shift_fraction
            adjusted = model_p.copy()
            adjusted[0] -= moved
            adjusted[1] += moved
            h = human_groups[country]
            human_p = h.set_index("score")["probability"].reindex(np.arange(1, 6), fill_value=0).to_numpy(float)
            output[model]["W1"][index] = float(core.w1_from_probabilities(adjusted, human_p))
            output[model]["TVD"][index] = float(core.tvd_from_probabilities(adjusted, human_p))
            output[model]["p1"][index] = model_p[0]
    return output, countries


def summarize_q121(
    scores: pd.DataFrame,
    human: pd.DataFrame,
    bootstrap_draws: int,
    permutations: int,
) -> pd.DataFrame:
    rows: list[dict] = []
    rng = np.random.default_rng(core.SEED + 707)
    perm_rng = np.random.default_rng(core.SEED + 708)
    for shift_fraction, scenario in (
        (0.0, "as collected"),
        (0.5, "move 50% of category-1 mass to category 2"),
        (1.0, "move 100% of category-1 mass to category 2"),
    ):
        arrays, countries = question_arrays(scores, human, shift_fraction)
        indices = rng.integers(0, len(countries), size=(bootstrap_draws, len(countries)))
        for metric in ("W1", "TVD"):
            first = arrays[core.MODELS[0]][metric]
            second = arrays[core.MODELS[1]][metric]
            delta = second - first
            boot_delta = delta[indices].mean(axis=1)
            jack_delta = np.asarray([np.delete(delta, idx).mean() for idx in range(len(countries))])
            low, high = core.bca_interval(boot_delta, float(delta.mean()), jack_delta)
            pvalue, mcse = core.signflip_test(delta, permutations, perm_rng)
            rows.append({
                "scenario": scenario,
                "shift_fraction": shift_fraction,
                "metric": metric,
                "gpt55_estimate": float(first.mean()),
                "gpt55_standard_error": float(first[indices].mean(axis=1).std(ddof=1)),
                "gpt56_estimate": float(second.mean()),
                "gpt56_standard_error": float(second[indices].mean(axis=1).std(ddof=1)),
                "delta_56_minus_55": float(delta.mean()),
                "delta_standard_error": float(boot_delta.std(ddof=1)),
                "delta_ci_low_bca": low,
                "delta_ci_high_bca": high,
                "permutation_p_two_sided": pvalue,
                "permutation_p_mcse": mcse,
                "countries": len(countries),
                "country_bootstrap_draws": bootstrap_draws,
                "permutations": permutations,
                "gpt55_original_category1_mean_probability": float(arrays[core.MODELS[0]]["p1"].mean()),
                "gpt56_original_category1_mean_probability": float(arrays[core.MODELS[1]]["p1"].mean()),
            })
    result = pd.DataFrame(rows)
    for scenario in result["scenario"].unique():
        mask = result["scenario"] == scenario
        result.loc[mask, "holm_p_two_metrics"] = core.holm_adjust(result.loc[mask, "permutation_p_two_sided"].to_numpy())
    return result


def five_anchor_analysis(
    scores: pd.DataFrame,
    human_wide: pd.DataFrame,
    profiles: dict[str, pd.DataFrame],
    bootstrap_draws: int,
    permutations: int,
) -> None:
    retained = [domain for domain in core.DOMAIN_ORDER if domain != "Inclusion"]
    five_scores = scores[scores["domain"].isin(retained)].copy()
    five_human = human_wide[retained].copy()
    five_profiles = {model: frame[retained].copy() for model, frame in profiles.items()}
    estimates, comparisons, loo, draws = core.build_core_inference(
        five_scores,
        five_human,
        five_profiles,
        bootstrap_draws,
        permutations,
    )
    estimates.insert(0, "sensitivity", "exclude Q121 / five anchors")
    comparisons.insert(0, "sensitivity", "exclude Q121 / five anchors")
    loo.insert(0, "sensitivity", "exclude Q121 / five anchors")
    estimates.to_csv(core.RESULTS / "five_anchor_metric_estimates.csv", index=False)
    comparisons.to_csv(core.RESULTS / "five_anchor_metric_comparisons.csv", index=False)
    loo.to_csv(core.RESULTS / "five_anchor_leave_one_country_out.csv", index=False)
    draws.to_parquet(core.RESULTS / "five_anchor_bootstrap_draws.parquet", index=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    parser.add_argument("--permutations", type=int, default=19_999)
    args = parser.parse_args()
    if args.bootstrap_draws < 1_000 or args.permutations < 999:
        raise ValueError("Sensitivity release requires >=1,000 bootstrap draws and >=999 permutations")

    outputs = core.validate_frozen_outputs()
    _, scores, human = core.score_outputs(outputs)
    human_wide = core.human_profiles(human)
    profiles = core.model_profiles(scores, human_wide.index)
    scores = core.attach_human_scores(scores, human_wide)

    five_anchor_analysis(scores, human_wide, profiles, args.bootstrap_draws, args.permutations)
    q121 = summarize_q121(scores, human, args.bootstrap_draws, args.permutations)
    q121.to_csv(core.RESULTS / "q121_prompt_deviation_sensitivity.csv", index=False)
    print("Five-anchor contrasts")
    print(pd.read_csv(core.RESULTS / "five_anchor_metric_comparisons.csv").to_string(index=False))
    print("\nQ121 label-shift sensitivity")
    print(q121.to_string(index=False))


if __name__ == "__main__":
    main()
