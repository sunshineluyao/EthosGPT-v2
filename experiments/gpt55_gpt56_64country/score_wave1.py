#!/usr/bin/env python3
"""Score and audit the 64-country GPT-5.5/GPT-5.6 API experiment.

The country is the primary independent unit. Five generations per
country-question estimate response instability; they are never treated as five
independent countries. The script produces point estimates, country-cluster
BCa intervals, randomization tests, multiplicity corrections, uncertainty
sensitivities, and spatial diagnostics from frozen model outputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Callable
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
from libpysal.weights import W
from scipy.spatial.distance import pdist
from scipy.stats import norm, rankdata, spearmanr, t
from spreg import ML_Error


ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUTPUTS = HERE / "outputs"
RESULTS = HERE / "results"
INPUTS = HERE / "inputs"
MANIFESTS = HERE / "manifests"

SEED = 20260902
MODELS = ("GPT-5.5", "GPT-5.6 Sol")
MODEL_FILES = {
    "GPT-5.5": OUTPUTS / "gpt-5.5_scores.jsonl",
    "GPT-5.6 Sol": OUTPUTS / "gpt-5.6-sol_scores.jsonl",
}
MODEL_IDS = {
    "GPT-5.5": "gpt-5.5-2026-04-23",
    "GPT-5.6 Sol": "gpt-5.6-sol",
}
QUESTION_ORDER = ("Q48", "Q57", "Q106", "Q108", "Q121", "Q159")
DOMAIN_ORDER = ("Agency", "Trust", "Distribution", "Market", "Inclusion", "Science")
EXPECTED_COUNTRIES = 64
EXPECTED_GENERATIONS = 5


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_jsonl(path: Path) -> pd.DataFrame:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON") from exc
    return pd.DataFrame(rows)


def validate_frozen_outputs() -> pd.DataFrame:
    frames = []
    for model, path in MODEL_FILES.items():
        frame = read_jsonl(path)
        if len(frame) != EXPECTED_COUNTRIES * len(QUESTION_ORDER) * EXPECTED_GENERATIONS:
            raise ValueError(f"{model}: expected 1,920 rows, found {len(frame):,}")
        if set(frame["question_id"]) != set(QUESTION_ORDER):
            raise ValueError(f"{model}: question roster differs from the frozen protocol")
        if frame["country"].nunique() != EXPECTED_COUNTRIES:
            raise ValueError(f"{model}: expected 64 countries")
        if set(frame["generation"]) != set(range(1, EXPECTED_GENERATIONS + 1)):
            raise ValueError(f"{model}: generations must be 1..5")
        counts = frame.groupby(["country", "question_id"])["generation"].nunique()
        if not (counts == EXPECTED_GENERATIONS).all() or len(counts) != 384:
            raise ValueError(f"{model}: incomplete country-question-generation blocks")
        if frame["record_key"].duplicated().any():
            raise ValueError(f"{model}: duplicate record keys")
        if set(frame["requested_model_id"]) != {MODEL_IDS[model]}:
            raise ValueError(f"{model}: requested model identifier drift")
        if set(frame["returned_model_id"]) != {MODEL_IDS[model]}:
            raise ValueError(f"{model}: returned model identifier drift")
        if set(frame["status"]) != {"valid"} or not (frame["http_status"] == 200).all():
            raise ValueError(f"{model}: invalid final response")
        if not np.allclose(frame["probability_sum"].astype(float), 1.0, atol=1e-9):
            raise ValueError(f"{model}: probability sums differ from one")
        frame = frame.copy()
        frame["model"] = model
        frames.append(frame)
    combined = pd.concat(frames, ignore_index=True)
    paired = combined.groupby(["country", "question_id", "generation"])["model"].nunique()
    if len(paired) != 1_920 or not (paired == 2).all():
        raise ValueError("Models are not complete on all 1,920 paired blocks")
    return combined


def support_probabilities(mapping: dict[str, float], scale_min: int, scale_max: int) -> np.ndarray:
    expected = [str(value) for value in range(scale_min, scale_max + 1)]
    if set(mapping) != set(expected):
        raise ValueError(f"Probability support differs from {expected}")
    values = np.asarray([float(mapping[key]) for key in expected])
    if not np.isfinite(values).all() or (values < 0).any() or not np.isclose(values.sum(), 1):
        raise ValueError("Probabilities must be finite, non-negative, and sum to one")
    return values


def w1_from_probabilities(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    """Normalized one-dimensional W1 for equally spaced ordered categories."""
    if p.shape[-1] < 2:
        return np.zeros(p.shape[:-1], dtype=float)
    return np.abs(np.cumsum(p, axis=-1)[..., :-1] - np.cumsum(q, axis=-1)[..., :-1]).sum(axis=-1) / (p.shape[-1] - 1)


def tvd_from_probabilities(p: np.ndarray, q: np.ndarray) -> np.ndarray:
    return 0.5 * np.abs(p - q).sum(axis=-1)


def score_outputs(outputs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    item_meta = pd.read_csv(ROOT / "data/metadata/item_dictionary.csv")
    meta = item_meta.set_index("question_id")
    human = pd.read_parquet(ROOT / "data/processed/human_item_distributions.parquet")
    countries = set(outputs["country"])
    human = human[human["country"].isin(countries) & human["question_id"].isin(QUESTION_ORDER)].copy()
    coverage = human.groupby(["country", "question_id"]).size().unstack()
    if coverage.shape != (EXPECTED_COUNTRIES, len(QUESTION_ORDER)) or coverage.isna().any().any():
        raise ValueError("The human comparison is not complete for all 64 x 6 cells")
    human_groups = {key: group.sort_values("score") for key, group in human.groupby(["country", "question_id"])}

    rows: list[dict] = []
    probability_rows: list[dict] = []
    for row in outputs.itertuples(index=False):
        scale_min = int(meta.loc[row.question_id, "scale_min"])
        scale_max = int(meta.loc[row.question_id, "scale_max"])
        direction = str(meta.loc[row.question_id, "direction"])
        model_p = support_probabilities(row.official_category_probabilities, scale_min, scale_max)
        h = human_groups[(row.country, row.question_id)]
        support = np.arange(scale_min, scale_max + 1)
        human_p = h.set_index("score")["probability"].reindex(support, fill_value=0).to_numpy(float)
        norm_support = (support - scale_min) / (scale_max - scale_min)
        expected_norm = float(model_p @ norm_support)
        directed = expected_norm if direction == "forward" else 1 - expected_norm
        rows.append({
            "model": row.model,
            "country": row.country,
            "country_code": int(row.country_code),
            "cultural_region": row.cultural_region,
            "question_id": row.question_id,
            "domain": row.domain,
            "generation": int(row.generation),
            "attempt": int(row.attempt),
            "w1": float(w1_from_probabilities(model_p, human_p)),
            "tvd": float(tvd_from_probabilities(model_p, human_p)),
            "model_expected_norm": expected_norm,
            "model_directed": directed,
            "human_n": int(h["n"].iloc[0]),
        })
        for category, probability in zip(support, model_p, strict=True):
            probability_rows.append({
                "model": row.model,
                "country": row.country,
                "country_code": int(row.country_code),
                "cultural_region": row.cultural_region,
                "question_id": row.question_id,
                "domain": row.domain,
                "generation": int(row.generation),
                "attempt": int(row.attempt),
                "category": int(category),
                "probability": float(probability),
            })
    generation_scores = pd.DataFrame(rows)
    long_probabilities = pd.DataFrame(probability_rows)

    ensemble_prob = (
        long_probabilities.groupby(
            ["model", "country", "country_code", "cultural_region", "question_id", "domain", "category"],
            as_index=False,
        )["probability"].mean()
    )
    ensemble_rows: list[dict] = []
    for key, group in ensemble_prob.groupby(["model", "country", "country_code", "cultural_region", "question_id", "domain"]):
        model, country, country_code, region, question_id, domain = key
        scale_min = int(meta.loc[question_id, "scale_min"])
        scale_max = int(meta.loc[question_id, "scale_max"])
        direction = str(meta.loc[question_id, "direction"])
        support = np.arange(scale_min, scale_max + 1)
        model_p = group.set_index("category")["probability"].reindex(support).to_numpy(float)
        h = human_groups[(country, question_id)]
        human_p = h.set_index("score")["probability"].reindex(support, fill_value=0).to_numpy(float)
        norm_support = (support - scale_min) / (scale_max - scale_min)
        expected_norm = float(model_p @ norm_support)
        ensemble_rows.append({
            "model": model,
            "country": country,
            "country_code": int(country_code),
            "cultural_region": region,
            "question_id": question_id,
            "domain": domain,
            "generations": EXPECTED_GENERATIONS,
            "w1": float(w1_from_probabilities(model_p, human_p)),
            "tvd": float(tvd_from_probabilities(model_p, human_p)),
            "model_expected_norm": expected_norm,
            "model_directed": expected_norm if direction == "forward" else 1 - expected_norm,
            "human_n": int(h["n"].iloc[0]),
            "model_probabilities": json.dumps({str(int(k)): float(v) for k, v in zip(support, model_p, strict=True)}, sort_keys=True),
        })
    return generation_scores, pd.DataFrame(ensemble_rows), human


def human_profiles(human: pd.DataFrame) -> pd.DataFrame:
    item_meta = pd.read_csv(ROOT / "data/metadata/item_dictionary.csv")
    frame = human.merge(item_meta[["question_id", "domain", "direction", "scale_min", "scale_max"]], on="question_id", validate="many_to_one")
    frame["norm"] = (frame["score"] - frame["scale_min"]) / (frame["scale_max"] - frame["scale_min"])
    frame["directed"] = np.where(frame["direction"] == "forward", frame["norm"], 1 - frame["norm"])
    values = (
        frame.assign(weighted=lambda x: x["directed"] * x["probability"])
        .groupby(["country", "domain"], as_index=False)["weighted"].sum()
    )
    wide = values.pivot(index="country", columns="domain", values="weighted").reindex(columns=DOMAIN_ORDER)
    if wide.shape != (EXPECTED_COUNTRIES, len(DOMAIN_ORDER)) or wide.isna().any().any():
        raise ValueError("Human profiles must be complete 64 x 6")
    return wide.sort_index()


def model_profiles(scores: pd.DataFrame, countries: pd.Index) -> dict[str, pd.DataFrame]:
    profiles = {}
    for model in MODELS:
        wide = scores[scores["model"] == model].pivot(index="country", columns="domain", values="model_directed")
        wide = wide.reindex(index=countries, columns=DOMAIN_ORDER)
        if wide.isna().any().any():
            raise ValueError(f"{model}: incomplete model profile")
        profiles[model] = wide
    return profiles


def metric_values(h: np.ndarray, m: np.ndarray, w1_country: np.ndarray, tvd_country: np.ndarray) -> dict[str, float]:
    sigma = h.std(axis=0, ddof=1)
    if (sigma <= 0).any():
        raise ValueError("A human profile dimension has zero cross-country variation")
    crg = np.sqrt(np.square((m - h) / sigma).mean(axis=1)).mean()
    hdist = pdist(h)
    mdist = pdist(m)
    csr = float(spearmanr(hdist, mdist).statistic)
    return {
        "W1": float(w1_country.mean()),
        "TVD": float(tvd_country.mean()),
        "CRG": float(crg),
        "VDR": float(mdist.mean() / hdist.mean()),
        "CSR": csr,
    }


def metric_loss(metric: str, value: float) -> float:
    if metric in {"W1", "TVD", "CRG"}:
        return value
    if metric == "VDR":
        return abs(value - 1.0)
    if metric == "CSR":
        return 1.0 - value
    raise KeyError(metric)


def bca_interval(draws: np.ndarray, estimate: float, jackknife: np.ndarray, alpha: float = 0.05) -> tuple[float, float]:
    draws = np.asarray(draws, float)
    draws = draws[np.isfinite(draws)]
    jackknife = np.asarray(jackknife, float)
    jackknife = jackknife[np.isfinite(jackknife)]
    if len(draws) < 100 or len(jackknife) < 3:
        return tuple(np.quantile(draws, [alpha / 2, 1 - alpha / 2]))
    prop = np.clip((np.sum(draws < estimate) + 0.5 * np.sum(draws == estimate)) / len(draws), 1 / (2 * len(draws)), 1 - 1 / (2 * len(draws)))
    z0 = norm.ppf(prop)
    mean_j = jackknife.mean()
    diffs = mean_j - jackknife
    denom = 6 * np.power(np.square(diffs).sum(), 1.5)
    acceleration = float(np.power(diffs, 3).sum() / denom) if denom > 0 else 0.0
    adjusted = []
    for probability in (alpha / 2, 1 - alpha / 2):
        z = norm.ppf(probability)
        adjusted.append(norm.cdf(z0 + (z0 + z) / (1 - acceleration * (z0 + z))))
    adjusted = np.clip(adjusted, 0, 1)
    return tuple(np.quantile(draws, adjusted))


def holm_adjust(pvalues: np.ndarray) -> np.ndarray:
    pvalues = np.asarray(pvalues, float)
    order = np.argsort(pvalues)
    adjusted = np.empty(len(pvalues), float)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (len(pvalues) - rank) * pvalues[idx])
        adjusted[idx] = min(running, 1.0)
    return adjusted


def bh_adjust(pvalues: np.ndarray) -> np.ndarray:
    pvalues = np.asarray(pvalues, float)
    order = np.argsort(pvalues)
    adjusted = np.empty(len(pvalues), float)
    running = 1.0
    for rank in range(len(pvalues) - 1, -1, -1):
        idx = order[rank]
        running = min(running, pvalues[idx] * len(pvalues) / (rank + 1))
        adjusted[idx] = min(running, 1.0)
    return adjusted


def signflip_test(values: np.ndarray, permutations: int, rng: np.random.Generator) -> tuple[float, float]:
    values = np.asarray(values, float)
    observed = float(values.mean())
    extreme = 0
    completed = 0
    batch_size = 10_000
    while completed < permutations:
        size = min(batch_size, permutations - completed)
        signs = rng.choice(np.array([-1.0, 1.0]), size=(size, len(values)))
        null = (signs * values).mean(axis=1)
        extreme += int(np.sum(np.abs(null) >= abs(observed) - 1e-15))
        completed += size
    p = (extreme + 1) / (permutations + 1)
    return float(p), float(math.sqrt(p * (1 - p) / (permutations + 1)))


def build_core_inference(scores: pd.DataFrame, human_wide: pd.DataFrame, profiles: dict[str, pd.DataFrame], bootstrap_draws: int, permutations: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = human_wide.index
    h = human_wide.to_numpy(float)
    model_arrays = {model: profiles[model].to_numpy(float) for model in MODELS}
    w1_country = {
        model: scores[scores["model"] == model].groupby("country")["w1"].mean().reindex(countries).to_numpy(float)
        for model in MODELS
    }
    tvd_country = {
        model: scores[scores["model"] == model].groupby("country")["tvd"].mean().reindex(countries).to_numpy(float)
        for model in MODELS
    }
    point = {model: metric_values(h, model_arrays[model], w1_country[model], tvd_country[model]) for model in MODELS}

    rng = np.random.default_rng(SEED)
    indices = rng.integers(0, len(countries), size=(bootstrap_draws, len(countries)))
    boot = {model: {metric: np.empty(bootstrap_draws) for metric in point[model]} for model in MODELS}
    for draw, idx in enumerate(indices):
        hb = h[idx]
        for model in MODELS:
            values = metric_values(hb, model_arrays[model][idx], w1_country[model][idx], tvd_country[model][idx])
            for metric, value in values.items():
                boot[model][metric][draw] = value

    jack = {model: {metric: [] for metric in point[model]} for model in MODELS}
    for omitted in range(len(countries)):
        keep = np.delete(np.arange(len(countries)), omitted)
        for model in MODELS:
            values = metric_values(h[keep], model_arrays[model][keep], w1_country[model][keep], tvd_country[model][keep])
            for metric, value in values.items():
                jack[model][metric].append(value)

    estimate_rows = []
    for model in MODELS:
        for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
            low, high = bca_interval(boot[model][metric], point[model][metric], np.asarray(jack[model][metric]))
            estimate_rows.append({
                "model": model,
                "metric": metric,
                "estimate": point[model][metric],
                "standard_error": float(np.std(boot[model][metric], ddof=1)),
                "ci_low_bca": low,
                "ci_high_bca": high,
                "countries": len(countries),
                "country_bootstrap_draws": bootstrap_draws,
                "target": 1.0 if metric in {"VDR", "CSR"} else 0.0,
            })

    # Leave-one-country-out values for transparent influence diagnostics.
    loo_rows = []
    for omitted, country in enumerate(countries):
        keep = np.delete(np.arange(len(countries)), omitted)
        values = {
            model: metric_values(h[keep], model_arrays[model][keep], w1_country[model][keep], tvd_country[model][keep])
            for model in MODELS
        }
        row = {"omitted_country": country, "countries_retained": len(keep)}
        for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
            row[f"delta_loss_{metric.lower()}"] = metric_loss(metric, values[MODELS[1]][metric]) - metric_loss(metric, values[MODELS[0]][metric])
        loo_rows.append(row)

    comparison_rows = []
    linear_differences = {
        "W1": w1_country[MODELS[1]] - w1_country[MODELS[0]],
        "TVD": tvd_country[MODELS[1]] - tvd_country[MODELS[0]],
    }
    sigma = h.std(axis=0, ddof=1)
    crg_country = {
        model: np.sqrt(np.square((model_arrays[model] - h) / sigma).mean(axis=1))
        for model in MODELS
    }
    linear_differences["CRG"] = crg_country[MODELS[1]] - crg_country[MODELS[0]]
    permutation_rng = np.random.default_rng(SEED + 101)
    for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
        estimate = metric_loss(metric, point[MODELS[1]][metric]) - metric_loss(metric, point[MODELS[0]][metric])
        draws = np.asarray([metric_loss(metric, b) for b in boot[MODELS[1]][metric]]) - np.asarray([metric_loss(metric, b) for b in boot[MODELS[0]][metric]])
        jack_delta = np.asarray([metric_loss(metric, b) for b in jack[MODELS[1]][metric]]) - np.asarray([metric_loss(metric, b) for b in jack[MODELS[0]][metric]])
        low, high = bca_interval(draws, estimate, jack_delta)
        if metric in linear_differences:
            p, mcse = signflip_test(linear_differences[metric], permutations, permutation_rng)
        else:
            # Swap the two model profiles independently within country. This is
            # the randomization analogue for nonlinear VDR and CSR losses.
            extreme = 0
            observed_abs = abs(estimate)
            for _ in range(permutations):
                swap = permutation_rng.integers(0, 2, len(countries)).astype(bool)
                first = model_arrays[MODELS[0]].copy()
                second = model_arrays[MODELS[1]].copy()
                first[swap], second[swap] = second[swap], first[swap].copy()
                first_values = metric_values(h, first, w1_country[MODELS[0]], tvd_country[MODELS[0]])
                second_values = metric_values(h, second, w1_country[MODELS[1]], tvd_country[MODELS[1]])
                null_delta = metric_loss(metric, second_values[metric]) - metric_loss(metric, first_values[metric])
                extreme += int(abs(null_delta) >= observed_abs - 1e-15)
            p = (extreme + 1) / (permutations + 1)
            mcse = math.sqrt(p * (1 - p) / (permutations + 1))
        comparison_rows.append({
            "metric": metric,
            "estimand": "loss(GPT-5.6 Sol) - loss(GPT-5.5)",
            "estimate": estimate,
            "standard_error": float(np.std(draws, ddof=1)),
            "ci_low_bca": low,
            "ci_high_bca": high,
            "permutation_p_two_sided": p,
            "permutation_p_mcse": mcse,
            "permutations": permutations,
            "interpretation_if_negative": "GPT-5.6 Sol closer to the metric target",
        })
    comparison = pd.DataFrame(comparison_rows)
    comparison["holm_p_five_metrics"] = holm_adjust(comparison["permutation_p_two_sided"].to_numpy())

    draw_frame = pd.DataFrame({
        f"{model.replace(' ', '_').replace('.', '')}_{metric}": boot[model][metric]
        for model in MODELS for metric in ("W1", "TVD", "CRG", "VDR", "CSR")
    })
    return pd.DataFrame(estimate_rows), comparison, pd.DataFrame(loo_rows), draw_frame


def build_domain_inference(scores: pd.DataFrame, bootstrap_draws: int, permutations: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    countries = sorted(scores["country"].unique())
    rng = np.random.default_rng(SEED + 202)
    indices = rng.integers(0, len(countries), size=(bootstrap_draws, len(countries)))
    permutation_rng = np.random.default_rng(SEED + 203)
    rows = []
    bias_rows = []
    for metric in ("w1", "tvd"):
        family_indices = []
        family_p = []
        for domain in DOMAIN_ORDER:
            arrays = {}
            for model in MODELS:
                arrays[model] = scores[(scores["model"] == model) & (scores["domain"] == domain)].set_index("country")[metric].reindex(countries).to_numpy(float)
            delta = arrays[MODELS[1]] - arrays[MODELS[0]]
            boot_delta = delta[indices].mean(axis=1)
            jack = np.asarray([np.delete(delta, i).mean() for i in range(len(countries))])
            low, high = bca_interval(boot_delta, float(delta.mean()), jack)
            p, mcse = signflip_test(delta, permutations, permutation_rng)
            row = {
                "domain": domain,
                "question_id": scores[scores["domain"] == domain]["question_id"].iloc[0],
                "metric": metric.upper(),
                "gpt55_estimate": float(arrays[MODELS[0]].mean()),
                "gpt55_se": float(arrays[MODELS[0]][indices].mean(axis=1).std(ddof=1)),
                "gpt56_estimate": float(arrays[MODELS[1]].mean()),
                "gpt56_se": float(arrays[MODELS[1]][indices].mean(axis=1).std(ddof=1)),
                "delta_56_minus_55": float(delta.mean()),
                "delta_se": float(boot_delta.std(ddof=1)),
                "ci_low_bca": low,
                "ci_high_bca": high,
                "permutation_p_two_sided": p,
                "permutation_p_mcse": mcse,
                "countries": len(countries),
                "country_bootstrap_draws": bootstrap_draws,
                "permutations": permutations,
            }
            rows.append(row)
            family_indices.append(len(rows) - 1)
            family_p.append(p)
        adjusted = holm_adjust(np.asarray(family_p))
        for idx, value in zip(family_indices, adjusted, strict=True):
            rows[idx]["holm_p_within_metric"] = value

    for model in MODELS:
        family_indices = []
        family_p = []
        for domain in DOMAIN_ORDER:
            frame = scores[(scores["model"] == model) & (scores["domain"] == domain)].set_index("country").reindex(countries)
            # Human directed score is attached by build_signed_bias before this function.
            values = frame["signed_bias"].to_numpy(float)
            boot = values[indices].mean(axis=1)
            jack = np.asarray([np.delete(values, i).mean() for i in range(len(countries))])
            low, high = bca_interval(boot, float(values.mean()), jack)
            p, mcse = signflip_test(values, permutations, permutation_rng)
            bias_rows.append({
                "model": model,
                "domain": domain,
                "question_id": frame["question_id"].iloc[0],
                "mean_signed_bias": float(values.mean()),
                "standard_error": float(boot.std(ddof=1)),
                "ci_low_bca": low,
                "ci_high_bca": high,
                "permutation_p_two_sided": p,
                "permutation_p_mcse": mcse,
                "countries": len(countries),
            })
            family_indices.append(len(bias_rows) - 1)
            family_p.append(p)
        adjusted = holm_adjust(np.asarray(family_p))
        for idx, value in zip(family_indices, adjusted, strict=True):
            bias_rows[idx]["holm_p_within_model"] = value
    return pd.DataFrame(rows), pd.DataFrame(bias_rows)


def attach_human_scores(scores: pd.DataFrame, human_wide: pd.DataFrame) -> pd.DataFrame:
    frame = scores.copy()
    lookup = human_wide.stack().rename("human_directed")
    frame = frame.merge(lookup.reset_index(), on=["country", "domain"], validate="many_to_one")
    frame["signed_bias"] = frame["model_directed"] - frame["human_directed"]
    return frame


MANUAL_COORDINATES = {
    "Andorra": (42.5063, 1.5218),
    "Hong Kong SAR": (22.3193, 114.1694),
    "Macau SAR": (22.1987, 113.5439),
    "Maldives": (3.2028, 73.2207),
    "Northern Ireland": (54.7877, -6.4923),
    "Singapore": (1.3521, 103.8198),
}


def build_coordinates(country_meta: pd.DataFrame) -> pd.DataFrame:
    path = Path(gpd.__file__).resolve().parent / "datasets/naturalearth_lowres/naturalearth_lowres.shp"
    world = gpd.read_file(path).to_crs("ESRI:54009")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        points = world.geometry.centroid
    centroids = gpd.GeoDataFrame(world[["name"]].copy(), geometry=points, crs="ESRI:54009").to_crs("EPSG:4326")
    natural = {row.name: (float(row.geometry.y), float(row.geometry.x)) for row in centroids.itertuples(index=False)}
    aliases = {"Great Britain": "United Kingdom", "United States": "United States of America", "Taiwan ROC": "Taiwan"}
    rows = []
    for row in country_meta.drop_duplicates("country").sort_values("country").itertuples(index=False):
        country = row.country
        if country in MANUAL_COORDINATES:
            latitude, longitude = MANUAL_COORDINATES[country]
            source = "manual geographic center for Natural Earth-omitted survey entity"
        else:
            name = aliases.get(country, country)
            if name not in natural:
                raise KeyError(f"No coordinate for {country} ({name})")
            latitude, longitude = natural[name]
            source = "Natural Earth low-resolution equal-area polygon centroid"
        rows.append({
            "country": country,
            "country_code": int(row.country_code),
            "cultural_region": row.cultural_region,
            "latitude": latitude,
            "longitude": longitude,
            "coordinate_source": source,
        })
    return pd.DataFrame(rows)


def haversine_matrix(coordinates: pd.DataFrame) -> np.ndarray:
    lat = np.radians(coordinates["latitude"].to_numpy(float))
    lon = np.radians(coordinates["longitude"].to_numpy(float))
    dlat = lat[:, None] - lat[None, :]
    dlon = lon[:, None] - lon[None, :]
    a = np.sin(dlat / 2) ** 2 + np.cos(lat[:, None]) * np.cos(lat[None, :]) * np.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def knn_weights(distance: np.ndarray, k: int) -> tuple[np.ndarray, W]:
    n = len(distance)
    adjacency = np.zeros((n, n), float)
    nearest = np.argsort(distance, axis=1)[:, 1 : k + 1]
    for i in range(n):
        adjacency[i, nearest[i]] = 1.0
    adjacency = np.maximum(adjacency, adjacency.T)
    adjacency /= adjacency.sum(axis=1, keepdims=True)
    neighbors = {i: list(np.flatnonzero(adjacency[i])) for i in range(n)}
    weights = {i: [float(adjacency[i, j]) for j in neighbors[i]] for i in range(n)}
    lib_weight = W(neighbors, weights, silence_warnings=True)
    lib_weight.transform = "R"
    return adjacency, lib_weight


def moran_geary(values: np.ndarray, matrix: np.ndarray, permutation_indices: np.ndarray) -> dict[str, float]:
    x = np.asarray(values, float)
    z = x - x.mean()
    denom = float(z @ z)
    n = len(x)
    s0 = float(matrix.sum())
    moran = n / s0 * float(z @ matrix @ z) / denom
    row_sum = matrix.sum(axis=1)
    col_sum = matrix.sum(axis=0)
    numerator = float((x * x * row_sum).sum() + (x * x * col_sum).sum() - 2 * x @ matrix @ x)
    geary = (n - 1) / (2 * s0) * numerator / denom
    permuted = z[permutation_indices]
    cross = np.einsum("bi,ij,bj->b", permuted, matrix, permuted, optimize=True)
    moran_null = n / s0 * cross / denom
    xp = x[permutation_indices]
    numerator_null = (xp * xp * row_sum).sum(axis=1) + (xp * xp * col_sum).sum(axis=1) - 2 * np.einsum("bi,ij,bj->b", xp, matrix, xp, optimize=True)
    geary_null = (n - 1) / (2 * s0) * numerator_null / denom
    expected_moran = -1 / (n - 1)
    p_moran = (1 + np.sum(np.abs(moran_null - expected_moran) >= abs(moran - expected_moran) - 1e-15)) / (len(permutation_indices) + 1)
    p_geary = (1 + np.sum(np.abs(geary_null - 1) >= abs(geary - 1) - 1e-15)) / (len(permutation_indices) + 1)
    return {
        "moran_i": moran,
        "moran_expected": expected_moran,
        "moran_p_two_sided": float(p_moran),
        "moran_p_mcse": float(math.sqrt(p_moran * (1 - p_moran) / (len(permutation_indices) + 1))),
        "geary_c": geary,
        "geary_expected": 1.0,
        "geary_p_two_sided": float(p_geary),
        "geary_p_mcse": float(math.sqrt(p_geary * (1 - p_geary) / (len(permutation_indices) + 1))),
    }


def build_spatial_analysis(scores: pd.DataFrame, human_wide: pd.DataFrame, profiles: dict[str, pd.DataFrame], spatial_permutations: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    countries = human_wide.index
    country_meta = scores[["country", "country_code", "cultural_region"]].drop_duplicates().set_index("country").reindex(countries).reset_index()
    coordinates = build_coordinates(country_meta)
    coordinates = coordinates.set_index("country").reindex(countries).reset_index()
    distance = haversine_matrix(coordinates)
    permutation_rng = np.random.default_rng(SEED + 404)
    permutation_indices = np.asarray([permutation_rng.permutation(len(countries)) for _ in range(spatial_permutations)])

    sigma = human_wide.to_numpy(float).std(axis=0, ddof=1)
    variables: list[tuple[str, str, str, np.ndarray]] = []
    for model in MODELS:
        overall_w1 = scores[scores["model"] == model].groupby("country")["w1"].mean().reindex(countries).to_numpy(float)
        overall_tvd = scores[scores["model"] == model].groupby("country")["tvd"].mean().reindex(countries).to_numpy(float)
        crg = np.sqrt(np.square((profiles[model].to_numpy(float) - human_wide.to_numpy(float)) / sigma).mean(axis=1))
        variables.extend([
            ("overall_error", "W1", model, overall_w1),
            ("overall_error", "TVD", model, overall_tvd),
            ("profile_error", "CRG", model, crg),
        ])
        for domain in DOMAIN_ORDER:
            values = scores[(scores["model"] == model) & (scores["domain"] == domain)].set_index("country")["signed_bias"].reindex(countries).to_numpy(float)
            variables.append(("signed_bias", domain, model, values))
    # Version contrasts retain sign for signed bias and use raw differences for error metrics.
    for family, outcome in (("overall_error", "W1"), ("overall_error", "TVD"), ("profile_error", "CRG")):
        first = next(v for f, o, m, v in variables if f == family and o == outcome and m == MODELS[0])
        second = next(v for f, o, m, v in variables if f == family and o == outcome and m == MODELS[1])
        variables.append((family, outcome, "GPT-5.6 Sol minus GPT-5.5", second - first))
    for domain in DOMAIN_ORDER:
        first = next(v for f, o, m, v in variables if f == "signed_bias" and o == domain and m == MODELS[0])
        second = next(v for f, o, m, v in variables if f == "signed_bias" and o == domain and m == MODELS[1])
        variables.append(("signed_bias", domain, "GPT-5.6 Sol minus GPT-5.5", second - first))

    diagnostic_rows = []
    sem_rows = []
    for k in (4, 6, 8):
        matrix, lib_weight = knn_weights(distance, k)
        for family, outcome, model, values in variables:
            result = moran_geary(values, matrix, permutation_indices)
            diagnostic_rows.append({
                "outcome_family": family,
                "outcome": outcome,
                "model_or_contrast": model,
                "knn_k": k,
                "countries": len(countries),
                "spatial_permutations": spatial_permutations,
                **result,
            })
        # Intercept-only spatial-error models quantify mean W1 and TVD version
        # contrasts while allowing spatially correlated residuals. They are
        # robustness models, not causal spillover specifications.
        outcomes: list[tuple[str, str, np.ndarray]] = []
        for metric in ("w1", "tvd"):
            for domain in DOMAIN_ORDER:
                values = {}
                for model in MODELS:
                    values[model] = scores[(scores["model"] == model) & (scores["domain"] == domain)].set_index("country")[metric].reindex(countries).to_numpy(float)
                outcomes.append((metric.upper(), domain, values[MODELS[1]] - values[MODELS[0]]))
            overall_values = {
                model: scores[scores["model"] == model].groupby("country")[metric].mean().reindex(countries).to_numpy(float)
                for model in MODELS
            }
            outcomes.append((metric.upper(), "All six anchors", overall_values[MODELS[1]] - overall_values[MODELS[0]]))
        for metric, label, y in outcomes:
            try:
                fitted = ML_Error(y.reshape(-1, 1), np.ones((len(y), 1)), w=lib_weight, name_y=label, name_x=["constant"])
                coefficient = float(fitted.betas[0, 0])
                coefficient_se = float(fitted.std_err[0])
                coefficient_z, coefficient_p = fitted.z_stat[0]
                lambda_value = float(fitted.lam)
                lambda_se = float(fitted.std_err[-1])
                lambda_z, lambda_p = fitted.z_stat[-1]
                sem_rows.append({
                    "metric": metric,
                    "scope": label,
                    "knn_k": k,
                    "countries": len(countries),
                    "mean_delta": coefficient,
                    "mean_delta_w1": coefficient if metric == "W1" else np.nan,
                    "standard_error": coefficient_se,
                    "z_value": float(coefficient_z),
                    "p_value_two_sided": float(coefficient_p),
                    "ci_low_95": coefficient - norm.ppf(0.975) * coefficient_se,
                    "ci_high_95": coefficient + norm.ppf(0.975) * coefficient_se,
                    "spatial_error_lambda": lambda_value,
                    "lambda_standard_error": lambda_se,
                    "lambda_z_value": float(lambda_z),
                    "lambda_p_value_two_sided": float(lambda_p),
                    "estimator": "maximum-likelihood spatial error; intercept only",
                })
            except Exception as exc:
                sem_rows.append({"metric": metric, "scope": label, "knn_k": k, "countries": len(countries), "estimator": "FAILED", "failure": str(exc)})

    diagnostics = pd.DataFrame(diagnostic_rows)
    primary = diagnostics["knn_k"] == 4
    diagnostics.loc[primary, "moran_bh_q_primary_family"] = bh_adjust(diagnostics.loc[primary, "moran_p_two_sided"].to_numpy())
    diagnostics.loc[primary, "geary_bh_q_primary_family"] = bh_adjust(diagnostics.loc[primary, "geary_p_two_sided"].to_numpy())
    sem = pd.DataFrame(sem_rows)
    for k in (4, 6, 8):
        mask = sem["knn_k"] == k
        if "p_value_two_sided" in sem:
            valid = mask & sem["p_value_two_sided"].notna()
            sem.loc[valid, "holm_p_fourteen_scopes"] = holm_adjust(sem.loc[valid, "p_value_two_sided"].to_numpy())
            for metric in ("W1", "TVD"):
                metric_valid = valid & (sem["metric"] == metric)
                sem.loc[metric_valid, "holm_p_seven_scopes"] = holm_adjust(
                    sem.loc[metric_valid, "p_value_two_sided"].to_numpy()
                )
    return coordinates, diagnostics, sem


def build_run_stability(generation_scores: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in MODELS:
        frame = generation_scores[generation_scores["model"] == model]
        for domain in ("All six anchors", *DOMAIN_ORDER):
            subset = frame if domain == "All six anchors" else frame[frame["domain"] == domain]
            cell_sd = subset.groupby(["country", "question_id"])[["w1", "tvd", "model_directed"]].std(ddof=1)
            rows.append({
                "model": model,
                "scope": domain,
                "country_question_cells": len(cell_sd),
                "generations_per_cell": EXPECTED_GENERATIONS,
                "mean_within_cell_sd_w1": float(cell_sd["w1"].mean()),
                "median_within_cell_sd_w1": float(cell_sd["w1"].median()),
                "mean_within_cell_sd_tvd": float(cell_sd["tvd"].mean()),
                "mean_within_cell_sd_directed_score": float(cell_sd["model_directed"].mean()),
            })
    return pd.DataFrame(rows)


def bootstrap_convergence(draws: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for column in draws:
        full = draws[column].dropna().to_numpy(float)
        for used in (1_000, 5_000, 10_000, len(full)):
            if used > len(full):
                continue
            low, high = np.quantile(full[:used], [0.025, 0.975])
            rows.append({"quantity": column, "draws_used": used, "percentile_ci_low": low, "percentile_ci_high": high})
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bootstrap-draws", type=int, default=20_000)
    parser.add_argument("--permutations", type=int, default=19_999)
    parser.add_argument("--spatial-permutations", type=int, default=9_999)
    args = parser.parse_args()
    if min(args.bootstrap_draws, args.permutations, args.spatial_permutations) < 99:
        raise ValueError("All resampling counts must be at least 99")
    RESULTS.mkdir(parents=True, exist_ok=True)
    INPUTS.mkdir(parents=True, exist_ok=True)
    MANIFESTS.mkdir(parents=True, exist_ok=True)

    outputs = validate_frozen_outputs()
    generation_scores, scores, human = score_outputs(outputs)
    human_wide = human_profiles(human)
    profiles = model_profiles(scores, human_wide.index)
    scores = attach_human_scores(scores, human_wide)

    estimates, comparisons, loo, boot_draws = build_core_inference(
        scores, human_wide, profiles, args.bootstrap_draws, args.permutations
    )
    domain, signed_bias = build_domain_inference(scores, args.bootstrap_draws, args.permutations)
    coordinates, spatial, spatial_error = build_spatial_analysis(scores, human_wide, profiles, args.spatial_permutations)
    stability = build_run_stability(generation_scores)
    convergence = bootstrap_convergence(boot_draws)

    generation_scores.to_csv(RESULTS / "generation_scores.csv", index=False)
    scores.to_csv(RESULTS / "country_question_scores.csv", index=False)
    estimates.to_csv(RESULTS / "metric_estimates.csv", index=False)
    comparisons.to_csv(RESULTS / "metric_comparisons.csv", index=False)
    domain.to_csv(RESULTS / "domain_comparisons.csv", index=False)
    signed_bias.to_csv(RESULTS / "signed_bias_inference.csv", index=False)
    loo.to_csv(RESULTS / "leave_one_country_out.csv", index=False)
    boot_draws.to_parquet(RESULTS / "country_bootstrap_draws.parquet", index=False)
    convergence.to_csv(RESULTS / "bootstrap_convergence.csv", index=False)
    coordinates.to_csv(INPUTS / "country_coordinates.csv", index=False)
    spatial.to_csv(RESULTS / "spatial_diagnostics.csv", index=False)
    spatial_error.to_csv(RESULTS / "spatial_error_models.csv", index=False)
    stability.to_csv(RESULTS / "run_stability.csv", index=False)

    retry_summary = (
        outputs.groupby(["model", "attempt"]).size().rename("records").reset_index().to_dict(orient="records")
    )
    usage_rows = []
    for model in MODELS:
        subset = outputs[outputs["model"] == model]
        usage_rows.append({
            "model": model,
            "input_tokens": int(sum(x["input_tokens"] for x in subset["usage"])),
            "output_tokens": int(sum(x["output_tokens"] for x in subset["usage"])),
            "reasoning_tokens": int(sum(x["output_tokens_details"].get("reasoning_tokens", 0) for x in subset["usage"])),
            "total_tokens": int(sum(x["total_tokens"] for x in subset["usage"])),
        })
    pd.DataFrame(usage_rows).to_csv(RESULTS / "token_usage.csv", index=False)

    manifest = {
        "protocol_id": str(outputs["protocol_id"].iloc[0]),
        "prompt_set_sha256": "d8673796bd2bdb9e7259d1548287e988d010942c808aa8d5f555735ec4a0cc73",
        "analysis_seed": SEED,
        "models": MODEL_IDS,
        "records": {model: int((outputs["model"] == model).sum()) for model in MODELS},
        "countries": EXPECTED_COUNTRIES,
        "questions": list(QUESTION_ORDER),
        "generations_per_country_question": EXPECTED_GENERATIONS,
        "primary_analysis_unit": "country",
        "country_bootstrap_draws": args.bootstrap_draws,
        "randomization_permutations": args.permutations,
        "spatial_permutations": args.spatial_permutations,
        "interval": "95% bias-corrected and accelerated country-cluster bootstrap",
        "multiplicity": "Holm within the five global metrics and within each six-domain family; BH for primary spatial diagnostic family",
        "spatial_weight_primary": "symmetric 4-nearest-neighbor graph from great-circle distances, row-standardized",
        "spatial_weight_sensitivity": [6, 8],
        "temporal_boundary": "Two model versions do not identify a temporal panel; spatial tests are cross-sectional version-contrast diagnostics.",
        "retry_summary": retry_summary,
        "frozen_output_sha256": {model: sha256(path) for model, path in MODEL_FILES.items()},
        "human_sampling_boundary": "Country-item distributions are unweighted public derivative cells; resampling cannot recover unavailable survey weights or provenance.",
    }
    (MANIFESTS / "analysis_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print("\nGlobal metric estimates")
    print(estimates.to_string(index=False))
    print("\nGPT-5.6 Sol minus GPT-5.5 target-loss contrasts")
    print(comparisons.to_string(index=False))
    print("\nDomain contrasts")
    print(domain.to_string(index=False))
    print("\nPrimary k=4 spatial diagnostics with BH q < .10")
    flagged = spatial[(spatial["knn_k"] == 4) & (spatial["moran_bh_q_primary_family"].fillna(1) < .10)]
    print(flagged.to_string(index=False) if len(flagged) else "None")


if __name__ == "__main__":
    main()
