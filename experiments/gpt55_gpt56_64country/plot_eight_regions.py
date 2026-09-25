#!/usr/bin/env python3
"""Draw eight-region descriptive diagnostics from the frozen Wave 1 score ledger.

Usage (from the repository root)::

    python experiments/gpt55_gpt56_64country/plot_eight_regions.py

This script compares the six-question mean loss for each country before
averaging countries within their *released* cultural-region crosswalk. It
reuses the released, 20,000-draw BCa marginal intervals and never interprets
an unadjusted regional interval as a multiple-testing-adjusted finding.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = ROOT / "experiments/gpt55_gpt56_64country"
ORDER = [
    "West & South Asia", "Catholic Europe", "Orthodox Europe",
    "English-Speaking", "Latin America", "African-Islamic",
    "Protestant Europe", "Confucian",
]
INK = "#18324A"
BLUE = "#315EAF"  # lower loss under 5.6 Sol
AMBER = "#B05719"  # higher loss under 5.6 Sol
GRID = "#DAE2EA"
MUTED = "#566778"
SURFACE = "#FBF6ED"


def prepare(scores_path: Path, summary_path: Path, roster_path: Path):
    raw = pd.read_csv(scores_path)
    roster = pd.read_csv(roster_path)
    published = pd.read_csv(summary_path)
    expected = {"GPT-5.5", "GPT-5.6 Sol"}
    if len(raw) != 64 * 6 * 2 or set(raw.model) != expected:
        raise ValueError("Expected exactly 768 validated six-item/model score rows")
    if raw.duplicated(["country_code", "model", "question_id"]).any():
        raise ValueError("Duplicate country/model/question score")
    if set(raw.cultural_region) != set(ORDER) or len(roster) != 64:
        raise ValueError("Country roster or eight cultural-region labels changed")
    if raw.groupby(["country_code", "model"]).question_id.nunique().ne(6).any():
        raise ValueError("Every country/model must include the same six questions")
    mapping = raw[["country_code", "country", "cultural_region"]].drop_duplicates()
    if len(mapping) != 64 or not mapping.sort_values("country_code").reset_index(drop=True).equals(
        roster[["country_code", "country", "cultural_region"]]
        .sort_values("country_code").reset_index(drop=True)
    ):
        raise ValueError("Score ledger does not match the released country crosswalk")
    c = raw.groupby(["country_code", "country", "cultural_region", "model"], as_index=False)[["tvd", "w1"]].mean()
    pair = c.pivot(index=["country_code", "country", "cultural_region"], columns="model", values=["tvd", "w1"])
    pair.columns = [f"{metric}_{model}" for metric, model in pair.columns]
    pair = pair.reset_index()
    for metric in ("tvd", "w1"):
        pair[f"delta_{metric}"] = pair[f"{metric}_GPT-5.6 Sol"] - pair[f"{metric}_GPT-5.5"]
    if len(pair) != 64 or len(published) != 16 or published.duplicated(["cultural_region", "metric"]).any():
        raise ValueError("Expected 64 countries and 16 published region/metric rows")
    if set(published.metric) != {"TVD", "W1"} or set(published.cultural_region) != set(ORDER):
        raise ValueError("Unexpected region or metric in published sensitivity file")
    if not (published.country_bootstrap_draws.eq(20_000) & published.bootstrap_seed.eq(20260925)).all():
        raise ValueError("Published bootstrap specification changed")
    for row in published.itertuples():
        group = pair[pair.cultural_region == row.cultural_region]
        metric = row.metric.lower()
        if len(group) != row.countries or not np.isclose(group[f"delta_{metric}"].mean(), row.delta_56_minus_55, atol=1e-12):
            raise ValueError(f"Published region mean does not reconcile: {row.cultural_region} {row.metric}")
        if len(group) < 5 and not (pd.isna(row.delta_ci_low_bca) and pd.isna(row.delta_ci_high_bca)):
            raise ValueError("Unexpected published interval for a group with fewer than five countries")
        if len(group) >= 5 and not (np.isfinite(row.delta_ci_low_bca) and np.isfinite(row.delta_ci_high_bca)):
            raise ValueError("Missing published marginal BCa interval")
    return pair, published.set_index(["cultural_region", "metric"])


def common_style():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 8.1,
        "axes.titlesize": 9.1, "axes.labelsize": 8.1,
        "xtick.labelsize": 7.6, "ytick.labelsize": 8.0,
        "svg.fonttype": "none", "pdf.fonttype": 42,
        "axes.unicode_minus": False,
        "savefig.facecolor": "white",
    })


def save(fig, dest: Path):
    for ext in ("pdf", "svg", "png"):
        fig.savefig(dest.with_suffix(f".{ext}"), dpi=240 if ext == "png" else None,
                    facecolor="white", metadata={"Creator": "EthosGPT eight-region plotting script"} if ext == "pdf" else None)
    plt.close(fig)


def fig_country_tvd(pair, summary, out):
    """Country dot strip plus the region means and their published uncertainty."""
    fig, ax = plt.subplots(figsize=(5.55, 4.55))
    fig.subplots_adjust(left=.303, right=.85, top=.82, bottom=.30)
    ax.set_axisbelow(True)
    ax.set_xlim(-.035, .0325)
    ax.set_ylim(-.55, 7.55)
    ax.invert_yaxis()
    ax.axvline(0, color=INK, linewidth=1.05, zorder=1)
    ax.grid(axis="x", color=GRID, linewidth=.62)
    ax.set_xticks([-.03, -.02, -.01, 0, .01, .02, .03])
    ax.set_xticklabels(["-.03", "-.02", "-.01", "0", "+.01", "+.02", "+.03"])
    ax.set_yticks(range(8), ORDER)
    ax.tick_params(axis="y", length=0, pad=7, colors=INK)
    ax.tick_params(axis="x", length=2, colors=MUTED)
    ax.set_xlabel("GPT-5.6 Sol minus GPT-5.5: country mean TVD", labelpad=8, color=INK)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.axhspan(6.57, 7.43, color=SURFACE, zorder=-2)
    for idx, region in enumerate(ORDER):
        part = pair.loc[pair.cultural_region == region].sort_values(["delta_tvd", "country_code"])
        # Rank-based offsets reveal points on top of one another without moving
        # a country into a different regional row or changing the x statistic.
        jitter = np.linspace(-.18, .18, len(part)) if len(part) > 1 else np.array([0.0])
        vals = part.delta_tvd.to_numpy()
        ax.scatter(vals, idx + jitter, c=[BLUE if value < 0 else AMBER for value in vals],
                   s=20, alpha=.73, edgecolors="white", linewidths=.32, zorder=3)
        rec = summary.loc[(region, "TVD")]
        mean = rec.delta_56_minus_55
        if len(part) >= 5:
            ax.plot([rec.delta_ci_low_bca, rec.delta_ci_high_bca], [idx, idx],
                    color=INK, linewidth=1.5, zorder=4)
            ax.plot([rec.delta_ci_low_bca, rec.delta_ci_low_bca], [idx-.085, idx+.085], color=INK, lw=.95, zorder=4)
            ax.plot([rec.delta_ci_high_bca, rec.delta_ci_high_bca], [idx-.085, idx+.085], color=INK, lw=.95, zorder=4)
        ax.scatter([mean], [idx], marker="D", s=37, facecolor="white" if len(part) < 5 else INK,
                   edgecolor=INK, linewidth=1.2, zorder=6)
        lower = int((part.delta_tvd < 0).sum())
        ax.text(1.028, idx, f"{lower}/{len(part)}", transform=ax.get_yaxis_transform(),
                va="center", ha="left", color=INK if region == "Confucian" else MUTED,
                fontsize=7.7, fontweight="bold" if region == "Confucian" else "normal")
    fig.text(.303, .914, "Every country within its cultural region", color=INK,
             fontweight="bold", fontsize=9.2)
    fig.text(.303, .869, "Lower error", color=BLUE, fontsize=8.0, fontweight="bold")
    fig.text(.696, .869, "Higher error", color=AMBER, fontsize=8.0, fontweight="bold")
    fig.text(.865, .877, "Lower TVD", color=INK, fontsize=7.5, ha="left")
    fig.text(.865, .850, "countries", color=INK, fontsize=7.5, ha="left")
    handles = [
        Line2D([0], [0], linestyle="none", marker="o", color=BLUE, markersize=4, label="Country"),
        Line2D([0], [0], linestyle="none", marker="D", markerfacecolor=INK, color=INK, markersize=4.8, label="Region mean"),
        Line2D([0], [0], color=INK, linewidth=1.5, label="95% BCa interval (n ≥ 5)"),
    ]
    fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(.28, .105), frameon=False,
               fontsize=7.5, ncol=2, handlelength=1.2, columnspacing=1.3)
    fig.text(.303, .055, "Open diamond: no interval for n < 5. Exploratory regional comparison.",
             color=MUTED, fontsize=7.3)
    save(fig, out / "figS6_region_country_tvd")


def fig_region_metrics(summary, out):
    """Aligned interval panels expose concordant and discordant error changes."""
    fig, axs = plt.subplots(1, 2, figsize=(5.55, 4.50), sharey=True)
    fig.subplots_adjust(left=.303, right=.965, top=.79, bottom=.30, wspace=.14)
    for ax, metric, lim, ticks in zip(
        axs, ["W1", "TVD"], [(-.017, .017), (-.032, .027)],
        [[-.015, -.005, 0, .005, .015], [-.03, -.015, 0, .015]],
    ):
        ax.set_xlim(*lim)
        ax.set_ylim(-.55, 7.55)
        ax.invert_yaxis()
        ax.axvline(0, color=INK, linewidth=1.0, zorder=1)
        ax.axhspan(4.57, 5.43, color="#F0F7F6", zorder=-2)
        ax.axhspan(6.57, 7.43, color=SURFACE, zorder=-2)
        ax.set_axisbelow(True)
        ax.grid(axis="x", color=GRID, linewidth=.58)
        ax.set_xticks(ticks)
        ax.set_xticklabels(["0" if abs(t) < 1e-9 else f"{t:+.3f}".rstrip("0").rstrip(".") for t in ticks])
        ax.set_yticks(range(8), [f"{region}  ({int(summary.loc[(region, metric), 'countries'])})" for region in ORDER])
        ax.tick_params(axis="y", length=0, pad=6, colors=INK)
        ax.tick_params(axis="x", length=0, colors=MUTED, pad=6)
        ax.set_title(f"{'Ordered distance (W1)' if metric == 'W1' else 'Total variation (TVD)'}", loc="left", pad=12,
                     color=INK, fontweight="bold", fontsize=8.6)
        for spine in ax.spines.values():
            spine.set_visible(False)
        for idx, region in enumerate(ORDER):
            rec = summary.loc[(region, metric)]
            mean, lo, hi = rec.delta_56_minus_55, rec.delta_ci_low_bca, rec.delta_ci_high_bca
            if np.isfinite(lo) and np.isfinite(hi):
                ax.plot([lo, hi], [idx, idx], color=INK, linewidth=1.6, zorder=4)
                ax.plot([lo, lo], [idx-.105, idx+.105], color=INK, linewidth=.85, zorder=4)
                ax.plot([hi, hi], [idx-.105, idx+.105], color=INK, linewidth=.85, zorder=4)
            ax.scatter([mean], [idx], marker="o" if metric == "W1" else "s", s=35,
                       facecolor=(BLUE if mean < 0 else AMBER) if rec.countries >= 5 else "white",
                       edgecolor=INK, linewidth=.95, zorder=5)
    axs[1].tick_params(axis="y", labelleft=False)
    fig.text(.303, .908, "Two metrics, eight original cultural regions", color=INK,
             fontweight="bold", fontsize=9.2)
    fig.text(.303, .878, "Left of zero: lower error under GPT-5.6 Sol; right of zero: higher error.",
             color=MUTED, fontsize=7.45)
    fig.text(.303, .135, "Equal-country means; whiskers: marginal 95% BCa intervals (n ≥ 5).",
             color=MUTED, fontsize=7.15)
    fig.text(.303, .087, "Hollow: n < 5 (no interval). Exploratory and unadjusted.",
             color=MUTED, fontsize=7.15)
    save(fig, out / "figS7_region_metric_intervals")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=EXPERIMENT / "results/country_question_scores.csv")
    parser.add_argument("--summary", type=Path, default=EXPERIMENT / "results/eight_region_sensitivity.csv")
    parser.add_argument("--roster", type=Path, default=EXPERIMENT / "inputs/country_roster.csv")
    parser.add_argument("--out", type=Path, default=ROOT / "results/region_figures")
    args = parser.parse_args()
    pair, summary = prepare(args.scores, args.summary, args.roster)
    args.out.mkdir(parents=True, exist_ok=True)
    common_style()
    fig_country_tvd(pair, summary, args.out)
    fig_region_metrics(summary, args.out)
    print(f"Validated {len(pair)} countries, eight regions, two metrics; wrote {args.out}")


if __name__ == "__main__":
    main()
