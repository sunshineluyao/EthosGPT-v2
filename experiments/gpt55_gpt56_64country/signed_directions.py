#!/usr/bin/env python3
"""Describe country and original eight-region signed survey-score gaps.

Input is the released five-generation country-question score CSV. All group
means weight countries equally. No unverified survey weights are introduced.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import TwoSlopeNorm
import numpy as np
import pandas as pd
from matplotlib.patches import FancyBboxPatch

ITEMS = ("Q48", "Q57", "Q106", "Q108", "Q121", "Q159")
SHORT = ("Agency", "Trust", "Equality", "Self-provision", "Immigration", "Science")
MODELS = ("GPT-5.5", "GPT-5.6 Sol")
REGIONS = ("African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
           "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia")


def compute(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    assert len(frame) == 64 * 6 * 2
    assert set(frame.question_id) == set(ITEMS)
    assert set(frame.cultural_region) == set(REGIONS)
    assert set(frame.model) == set(MODELS)
    assert not frame.duplicated(["model", "country", "question_id"]).any()
    assert np.allclose(frame.signed_bias, frame.model_directed - frame.human_directed)
    base = frame[frame.model == MODELS[0]].copy()
    updated = frame[frame.model == MODELS[1]].copy()
    joined = base.merge(updated, on=["country", "country_code", "cultural_region", "question_id"],
                        suffixes=("_55", "_56"), validate="one_to_one")
    countries = joined[["country", "country_code", "cultural_region", "question_id",
                        "human_directed_55", "signed_bias_55", "signed_bias_56"]].copy()
    countries = countries.rename(columns={"human_directed_55": "human_directed"})
    assert np.allclose(joined.human_directed_55, joined.human_directed_56)
    countries["delta_signed_bias_56_minus_55"] = countries.signed_bias_56 - countries.signed_bias_55
    countries["delta_tvd_56_minus_55"] = joined.tvd_56 - joined.tvd_55
    countries["delta_w1_56_minus_55"] = joined.w1_56 - joined.w1_55
    countries = countries.sort_values(["cultural_region", "country", "question_id"])
    group = countries.groupby(["cultural_region", "question_id"], sort=False)
    regions = group.agg(countries=("country", "nunique"),
                        mean_bias_55=("signed_bias_55", "mean"),
                        mean_bias_56=("signed_bias_56", "mean"),
                        mean_delta_bias=("delta_signed_bias_56_minus_55", "mean"),
                        positive_countries_56=("signed_bias_56", lambda s: int((s > 0).sum())),
                        mean_delta_tvd=("delta_tvd_56_minus_55", "mean")).reset_index()
    global_means = countries.groupby("question_id", sort=False).agg(
        countries=("country", "nunique"),
        mean_bias_55=("signed_bias_55", "mean"),
        mean_bias_56=("signed_bias_56", "mean"),
        mean_delta_bias=("delta_signed_bias_56_minus_55", "mean"),
        positive_countries_56=("signed_bias_56", lambda s: int((s > 0).sum())),
        mean_delta_tvd=("delta_tvd_56_minus_55", "mean")).reset_index()
    assert len(regions) == 48 and len(global_means) == 6
    return countries, regions, global_means


def chart(countries: pd.DataFrame, regions: pd.DataFrame, out: Path) -> None:
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    ordered = pd.MultiIndex.from_product([REGIONS, ITEMS], names=["cultural_region", "question_id"])
    mat = regions.set_index(["cultural_region", "question_id"]).reindex(ordered)
    left = mat.mean_bias_56.to_numpy().reshape(8, 6)
    right = mat.mean_delta_bias.to_numpy().reshape(8, 6)
    fig, axes = plt.subplots(1, 2, figsize=(7.15, 4.15))
    fig.subplots_adjust(left=.225, right=.985, top=.92, bottom=.25, wspace=.07)
    for ax, array, title, bound in zip(axes, (left, right),
             ("a  GPT-5.6 minus survey", "b  GPT-5.6 minus GPT-5.5 signed gap"),
             (.23, .055), strict=True):
        im = ax.imshow(array, cmap="PuOr_r", norm=TwoSlopeNorm(vcenter=0, vmin=-bound, vmax=bound), aspect="auto")
        ax.set_title(title, fontsize=9, loc="left", pad=9)
        ax.set_yticks(range(8), REGIONS if ax is axes[0] else [""] * 8, fontsize=7.3)
        ax.set_xticks(range(6), SHORT, rotation=43, ha="right", fontsize=6.9)
        for i in range(8):
            for j in range(6):
                value = array[i, j]
                ax.text(j, i, f"{value:+.2f}", ha="center", va="center", fontsize=6.5,
                        color="white" if abs(value) > bound * .57 else "#222222")
        ax.tick_params(length=0)
        for spine in ax.spines.values():
            spine.set_visible(False)
        cb = fig.colorbar(im, ax=ax, orientation="horizontal", fraction=.075, pad=.34, shrink=.86)
        cb.set_label("Normalized signed score", fontsize=7, labelpad=2)
        cb.ax.tick_params(labelsize=6.5)
    fig.text(.59, .065, "Orange: higher on named direction; purple: lower. Equal-country region means.",
             ha="center", fontsize=7.0)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", metadata={"Creator": "EthosGPT signed_directions.py"})
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight", dpi=220)
    plt.close(fig)


def argument_figure(countries: pd.DataFrame, global_means: pd.DataFrame,
                    region_metrics: pd.DataFrame, out: Path) -> None:
    """Visualize the theoretical question and two measured scales without causal arrows."""
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                         "pdf.fonttype": 42, "svg.fonttype": "none"})
    fig = plt.figure(figsize=(7.1, 3.45), facecolor="white")
    top = fig.add_axes([.025, .755, .95, .225])
    top.set_axis_off()
    heads = ("Opportunity", "Distribution and adjustment", "Coordination")
    details = ("Agency (Q48) · science (Q159)",
               "Equality / incentives (Q106)\nSelf-provision (Q108)",
               "Trust (Q57) · immigration (Q121)")
    widths = (.28, .40, .28)
    xs = (.0, .30, .72)
    for x, w, head, detail in zip(xs, widths, heads, details, strict=True):
        top.add_patch(FancyBboxPatch((x, .25), w, .66, boxstyle="round,pad=.012",
                      facecolor="#edf5f6", edgecolor="#276477", linewidth=.9,
                      transform=top.transAxes))
        top.text(x + w/2, .68, head, ha="center", va="center", fontsize=9.3,
                 weight="bold", color="#17324d", transform=top.transAxes)
        top.text(x + w/2, .40, detail, ha="center", va="center", fontsize=7.7,
                 color="#17324d", transform=top.transAxes)
    top.text(.5, .03, "Conceptual: innovation replaces old routines; responses concern its opportunities and social adjustment.",
             ha="center", va="bottom", fontsize=7.7, color="#394755", transform=top.transAxes)
    ax1 = fig.add_axes([.19, .15, .31, .55])
    ax2 = fig.add_axes([.70, .15, .265, .55])
    order = pd.DataFrame({"question_id": ITEMS, "short": SHORT})
    g = order.merge(global_means, on="question_id", validate="one_to_one")
    yy = np.arange(6)[::-1]
    ax1.axvline(0, lw=.8, c="#172b3e")
    for i, row in g.iterrows():
        y = yy[i]
        ax1.plot([row.mean_bias_55, row.mean_bias_56], [y, y],
                 color="#9eabb5", lw=1, zorder=1)
        ax1.scatter(row.mean_bias_55, y, facecolors="none", edgecolors="#657786", s=24, zorder=2)
        ax1.scatter(row.mean_bias_56, y, c="#17324d", s=24, zorder=3)
    ax1.set_yticks(yy, g.short, fontsize=8.2)
    ax1.set_xlim(-.145, .135)
    ax1.set_xticks([-.10, 0, .10], ["−.10", "0", "+.10"], fontsize=8)
    ax1.set_xlabel("Model minus survey directed score", fontsize=8)
    ax1.set_title("Observed | which answers are overstated?", loc="left", fontsize=9, weight="bold", pad=8)
    ax1.text(.02, -.32, "○ GPT-5.5    ● GPT-5.6 Sol", transform=ax1.transAxes, fontsize=8)
    ax2.axvline(0, lw=.8, c="#172b3e")
    region = region_metrics[region_metrics.metric == "TVD"].set_index("cultural_region").reindex(REGIONS)
    per_country = countries.groupby(["country", "cultural_region"]).delta_tvd_56_minus_55.mean()
    for i, label in enumerate(REGIONS):
        y = 7-i
        vals = per_country.xs(label, level="cultural_region").to_numpy()
        offsets = np.linspace(-.13, .13, len(vals)) if len(vals)>1 else [0]
        ax2.scatter(vals, y + offsets, s=7, c="#bac4cc", edgecolors="none", zorder=1)
        row = region.loc[label]
        if pd.notna(row.delta_ci_low_bca) and pd.notna(row.delta_ci_high_bca):
            ax2.plot([row.delta_ci_low_bca, row.delta_ci_high_bca], [y, y],
                     color="#17324d", lw=1.2, zorder=2)
        ax2.scatter(row.delta_56_minus_55, y, marker="D", s=23,
                    c="#bd6939" if row.delta_56_minus_55 > 0 else "#276477", zorder=3)
    ax2.set_yticks(np.arange(8)[::-1],
                   ["African-Islamic", "Catholic Europe", "Confucian", "English-Speaking",
                    "Latin America", "Orthodox Europe", "Protestant Europe", "West & South Asia"], fontsize=7.8)
    ax2.set_xlim(-.032, .032)
    ax2.set_xticks([-.02, 0, .02], ["−.02", "0", "+.02"], fontsize=8)
    ax2.set_xlabel("GPT-5.6 minus GPT-5.5 category error", fontsize=8)
    ax2.set_title("Observed | countries within eight regions", loc="left", fontsize=9, weight="bold", pad=8)
    for ax in (ax1, ax2):
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#e6eaee", lw=.5)
    fig.text(.5, .018, "Smaller category error is descriptive; effects on decisions and sustainable growth remain to be tested.",
             ha="center", fontsize=8.0, color="#394755")
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight", metadata={"Creator": "EthosGPT signed_directions.py"})
    fig.savefig(out.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(out.with_suffix(".png"), bbox_inches="tight", dpi=220)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scores", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--region-metrics", type=Path, required=True)
    args = parser.parse_args()
    frame = pd.read_csv(args.scores)
    countries, regions, global_means = compute(frame)
    infer = pd.read_csv(args.scores.parent / "signed_bias_inference.csv")
    for row in infer.itertuples(index=False):
        observed = global_means.set_index("question_id").loc[row.question_id,
                    "mean_bias_55" if row.model == MODELS[0] else "mean_bias_56"]
        assert np.isclose(observed, row.mean_signed_bias, atol=1e-12)
    region_metrics = pd.read_csv(args.region_metrics)
    expected_tvd = region_metrics[region_metrics.metric == "TVD"].set_index("cultural_region")
    for row in regions[regions.question_id == "Q48"].itertuples(index=False):
        observed = countries[countries.cultural_region == row.cultural_region].groupby("country").delta_tvd_56_minus_55.mean().mean()
        assert np.isclose(observed, expected_tvd.loc[row.cultural_region, "delta_56_minus_55"], atol=1e-12)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    countries.to_csv(args.output_dir / "signed_country_items.csv", index=False, float_format="%.9f")
    regions.to_csv(args.output_dir / "signed_eight_regions.csv", index=False, float_format="%.9f")
    global_means.to_csv(args.output_dir / "signed_global_items.csv", index=False, float_format="%.9f")
    chart(countries, regions, args.output_dir / "figS8_signed_eight_regions.pdf")
    argument_figure(countries, global_means, region_metrics,
                    args.output_dir / "fig1_argument_bridge.pdf")
    print(global_means.to_string(index=False, float_format=lambda x: f"{x:+.4f}"))
    print(regions.to_string(index=False, float_format=lambda x: f"{x:+.4f}"))


if __name__ == "__main__":
    main()
