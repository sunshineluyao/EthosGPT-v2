#!/usr/bin/env python3
"""Separate model-run and human-cell contributions to uncertainty.

These conditional simulations complement, rather than replace, the primary
country-cluster bootstrap in ``score_wave1.py``. The human simulation is a
multinomial cell bootstrap and cannot reconstruct unavailable survey weights,
strata, clusters, or uncertain upstream provenance.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

import score_wave1 as core


def summarize(
    source: str,
    draws: dict[str, dict[str, np.ndarray]],
    point: dict[str, dict[str, float]],
) -> tuple[list[dict], list[dict]]:
    model_rows: list[dict] = []
    contrast_rows: list[dict] = []
    for model in core.MODELS:
        for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
            values = np.asarray(draws[model][metric], float)
            finite = values[np.isfinite(values)]
            raw_low, raw_high = np.quantile(finite, [0.025, 0.975])
            centered = finite - finite.mean()
            low, high = point[model][metric] + np.quantile(centered, [0.025, 0.975])
            model_rows.append({
                "uncertainty_source": source,
                "model": model,
                "metric": metric,
                "point_estimate": point[model][metric],
                "conditional_standard_error": float(np.std(finite, ddof=1)),
                "centered_sensitivity_interval_low_95": float(low),
                "centered_sensitivity_interval_high_95": float(high),
                "simulation_mean": float(finite.mean()),
                "simulation_bias_from_point": float(finite.mean() - point[model][metric]),
                "raw_simulation_quantile_low_025": float(raw_low),
                "raw_simulation_quantile_high_975": float(raw_high),
                "draws": int(len(finite)),
            })
    for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
        values = np.asarray([core.metric_loss(metric, value) for value in draws[core.MODELS[1]][metric]]) - np.asarray([core.metric_loss(metric, value) for value in draws[core.MODELS[0]][metric]])
        finite = values[np.isfinite(values)]
        estimate = core.metric_loss(metric, point[core.MODELS[1]][metric]) - core.metric_loss(metric, point[core.MODELS[0]][metric])
        raw_low, raw_high = np.quantile(finite, [0.025, 0.975])
        centered = finite - finite.mean()
        low, high = estimate + np.quantile(centered, [0.025, 0.975])
        contrast_rows.append({
            "uncertainty_source": source,
            "metric": metric,
            "point_loss_delta_56_minus_55": estimate,
            "conditional_standard_error": float(np.std(finite, ddof=1)),
            "centered_sensitivity_interval_low_95": float(low),
            "centered_sensitivity_interval_high_95": float(high),
            "simulation_mean": float(finite.mean()),
            "simulation_bias_from_point": float(finite.mean() - estimate),
            "raw_simulation_quantile_low_025": float(raw_low),
            "raw_simulation_quantile_high_975": float(raw_high),
            "draws": int(len(finite)),
        })
    return model_rows, contrast_rows


def empty_draws(draw_count: int) -> dict[str, dict[str, np.ndarray]]:
    return {
        model: {metric: np.zeros(draw_count, float) for metric in ("W1", "TVD", "CRG", "VDR", "CSR")}
        for model in core.MODELS
    }


def human_multinomial_draws(
    scores: pd.DataFrame,
    human: pd.DataFrame,
    human_wide: pd.DataFrame,
    profiles: dict[str, pd.DataFrame],
    draw_count: int,
) -> dict[str, dict[str, np.ndarray]]:
    countries = list(human_wide.index)
    country_index = {country: idx for idx, country in enumerate(countries)}
    domain_index = {domain: idx for idx, domain in enumerate(core.DOMAIN_ORDER)}
    item_meta = pd.read_csv(core.ROOT / "data/metadata/item_dictionary.csv").set_index("question_id")
    human_groups = {key: group.sort_values("score") for key, group in human.groupby(["country", "question_id"])}
    rng = np.random.default_rng(core.SEED + 505)
    h_draw = np.empty((draw_count, len(countries), len(core.DOMAIN_ORDER)), float)
    draws = empty_draws(draw_count)
    model_prob = {
        (row.model, row.country, row.question_id): json.loads(row.model_probabilities)
        for row in scores.itertuples(index=False)
    }
    for country in countries:
        for domain in core.DOMAIN_ORDER:
            question_id = scores[(scores["country"] == country) & (scores["domain"] == domain)]["question_id"].iloc[0]
            meta = item_meta.loc[question_id]
            support = np.arange(int(meta.scale_min), int(meta.scale_max) + 1)
            h = human_groups[(country, question_id)]
            probabilities = h.set_index("score")["probability"].reindex(support, fill_value=0).to_numpy(float)
            n = int(h["n"].iloc[0])
            sampled = rng.multinomial(n, probabilities, size=draw_count) / n
            normalized = (support - int(meta.scale_min)) / (int(meta.scale_max) - int(meta.scale_min))
            expected = sampled @ normalized
            if meta.direction == "reverse":
                expected = 1 - expected
            h_draw[:, country_index[country], domain_index[domain]] = expected
            for model in core.MODELS:
                p = np.asarray([model_prob[(model, country, question_id)][str(int(value))] for value in support], float)
                draws[model]["W1"] += core.w1_from_probabilities(np.broadcast_to(p, sampled.shape), sampled) / (len(countries) * len(core.DOMAIN_ORDER))
                draws[model]["TVD"] += core.tvd_from_probabilities(np.broadcast_to(p, sampled.shape), sampled) / (len(countries) * len(core.DOMAIN_ORDER))
    model_arrays = {model: profiles[model].to_numpy(float) for model in core.MODELS}
    for draw in range(draw_count):
        hb = h_draw[draw]
        sigma = hb.std(axis=0, ddof=1)
        hdist = core.pdist(hb)
        for model in core.MODELS:
            m = model_arrays[model]
            draws[model]["CRG"][draw] = np.sqrt(np.square((m - hb) / sigma).mean(axis=1)).mean()
            mdist = core.pdist(m)
            draws[model]["VDR"][draw] = mdist.mean() / hdist.mean()
            draws[model]["CSR"][draw] = core.spearmanr(hdist, mdist).statistic
    return draws


def generation_draws(
    outputs: pd.DataFrame,
    human: pd.DataFrame,
    human_wide: pd.DataFrame,
    draw_count: int,
) -> dict[str, dict[str, np.ndarray]]:
    countries = list(human_wide.index)
    country_index = {country: idx for idx, country in enumerate(countries)}
    domain_index = {domain: idx for idx, domain in enumerate(core.DOMAIN_ORDER)}
    item_meta = pd.read_csv(core.ROOT / "data/metadata/item_dictionary.csv").set_index("question_id")
    human_groups = {key: group.sort_values("score") for key, group in human.groupby(["country", "question_id"])}
    rng = np.random.default_rng(core.SEED + 606)
    draws = empty_draws(draw_count)
    m_draw = {model: np.empty((draw_count, len(countries), len(core.DOMAIN_ORDER)), float) for model in core.MODELS}
    for model in core.MODELS:
        frame = outputs[outputs["model"] == model]
        for (country, question_id, domain), group in frame.groupby(["country", "question_id", "domain"]):
            meta = item_meta.loc[question_id]
            support = np.arange(int(meta.scale_min), int(meta.scale_max) + 1)
            generation_probabilities = np.vstack([
                core.support_probabilities(mapping, int(meta.scale_min), int(meta.scale_max))
                for mapping in group.sort_values("generation")["official_category_probabilities"]
            ])
            selected = rng.integers(0, core.EXPECTED_GENERATIONS, size=(draw_count, core.EXPECTED_GENERATIONS))
            sampled = generation_probabilities[selected].mean(axis=1)
            h = human_groups[(country, question_id)]
            human_p = h.set_index("score")["probability"].reindex(support, fill_value=0).to_numpy(float)
            draws[model]["W1"] += core.w1_from_probabilities(sampled, np.broadcast_to(human_p, sampled.shape)) / (len(countries) * len(core.DOMAIN_ORDER))
            draws[model]["TVD"] += core.tvd_from_probabilities(sampled, np.broadcast_to(human_p, sampled.shape)) / (len(countries) * len(core.DOMAIN_ORDER))
            normalized = (support - int(meta.scale_min)) / (int(meta.scale_max) - int(meta.scale_min))
            expected = sampled @ normalized
            if meta.direction == "reverse":
                expected = 1 - expected
            m_draw[model][:, country_index[country], domain_index[domain]] = expected
    h = human_wide.to_numpy(float)
    sigma = h.std(axis=0, ddof=1)
    hdist = core.pdist(h)
    for draw in range(draw_count):
        for model in core.MODELS:
            m = m_draw[model][draw]
            draws[model]["CRG"][draw] = np.sqrt(np.square((m - h) / sigma).mean(axis=1)).mean()
            mdist = core.pdist(m)
            draws[model]["VDR"][draw] = mdist.mean() / hdist.mean()
            draws[model]["CSR"][draw] = core.spearmanr(hdist, mdist).statistic
    return draws


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--draws", type=int, default=5_000)
    args = parser.parse_args()
    if args.draws < 100:
        raise ValueError("At least 100 sensitivity draws are required")
    outputs = core.validate_frozen_outputs()
    _, scores, human = core.score_outputs(outputs)
    human_wide = core.human_profiles(human)
    profiles = core.model_profiles(scores, human_wide.index)
    scores = core.attach_human_scores(scores, human_wide)
    point = {}
    for model in core.MODELS:
        w1_country = scores[scores["model"] == model].groupby("country")["w1"].mean().reindex(human_wide.index).to_numpy(float)
        tvd_country = scores[scores["model"] == model].groupby("country")["tvd"].mean().reindex(human_wide.index).to_numpy(float)
        point[model] = core.metric_values(human_wide.to_numpy(float), profiles[model].to_numpy(float), w1_country, tvd_country)

    human_draws = human_multinomial_draws(scores, human, human_wide, profiles, args.draws)
    run_draws = generation_draws(outputs, human, human_wide, args.draws)
    model_rows: list[dict] = []
    contrast_rows: list[dict] = []
    for source, draws in (
        ("human multinomial cells, fixed countries and model means", human_draws),
        ("five-generation resampling, fixed countries and human cells", run_draws),
    ):
        model, contrast = summarize(source, draws, point)
        model_rows.extend(model)
        contrast_rows.extend(contrast)
    pd.DataFrame(model_rows).to_csv(core.RESULTS / "conditional_uncertainty_estimates.csv", index=False)
    pd.DataFrame(contrast_rows).to_csv(core.RESULTS / "conditional_uncertainty_contrasts.csv", index=False)
    packed = {}
    for source_name, source_draws in (("human", human_draws), ("generation", run_draws)):
        for model in core.MODELS:
            for metric, values in source_draws[model].items():
                packed[f"{source_name}_{model.replace(' ', '_').replace('.', '')}_{metric}"] = values
    pd.DataFrame(packed).to_parquet(core.RESULTS / "conditional_uncertainty_draws.parquet", index=False)
    print(pd.DataFrame(contrast_rows).to_string(index=False))


if __name__ == "__main__":
    main()
