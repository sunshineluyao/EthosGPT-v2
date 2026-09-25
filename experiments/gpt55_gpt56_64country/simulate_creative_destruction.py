#!/usr/bin/env python3
"""Conditional quality-ladder illustration from the six archived survey gaps.

This is a deliberately assumed decision rule, not an estimate of policy effects,
national productivity, cultural values, or environmental sustainability.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ITEMS = ("Q48", "Q57", "Q106", "Q108", "Q121", "Q159")
REGIONS = ("African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
           "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia")
MODELS = ("GPT-5.5", "GPT-5.6 Sol")
FACETS = {"Q48": "agency", "Q57": "trust", "Q106": "income equality",
          "Q108": "individual provision", "Q121": "immigration contribution",
          "Q159": "science opportunity"}

SCENARIOS = (
    ("weak", .15, .10, .05, .02, True, True),
    ("illustrative", .30, .20, .10, .04, True, True),
    ("strong", .45, .30, .15, .08, True, True),
    ("omit_conflicting_Q106_Q121", .30, .20, .10, .04, False, False),
    ("no_decision_link", .0, .20, .10, .04, True, True),
)


def decisions(x: np.ndarray, b: float, use_income: bool, use_immigration: bool) -> np.ndarray:
    """Order: Q48, Q57, Q106, Q108, Q121, Q159; returns entry, aid, coordination.

    Exact six-facet rule: entry=.5+b*(agency+science-1),
    aid=.5+b*(equality-individual provision),
    coordination=.5+b*(trust+immigration-1). Omitted facets are neutral 0.5.
    These signs and coefficients are hypothetical, not inferred from the survey.
    """
    assert x.shape[-1] == 6 and np.isfinite(x).all()
    assert ((x >= 0) & (x <= 1)).all()
    agency, trust, equality, individual, immigration, science = np.moveaxis(x, -1, 0)
    if not use_income:
        equality = np.full_like(equality, .5)
    if not use_immigration:
        immigration = np.full_like(immigration, .5)
    p = np.stack([.5 + b * (agency + science - 1),
                  .5 + b * (equality - individual),
                  .5 + b * (trust + immigration - 1)], axis=-1)
    assert np.all((0 <= p) & (p <= 1)), "chosen scenario should avoid clipping"
    return p


def outcomes(p: np.ndarray, entry_coef: float, coord_coef: float, jump: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Bernoulli innovation replaces one incumbent; E[log quality gain] is exact.

    Adoption is not GDP; (1-aid)*arrival is an unassisted-transition index,
    not actual job destruction. Twenty periods have constant assumed parameters.
    """
    innovation = .05 + entry_coef * p[..., 0] + coord_coef * p[..., 2]
    assert ((innovation > 0) & (innovation < 1)).all()
    annual_log_quality = innovation * np.log1p(jump)
    uncovered_transition = innovation * (1 - p[..., 1])
    return innovation, annual_log_quality, uncovered_transition


def run(scores: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    assert len(scores) == 64 * 6 * 2
    assert set(scores.question_id) == set(ITEMS) and set(scores.model) == set(MODELS)
    assert set(scores.cultural_region) == set(REGIONS)
    assert not scores.duplicated(["country", "question_id", "model"]).any()
    cols = ["country", "country_code", "cultural_region", "model"]
    human = scores.pivot(index=cols, columns="question_id", values="human_directed")
    model = scores.pivot(index=cols, columns="question_id", values="model_directed")
    assert human.notna().all().all() and model.notna().all().all()
    human, model = human.loc[:, ITEMS], model.loc[:, ITEMS]
    assert (human.groupby(level="country").nunique() == 1).all().all()
    h, a = human.to_numpy(), model.to_numpy()
    idx = human.reset_index()[cols]
    rows: list[pd.DataFrame] = []
    for name, b, alpha, beta, jump, include_income, include_immigration in SCENARIOS:
        hp = decisions(h, b, include_income, include_immigration)
        ap = decisions(a, b, include_income, include_immigration)
        lh, gh, th = outcomes(hp, alpha, beta, jump)
        la, ga, ta = outcomes(ap, alpha, beta, jump)
        result = idx.copy()
        result["scenario"] = name
        for j, key in enumerate(("innovation_support", "transition_assistance", "coordination")):
            result[f"survey_{key}"] = hp[:, j]
            result[f"model_{key}"] = ap[:, j]
            result[f"delta_{key}"] = ap[:, j] - hp[:, j]
        result["survey_arrival_probability"] = lh
        result["model_arrival_probability"] = la
        result["delta_arrival_pp"] = 100 * (la - lh)
        result["survey_annual_log_quality"] = gh
        result["model_annual_log_quality"] = ga
        result["delta_20step_log_quality_pp"] = 100 * 20 * (ga - gh)
        result["survey_unassisted_transition"] = th
        result["model_unassisted_transition"] = ta
        result["delta_unassisted_transitions_per_100"] = 100 * (ta - th)
        rows.append(result)
    countries = pd.concat(rows, ignore_index=True)
    assert len(countries) == 64 * 2 * len(SCENARIOS)
    assert (countries[countries.scenario == "no_decision_link"].delta_20step_log_quality_pp.abs() < 1e-13).all()
    assert (countries[countries.scenario == "no_decision_link"].delta_unassisted_transitions_per_100.abs() < 1e-13).all()
    numeric = ["delta_arrival_pp", "delta_20step_log_quality_pp", "delta_unassisted_transitions_per_100"]
    regions = countries.groupby(["scenario", "model", "cultural_region"], sort=False).agg(
        countries=("country", "nunique"), **{f"mean_{k}": (k, "mean") for k in numeric}
    ).reset_index()
    global_summary = countries.groupby(["scenario", "model"], sort=False).agg(
        countries=("country", "nunique"), **{f"mean_{k}": (k, "mean") for k in numeric}
    ).reset_index()
    central = countries[countries.scenario == "illustrative"]
    facets: list[dict[str, str | float]] = []
    for name in MODELS:
        subset = (model - human).reset_index()
        subset = subset[subset.model == name]
        for q in ITEMS:
            error = subset[q].mean()
            lambda_effect_pp = 100 * .30 * ( .20 if q in ("Q48", "Q159") else .10 if q in ("Q57", "Q121") else 0 ) * error
            aid_effect_pp = 100 * .30 * (1 if q == "Q106" else -1 if q == "Q108" else 0) * error
            facets.append({"model": name, "item": q, "named_position": FACETS[q],
                           "mean_model_minus_survey_score": error,
                           "contribution_to_mean_arrival_pp": lambda_effect_pp,
                           "contribution_to_mean_assistance_pp": aid_effect_pp})
    facet_df = pd.DataFrame(facets)
    for name in MODELS:
        measured = float(central[central.model == name].delta_arrival_pp.mean())
        decomposed = facet_df[facet_df.model == name].contribution_to_mean_arrival_pp.sum()
        assert np.isclose(measured, decomposed, atol=1e-12)
    checks = pd.DataFrame({"property": ["country_count", "region_count", "question_count", "model_count", "scenario_count"],
                           "value": [64, 8, 6, 2, len(SCENARIOS)]})
    return countries, regions, global_summary, facet_df, checks


def plot(regions: pd.DataFrame, path: Path) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    central = regions[regions.scenario == "illustrative"]
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.3), sharey=True)
    fig.subplots_adjust(left=.22, right=.985, top=.83, bottom=.19, wspace=.16)
    y = np.arange(len(REGIONS))
    for ax, key, title in zip(axes,
            ("mean_delta_20step_log_quality_pp", "mean_delta_unassisted_transitions_per_100"),
            ("a  Expected log quality, 20 steps", "b  Unassisted transitions / 100, per step"), strict=True):
        for model_name, color, offset in ((MODELS[0], "#187c98", -.12), (MODELS[1], "#bd5b35", .12)):
            dat = central[central.model == model_name].set_index("cultural_region").reindex(REGIONS)
            assert dat[key].notna().all()
            ax.scatter(dat[key], y + offset, marker="o" if offset < 0 else "D", s=27,
                       label=model_name, color=color, zorder=3, edgecolors="white", linewidth=.35)
        ax.axvline(0, color="#727c87", linewidth=.85)
        ax.set_title(title, loc="left", fontsize=9, pad=10)
        ax.grid(axis="x", color="#e8edf0", linewidth=.6)
        ax.set_axisbelow(True)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.set_yticks(y, REGIONS, fontsize=7.5)
        ax.tick_params(axis="y", length=0)
    axes[0].invert_yaxis()
    axes[0].set_xlabel("Model-guided minus survey-guided (percentage points)", fontsize=7)
    axes[1].set_xlabel("Model-guided minus survey-guided (index units)", fontsize=7)
    axes[0].legend(loc="lower center", bbox_to_anchor=(1.10, 1.12), ncol=2, frameon=False, fontsize=7.5)
    for suffix in ("pdf", "svg", "png"):
        fig.savefig(path.with_suffix("." + suffix), dpi=250, metadata={"Creator": "EthosGPT conditional simulation"})
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=Path(__file__).parent / "results/country_question_scores.csv")
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).parents[2] / "results/creative_destruction")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    countries, regions, global_summary, facets, checks = run(pd.read_csv(args.scores))
    for name, data in (("country_simulation.csv", countries), ("eight_region_simulation.csv", regions),
                       ("global_scenarios.csv", global_summary), ("six_facet_contributions.csv", facets),
                       ("input_validation.csv", checks)):
        data.to_csv(args.output_dir / name, index=False, float_format="%.12g")
    plot(regions, args.output_dir / "creative_destruction_regions.pdf")
    print(global_summary.to_string(index=False))


if __name__ == "__main__":
    main()
