#!/usr/bin/env python3
"""Generate the v0.4.0 manuscript tables, figures, and appendix assets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import shutil

os.environ.setdefault("SOURCE_DATE_EPOCH", "1788566400")
os.environ.setdefault("TZ", "UTC")

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Circle, FancyBboxPatch, Polygon, Rectangle
import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist
from scipy.stats import spearmanr


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"
RESULTS = EXP / "results"
PAPER_FIGURES = ROOT / "paper/figs"
RESULT_FIGURES = ROOT / "results/figures"
PAPER_TABLES = ROOT / "paper/tabs"

NAVY = "#17324D"
TEAL = "#008F80"
MAGENTA = "#B23A6F"
GRAY = "#6B7280"
LIGHT = "#F3F5F7"
GRID = "#D8DEE5"
TEAL_LIGHT = "#DDF4EF"
MAGENTA_LIGHT = "#F8E4EC"


def style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "font.size": 8.5,
        "axes.titlesize": 9.2,
        "axes.labelsize": 8.4,
        "xtick.labelsize": 7.4,
        "ytick.labelsize": 7.7,
        "legend.fontsize": 7.3,
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ethosgpt-v0.7.0-base",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def save_figure(fig: plt.Figure, stem: str) -> None:
    # v1.0 owns the displayed visual sequence. This legacy stage now supplies
    # tables/tutorial assets only and must not repopulate retired figure stems.
    if stem in {"fig1_wave1_design", "fig2_wave1_results"}:
        return
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    metadata = {"Creator": "EthosGPT v0.7.0 reproducible figure pipeline"}
    fig.savefig(RESULT_FIGURES / f"{stem}.pdf", metadata=metadata)
    fig.savefig(RESULT_FIGURES / f"{stem}.svg", metadata=metadata)
    for suffix in (".pdf", ".svg"):
        shutil.copy2(RESULT_FIGURES / f"{stem}{suffix}", PAPER_FIGURES / f"{stem}{suffix}")


def card(ax: plt.Axes, x: float, title: str, subtitle: str, accent: str) -> None:
    patch = FancyBboxPatch(
        (x, 0.08), 0.205, 0.79,
        boxstyle="round,pad=0.010,rounding_size=0.018",
        linewidth=0.9, edgecolor=accent, facecolor="white",
        transform=ax.transAxes,
    )
    ax.add_patch(patch)
    ax.text(x + 0.1025, 0.39, title, ha="center", va="center", color=NAVY,
            weight="bold", fontsize=8.8, transform=ax.transAxes)
    ax.text(x + 0.1025, 0.235, subtitle, ha="center", va="center", color=GRAY,
            fontsize=7.2, linespacing=1.10, transform=ax.transAxes)


def figure_design_bridge() -> None:
    fig, ax = plt.subplots(figsize=(7.05, 2.02))
    ax.set_axis_off()
    xs = [0.005, 0.258, 0.511, 0.764]
    accents = [NAVY, "#4361A8", TEAL, MAGENTA]
    titles = ["Public-value evidence", "Paired model versions", "Cultural geometry", "Economic relevance"]
    subtitles = [
        "64 countries × 6 anchors\nunweighted survey\nprobability distributions",
        "GPT-5.5 vs GPT-5.6 Sol\n5 generations per\ncountry–item",
        "distribution error, profile gap,\nspread, and country\nrelations",
        "innovation, adjustment,\nand legitimacy under\nexplicit decision rules",
    ]
    for x, title, subtitle, accent in zip(xs, titles, subtitles, accents, strict=True):
        card(ax, x, title, subtitle, accent)
    for x in (0.229, 0.482, 0.735):
        ax.annotate("", xy=(x + 0.019, 0.50), xytext=(x, 0.50), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="-|>", lw=1.0, color=GRAY))

    # Survey stack icon.
    for offset in (0.0, 0.012, 0.024):
        ax.add_patch(Rectangle((xs[0] + 0.057 + offset, 0.57 + offset), 0.082, 0.13,
                               transform=ax.transAxes, fc="white", ec=NAVY, lw=0.8))
    for iy, width in enumerate((0.056, 0.071, 0.044)):
        ax.plot([xs[0] + 0.075, xs[0] + 0.075 + width], [0.665 - iy * 0.031] * 2,
                transform=ax.transAxes, color=NAVY, lw=1.2)
    ax.text(xs[0] + 0.1025, 0.765, "64", ha="center", va="center", color=NAVY,
            fontsize=10, weight="bold", transform=ax.transAxes)

    # Two chips and five repeated dots.
    for dx, color in ((0.042, "#4361A8"), (0.115, "#6A4C93")):
        ax.add_patch(FancyBboxPatch((xs[1] + dx, 0.585), 0.050, 0.095,
                                   boxstyle="round,pad=0.006", transform=ax.transAxes,
                                   fc=LIGHT, ec=color, lw=0.9))
        for k in range(5):
            ax.add_patch(Circle((xs[1] + dx + 0.005 + k * 0.010, 0.557), 0.0032,
                                transform=ax.transAxes, fc=color, ec="none"))

    # Center, spread, structure icon.
    cx = xs[2] + 0.103
    ax.add_patch(Circle((cx, 0.635), 0.054, transform=ax.transAxes, fc="none", ec=TEAL, lw=1.0))
    nodes = [(cx - .035, .625), (cx + .002, .669), (cx + .037, .606)]
    for a, b in ((0, 1), (1, 2), (0, 2)):
        ax.plot([nodes[a][0], nodes[b][0]], [nodes[a][1], nodes[b][1]], transform=ax.transAxes,
                color=TEAL, lw=.75)
    for px, py in nodes:
        ax.add_patch(Circle((px, py), .008, transform=ax.transAxes, fc=TEAL, ec="white", lw=.5))

    # Innovation / adjustment controls icon.
    for idx, (label, ypos) in enumerate((("I", .68), ("A", .625), ("L", .57))):
        ax.text(xs[3] + .050, ypos, label, color=MAGENTA, weight="bold", fontsize=7.4,
                ha="center", va="center", transform=ax.transAxes)
        ax.plot([xs[3] + .068, xs[3] + .155], [ypos, ypos], transform=ax.transAxes,
                color=GRID, lw=2.2, solid_capstyle="round")
        knob = (0.095, 0.132, 0.112)[idx]
        ax.add_patch(Circle((xs[3] + knob, ypos), .008, transform=ax.transAxes,
                            fc=MAGENTA, ec="white", lw=.5))
    ax.text(0.5, 0.985, "From survey distributions to technology-facing implications",
            ha="center", va="top", fontsize=10.2, weight="bold", color=NAVY, transform=ax.transAxes)
    save_figure(fig, "fig1_wave1_design")
    plt.close(fig)


def forest(ax: plt.Axes, frame: pd.DataFrame, label_col: str, estimate_col: str,
           low_col: str, high_col: str, p_col: str, title: str, xlabel: str,
           xlim: tuple[float, float]) -> None:
    data = frame.reset_index(drop=True)
    y = np.arange(len(data))[::-1]
    ax.axvline(0, color=NAVY, lw=0.8, zorder=0)
    for index, row in data.iterrows():
        estimate = float(row[estimate_col])
        low = float(row[low_col])
        high = float(row[high_col])
        color = TEAL if estimate < 0 else MAGENTA
        significant = float(row[p_col]) <= 0.05
        yy = y[index]
        ax.plot([low, high], [yy, yy], color=color, lw=1.7, solid_capstyle="round")
        ax.scatter([estimate], [yy], s=34, marker="o" if label_col == "metric_label" else "D",
                   facecolor=color if significant else "white", edgecolor=color, linewidth=1.1, zorder=3)
    ax.set_yticks(y, data[label_col])
    ax.set_xlim(*xlim)
    ax.set_xlabel(xlabel)
    ax.set_title(title, loc="left", color=NAVY, weight="bold", pad=4)
    ax.grid(axis="x", color=GRID, lw=0.5, alpha=0.8)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)


def country_crg(scores: pd.DataFrame) -> pd.DataFrame:
    domains = ["Agency", "Trust", "Distribution", "Market", "Inclusion", "Science"]
    human = scores.drop_duplicates(["country", "domain"])[["country", "domain", "human_directed"]].pivot(
        index="country", columns="domain", values="human_directed"
    ).reindex(columns=domains)
    sigma = human.std(ddof=1)
    rows = []
    for model in ("GPT-5.5", "GPT-5.6 Sol"):
        model_values = scores[scores.model == model].pivot(index="country", columns="domain", values="model_directed").reindex(columns=domains)
        values = np.sqrt(np.square((model_values - human) / sigma).mean(axis=1))
        rows.append(values.rename(model))
    frame = pd.concat(rows, axis=1)
    frame["delta_crg"] = frame["GPT-5.6 Sol"] - frame["GPT-5.5"]
    return frame.reset_index()


def figure_results() -> None:
    global_data = pd.read_csv(RESULTS / "metric_comparisons.csv")
    global_data["metric_label"] = global_data["metric"].map({
        "W1": "Ordered distance (W1)",
        "TVD": "Category mass (TVD)",
        "CRG": "Profile gap (CRG)",
        "VDR": "Dispersion gap |VDR−1|",
        "CSR": "Structure loss 1−CSR",
    })
    domains = pd.read_csv(RESULTS / "domain_comparisons.csv")
    domains = domains[domains.metric == "W1"].copy()
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    crg = country_crg(scores)
    coordinates = pd.read_csv(EXP / "inputs/country_coordinates.csv")
    map_data = crg.merge(coordinates, on="country", validate="one_to_one")

    fig = plt.figure(figsize=(7.08, 4.62))
    grid = fig.add_gridspec(2, 2, width_ratios=(1.18, 0.82), height_ratios=(1.02, 1.0),
                           hspace=0.47, wspace=0.34)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_b = fig.add_subplot(grid[0, 1])
    ax_c = fig.add_subplot(grid[1, :])
    forest(ax_a, global_data, "metric_label", "estimate", "ci_low_bca", "ci_high_bca",
           "holm_p_five_metrics", "A  Overall target-loss changes", "GPT-5.6 − GPT-5.5", (-0.058, 0.089))
    forest(ax_b, domains, "domain", "delta_56_minus_55", "ci_low_bca", "ci_high_bca",
           "holm_p_within_metric", "B  Ordered-distance changes by anchor", "Δ W1", (-0.017, 0.014))
    ax_b.legend(
        handles=[
            Line2D([0], [0], marker="D", color="none", markerfacecolor=NAVY,
                   markeredgecolor=NAVY, markersize=4.8, label="Holm p <= .05"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor="white",
                   markeredgecolor=NAVY, markersize=4.8, label="uncertain"),
        ],
        loc="lower right", frameon=False, handletextpad=.35, borderaxespad=.1,
    )

    world_path = Path(gpd.__file__).resolve().parent / "datasets/naturalearth_lowres/naturalearth_lowres.shp"
    world = gpd.read_file(world_path)
    world.plot(ax=ax_c, color="#F1F3F5", edgecolor="#C5CCD3", linewidth=0.35)
    bound = max(abs(map_data.delta_crg.min()), abs(map_data.delta_crg.max()))
    cmap = LinearSegmentedColormap.from_list("ethos_div", [TEAL, "#F7F7F7", MAGENTA])
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
    sizes = 17 + 90 * np.sqrt(np.abs(map_data.delta_crg) / bound)
    scatter = ax_c.scatter(map_data.longitude, map_data.latitude, c=map_data.delta_crg,
                           cmap=cmap, norm=norm, s=sizes, marker="D", edgecolor="white",
                           linewidth=0.45, zorder=3)
    ax_c.set_xlim(-177, 181)
    ax_c.set_ylim(-58, 85)
    ax_c.set_aspect("auto")
    ax_c.set_axis_off()
    ax_c.set_title("C  Where the country-profile gap changed", loc="left", color=NAVY,
                   weight="bold", pad=4)
    cbar = fig.colorbar(scatter, ax=ax_c, orientation="horizontal", fraction=0.046, pad=0.035, aspect=35)
    cbar.set_label("Δ CRG   (teal: closer; magenta: farther)", fontsize=7.5)
    cbar.ax.tick_params(labelsize=7.1, length=2)
    ax_c.text(0.01, 0.02, "64 countries; diamonds show country-level change\n"
              "k=4 Geary C=0.752, BH q=0.029", transform=ax_c.transAxes,
              fontsize=7.2, color=NAVY, ha="left", va="bottom",
              bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=GRID, lw=.5, alpha=.92))
    fig.text(0.012, 0.008, "Negative values indicate closer alignment; positive values indicate farther alignment. Filled markers pass Holm correction; country is the inferential unit.",
             fontsize=7.2, color=GRAY)
    save_figure(fig, "fig2_wave1_results")
    plt.close(fig)


def figure_uncertainty() -> None:
    conditional = pd.read_csv(RESULTS / "conditional_uncertainty_contrasts.csv")
    metric_order = ["W1", "TVD", "CRG", "VDR", "CSR"]
    source_labels = {
        "human multinomial cells, fixed countries and model means": "human-cell resampling",
        "five-generation resampling, fixed countries and human cells": "five-run resampling",
    }
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 2.75), sharey=True)
    for ax, (source, part) in zip(axes, conditional.groupby("uncertainty_source", sort=False), strict=True):
        part = part.set_index("metric").reindex(metric_order).reset_index()
        y = np.arange(len(part))[::-1]
        ax.axvline(0, color=NAVY, lw=.8)
        for idx, row in part.iterrows():
            est = row.point_loss_delta_56_minus_55
            color = TEAL if est < 0 else MAGENTA
            ax.plot([row.centered_sensitivity_interval_low_95, row.centered_sensitivity_interval_high_95],
                    [y[idx], y[idx]], color=color, lw=1.8)
            ax.scatter(est, y[idx], color=color, s=28, zorder=3)
        ax.set_yticks(y, metric_order)
        ax.grid(axis="x", color=GRID, lw=.5)
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_title(source_labels[source], color=NAVY, weight="bold")
        ax.set_xlabel("Conditional target-loss contrast")
    fig.suptitle("Uncertainty sources do not replace country-level inference", color=NAVY,
                 weight="bold", y=1.01)
    fig.text(.01, .01, "Centered 95% sensitivity intervals from 5,000 draws; survey design and weights remain unavailable.",
             fontsize=7.2, color=GRAY)
    fig.tight_layout(rect=(0, .05, 1, .96))
    save_figure(fig, "figS1_uncertainty_sources")
    plt.close(fig)


def fmt(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return "--"
    text = f"{value:.{digits}f}"
    if text.startswith("0."):
        return text[1:]
    if text.startswith("-0."):
        return "-" + text[2:]
    return text


def main_table() -> None:
    estimates = pd.read_csv(RESULTS / "metric_estimates.csv")
    comparisons = pd.read_csv(RESULTS / "metric_comparisons.csv").set_index("metric")
    labels = {"W1": "W1 $\\downarrow$", "TVD": "TVD $\\downarrow$", "CRG": "CRG $\\downarrow$", "VDR": "VDR $\\to 1$", "CSR": "CSR $\\uparrow$"}
    lines = [
        r"\begin{table}[t]",
        r"\centering",
        r"\caption{Sixty-four-country model comparison. Parentheses give country-bootstrap SEs; the contrast is target loss for GPT-5.6 Sol minus GPT-5.5, so negative values favor GPT-5.6.}",
        r"\label{tab:main}",
        r"\scriptsize",
        r"\setlength{\tabcolsep}{3.0pt}",
        r"\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrl@{}}",
        r"\toprule",
        r"Metric & GPT-5.5 & GPT-5.6 Sol & $\Delta$ loss [95\% BCa CI] & Holm $p$ \\",
        r"\midrule",
    ]
    for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
        first = estimates[(estimates.model == "GPT-5.5") & (estimates.metric == metric)].iloc[0]
        second = estimates[(estimates.model == "GPT-5.6 Sol") & (estimates.metric == metric)].iloc[0]
        comp = comparisons.loc[metric]
        direction = r"\textcolor{improveink}{$\downarrow$}" if comp.estimate < 0 else r"\textcolor{worseink}{$\uparrow$}"
        delta = f"{fmt(comp.estimate)} [{fmt(comp.ci_low_bca)},{fmt(comp.ci_high_bca)}] {direction}"
        pvalue = "<.001" if comp.holm_p_five_metrics < .001 else fmt(comp.holm_p_five_metrics, 3)
        if comp.holm_p_five_metrics <= .05:
            delta = r"\cellcolor{improvebg}\textbf{" + delta + "}"
            pvalue = r"\cellcolor{improvebg}\textbf{" + pvalue + "}"
        lines.append(
            f"{labels[metric]} & {fmt(first.estimate)} ({fmt(first.standard_error)}) & "
            f"{fmt(second.estimate)} ({fmt(second.standard_error)}) & {delta} & {pvalue} \\\\" 
        )
    lines += [
        r"\bottomrule",
        r"\end{tabular*}",
        r"\vspace{1pt}",
        r"\begin{minipage}{.98\linewidth}\scriptsize W1 respects ordinal distance; TVD measures category mass. CRG is the standardized country-profile gap. VDR compares cross-country spread; CSR compares the rank order of country-pair distances. All intervals use 20,000 country resamples; $p$-values use 19,999 paired sign flips and Holm correction across five metrics.\end{minipage}",
        r"\end{table}",
    ]
    (PAPER_TABLES / "table1_main.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def appendix_tables_and_data() -> None:
    roster = pd.read_csv(EXP / "inputs/country_roster.csv")
    human = pd.read_parquet(ROOT / "data/processed/human_item_distributions.parquet")
    questions = ["Q48", "Q57", "Q106", "Q108", "Q121", "Q159"]
    counts = (
        human[human.country.isin(roster.country) & human.question_id.isin(questions)]
        .drop_duplicates(["country", "question_id"])
        .pivot(index="country", columns="question_id", values="n")
        .reindex(columns=questions)
    )
    coverage = roster.merge(counts.reset_index(), on="country", validate="one_to_one")
    coverage["six_anchor_complete"] = coverage[questions].notna().all(axis=1)
    coverage.to_csv(RESULTS / "country_coverage_and_human_cell_counts.csv", index=False)
    summary = coverage[questions].agg(["min", "median", "max"]).T.reset_index().rename(columns={"index": "question_id"})
    summary.to_csv(RESULTS / "human_cell_count_summary.csv", index=False)

    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    q = scores[(scores.country == "China") & (scores.question_id == "Q106")].copy()
    hq = human[(human.country == "China") & (human.question_id == "Q106")][["score", "probability", "n"]].sort_values("score")
    tutorial = hq.rename(columns={"probability": "human_probability"})
    for _, row in q.iterrows():
        values = json.loads(row.model_probabilities)
        tutorial[row.model.replace(" ", "_").replace(".", "") + "_probability"] = [values[str(int(value))] for value in tutorial.score]
    tutorial.to_csv(RESULTS / "tutorial_china_q106.csv", index=False)

    domains = ["Agency", "Trust", "Distribution", "Market", "Inclusion", "Science"]
    hwide = scores.drop_duplicates(["country", "domain"])[["country", "domain", "human_directed"]].pivot(index="country", columns="domain", values="human_directed").reindex(columns=domains)
    profiles = {model: scores[scores.model == model].pivot(index="country", columns="domain", values="model_directed").reindex(columns=domains) for model in ("GPT-5.5", "GPT-5.6 Sol")}
    selected = ["China", "Brazil", "Nigeria", "United States"]
    profile_rows = []
    for source, frame in (("Human", hwide), *profiles.items()):
        for country in selected:
            profile_rows.append({"source": source, "country": country, **frame.loc[country].to_dict()})
    pd.DataFrame(profile_rows).to_csv(RESULTS / "tutorial_four_country_profiles.csv", index=False)
    distance_rows = []
    human_dist = pdist(hwide.loc[selected].to_numpy(float))
    pairs = [(selected[i], selected[j]) for i in range(len(selected)) for j in range(i + 1, len(selected))]
    for source, frame in (("Human", hwide), *profiles.items()):
        distance = pdist(frame.loc[selected].to_numpy(float))
        for (first, second), value in zip(pairs, distance, strict=True):
            distance_rows.append({"source": source, "country_1": first, "country_2": second, "distance": value})
        if source != "Human":
            distance_rows.append({
                "source": source,
                "country_1": "SUMMARY",
                "country_2": "VDR / CSR",
                "distance": np.nan,
                "vdr": float(distance.mean() / human_dist.mean()),
                "csr": float(spearmanr(human_dist, distance).statistic),
            })
    pd.DataFrame(distance_rows).to_csv(RESULTS / "tutorial_four_country_distances.csv", index=False)

    # Longtable source: every new-API country, its descriptive region, and six human cell counts.
    lines = [
        r"\begin{longtable}{p{0.18\linewidth}p{0.20\linewidth}rrrrrr}",
        r"\caption{Complete new-API roster and human comparison-cell counts. Every listed country has all six anchors in both model versions; counts are unweighted records in the public derivative.}\label{tab:country-roster}\\",
        r"\toprule Country / society & Descriptive region & Q48 & Q57 & Q106 & Q108 & Q121 & Q159 \\",
        r"\midrule\endfirsthead",
        r"\toprule Country / society & Descriptive region & Q48 & Q57 & Q106 & Q108 & Q121 & Q159 \\",
        r"\midrule\endhead",
    ]
    escape = lambda value: str(value).replace("&", r"\&")
    for row in coverage.sort_values(["cultural_region", "country"]).itertuples(index=False):
        lines.append(f"{escape(row.country)} & {escape(row.cultural_region)} & " + " & ".join(str(int(getattr(row, qid))) for qid in questions) + r" \\")
    lines += [r"\bottomrule", r"\end{longtable}"]
    (PAPER_TABLES / "appendix_country_roster.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")

    official = json.loads((EXP / "inputs/official_wvs_questions.json").read_text(encoding="utf-8"))
    actual = json.loads((EXP / "inputs/questionnaire_and_prompts.json").read_text(encoding="utf-8"))
    actual_by_q = {item["question_id"]: item for item in actual["questions"]}

    def latex_escape(value: str) -> str:
        replacements = {
            "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
            "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
            "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
        }
        return "".join(replacements.get(char, char) for char in value)

    prompt_lines = []
    for item in official["questions"]:
        qid = item["question_id"]
        prompt_lines += [
            f"\\subsection{{{qid}: {latex_escape(item['domain'])}}}",
            r"\paragraph{Official WVS7 wording.} " + latex_escape(item["official_wording"]) +
            f" \\citep[p.~{item['source_page']}]{{wvs7masterquestionnaire}}",
            r"\paragraph{Official choices.} " + "; ".join(
                f"{latex_escape(str(key))} = {latex_escape(str(value))}" for key, value in sorted(item["choices"].items(), key=lambda pair: int(pair[0]))
            ) + ".",
            f"\\begin{{promptlisting}}{{Exact API prompt template for {qid}}}",
            actual_by_q[qid]["prompt_template"],
            r"\end{promptlisting}",
        ]
    (ROOT / "paper/appendices/generated_questionnaire_prompts.tex").write_text("\n\n".join(prompt_lines) + "\n", encoding="utf-8")


def generated_tutorial_tables() -> None:
    tutorial = pd.read_csv(RESULTS / "tutorial_china_q106.csv")
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    china = scores[(scores.country == "China") & (scores.question_id == "Q106")].set_index("model")
    lines = [
        r"\begin{table}[h]", r"\centering", r"\caption{Worked item example: China, Q106. Model columns average the five generations.}",
        r"\label{tab:tutorial-q106}", r"\small", r"\begin{tabular}{rrrr}",
        r"\toprule Score & Human $q_r$ & GPT-5.5 $p_r$ & GPT-5.6 Sol $p_r$ \\", r"\midrule",
    ]
    for _, row in tutorial.iterrows():
        lines.append(
            f"{int(row['score'])} & {row['human_probability']:.3f} & "
            f"{row['GPT-55_probability']:.3f} & {row['GPT-56_Sol_probability']:.3f}"
            + r" \\"
        )
    lines += [
        r"\midrule",
        f"W1 & -- & {china.loc['GPT-5.5','w1']:.4f} & {china.loc['GPT-5.6 Sol','w1']:.4f}" + r" \\",
        f"TVD & -- & {china.loc['GPT-5.5','tvd']:.4f} & {china.loc['GPT-5.6 Sol','tvd']:.4f}" + r" \\",
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ]

    profile = pd.read_csv(RESULTS / "tutorial_four_country_profiles.csv")
    china_profile = profile[profile.country == "China"].set_index("source")
    human_scores = scores.drop_duplicates(["country", "domain"])[["country", "domain", "human_directed"]].pivot(index="country", columns="domain", values="human_directed")
    sigmas = human_scores.std(ddof=1)
    lines += [
        r"\begin{table}[h]", r"\centering", r"\caption{Worked country-profile example for China. Directed scores are on $[0,1]$; $\sigma_k$ is the 64-country human SD.}",
        r"\label{tab:tutorial-crg}", r"\small", r"\begin{tabular}{lrrrrr}",
        r"\toprule Domain & Human & GPT-5.5 & GPT-5.6 Sol & $\sigma_k$ & GPT-5.5 $z$ error \\", r"\midrule",
    ]
    for domain in ("Agency", "Trust", "Distribution", "Market", "Inclusion", "Science"):
        h = china_profile.loc["Human", domain]
        m55 = china_profile.loc["GPT-5.5", domain]
        m56 = china_profile.loc["GPT-5.6 Sol", domain]
        lines.append(
            f"{domain} & {h:.3f} & {m55:.3f} & {m56:.3f} & "
            f"{sigmas[domain]:.3f} & {(m55-h)/sigmas[domain]:.3f}" + r" \\"
        )
    z55 = (china_profile.loc["GPT-5.5", sigmas.index] - china_profile.loc["Human", sigmas.index]) / sigmas
    z56 = (china_profile.loc["GPT-5.6 Sol", sigmas.index] - china_profile.loc["Human", sigmas.index]) / sigmas
    lines += [
        r"\midrule",
        f"CRG & -- & {np.sqrt(np.square(z55).mean()):.3f} & {np.sqrt(np.square(z56).mean()):.3f} & -- & --" + r" \\",
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ]

    distances = pd.read_csv(RESULTS / "tutorial_four_country_distances.csv")
    pair_rows = distances[distances.country_1 != "SUMMARY"].pivot(index=["country_1", "country_2"], columns="source", values="distance").reset_index()
    summary = distances[distances.country_1 == "SUMMARY"].set_index("source")
    lines += [
        r"\begin{table}[h]", r"\centering", r"\caption{Four-country tutorial subset (China, Brazil, Nigeria, United States). This subset illustrates the arithmetic and is not a separate inferential result.}",
        r"\label{tab:tutorial-geometry}", r"\small", r"\begin{tabular}{llrrr}",
        r"\toprule Country 1 & Country 2 & Human distance & GPT-5.5 & GPT-5.6 Sol \\", r"\midrule",
    ]
    for _, row in pair_rows.iterrows():
        lines.append(
            f"{row['country_1']} & {row['country_2']} & {row['Human']:.3f} & "
            f"{row['GPT-5.5']:.3f} & {row['GPT-5.6 Sol']:.3f}" + r" \\"
        )
    lines += [
        r"\midrule",
        f"VDR & -- & 1.000 & {summary.loc['GPT-5.5','vdr']:.3f} & {summary.loc['GPT-5.6 Sol','vdr']:.3f}" + r" \\",
        f"CSR & -- & 1.000 & {summary.loc['GPT-5.5','csr']:.3f} & {summary.loc['GPT-5.6 Sol','csr']:.3f}" + r" \\",
        r"\bottomrule", r"\end{tabular}", r"\end{table}",
    ]
    (PAPER_TABLES / "appendix_tutorial_tables.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generated_full_results_tables() -> None:
    def compact(value: float, digits: int = 4) -> str:
        """TeX-friendly decimals for wide statistical tables."""
        return f"{value:.{digits}f}".replace("-0.", "-.").replace("0.", ".")

    estimates = pd.read_csv(RESULTS / "metric_estimates.csv")
    comparisons = pd.read_csv(RESULTS / "metric_comparisons.csv")
    domains = pd.read_csv(RESULTS / "domain_comparisons.csv")
    q121 = pd.read_csv(RESULTS / "q121_prompt_deviation_sensitivity.csv")
    conditional = pd.read_csv(RESULTS / "conditional_uncertainty_contrasts.csv")
    stability = pd.read_csv(RESULTS / "run_stability.csv")
    bias = pd.read_csv(RESULTS / "signed_bias_inference.csv")
    convergence = pd.read_csv(RESULTS / "bootstrap_convergence.csv")
    lines = [
        r"\begin{table}[h]", r"\centering", r"\caption{Global model estimates. Standard errors and BCa intervals resample countries in 20,000 draws.}",
        r"\label{tab:global-estimates}", r"\small", r"\begin{tabular}{llrrr}",
        r"\toprule Model & Metric & Estimate & SE & 95\% BCa CI \\", r"\midrule",
    ]
    for row in estimates.itertuples(index=False):
        lines.append(
            f"{row.model} & {row.metric} & {row.estimate:.4f} & {row.standard_error:.4f} & "
            f"[{row.ci_low_bca:.4f},{row.ci_high_bca:.4f}]" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}",
              r"\begin{table}[h]", r"\centering", r"\caption{Global target-loss contrasts. Negative estimates favor GPT-5.6 Sol.}",
              r"\label{tab:global-contrasts}", r"\small", r"\begin{tabular}{lrrrrr}",
              r"\toprule Metric & $\Delta$ loss & SE & 95\% BCa CI & $p_{\rm perm}$ & Holm $p$ \\", r"\midrule"]
    for row in comparisons.itertuples(index=False):
        lines.append(
            f"{row.metric} & {row.estimate:.4f} & {row.standard_error:.4f} & "
            f"[{row.ci_low_bca:.4f},{row.ci_high_bca:.4f}] & "
            f"{row.permutation_p_two_sided:.5f} & {row.holm_p_five_metrics:.5f}" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", r"\FloatBarrier"]
    for metric in ("W1", "TVD"):
        label = metric.lower()
        lines += [
            r"\begin{table}[htbp]", r"\centering", r"\footnotesize", r"\setlength{\tabcolsep}{1.8pt}",
            rf"\caption{{Domain {metric} estimates and paired contrasts. Model cells report estimate (country-bootstrap SE); $\Delta$ is GPT-5.6 Sol minus GPT-5.5 and negative values favor GPT-5.6 Sol.}}\label{{tab:domain-{label}}}",
            r"\begin{tabular}{@{}lrrrrrr@{}}",
            r"\toprule Domain & 5.5 (SE) & 5.6 (SE) & $\Delta$ (SE) & 95\% BCa CI & $p_{\rm perm}$ & Holm $p$ \\",
            r"\midrule",
        ]
        for row in domains[domains.metric == metric].itertuples(index=False):
            lines.append(
                f"{row.domain} & {compact(row.gpt55_estimate)} ({compact(row.gpt55_se)}) & "
                f"{compact(row.gpt56_estimate)} ({compact(row.gpt56_se)}) & "
                f"{compact(row.delta_56_minus_55)} ({compact(row.delta_se)}) & "
                f"[{compact(row.ci_low_bca)},{compact(row.ci_high_bca)}] & "
                f"{compact(row.permutation_p_two_sided, 5)} & {compact(row.holm_p_within_metric, 5)}" + r" \\"
            )
        lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    lines += [r"\FloatBarrier",
              r"\begin{table}[h]", r"\centering", r"\caption{Q121 label-conflict sensitivity. The relabeling scenarios move the stated fraction of each model's category-1 mass to category 2; they bound scoring effects and do not recreate model generation.}",
              r"\label{tab:q121-sensitivity}", r"\small", r"\begin{tabular}{llrrr}",
              r"\toprule Scenario & Metric & $\Delta$ & 95\% BCa CI & Holm $p$ \\", r"\midrule"]
    short_scenario = {0.0: "as collected", 0.5: r"50\% shift", 1.0: r"100\% shift"}
    for row in q121.itertuples(index=False):
        lines.append(
            f"{short_scenario[row.shift_fraction]} & {row.metric} & {row.delta_56_minus_55:.4f} & "
            f"[{row.delta_ci_low_bca:.4f},{row.delta_ci_high_bca:.4f}] & "
            f"{row.holm_p_two_metrics:.4f}" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}",
              r"\begin{table}[h]", r"\centering", r"\caption{Conditional uncertainty decomposition. These centered sensitivity intervals hold countries fixed; they complement, not replace, Table~\ref{tab:global-contrasts}.}",
              r"\label{tab:conditional-uncertainty}", r"\small", r"\begin{tabular}{llrr}",
              r"\toprule Source & Metric & Conditional SE & Centered 95\% interval \\", r"\midrule"]
    source_short = {
        "human multinomial cells, fixed countries and model means": "human cells",
        "five-generation resampling, fixed countries and human cells": "five generations",
    }
    for row in conditional.itertuples(index=False):
        lines.append(
            f"{source_short[row.uncertainty_source]} & {row.metric} & "
            f"{row.conditional_standard_error:.4f} & "
            f"[{row.centered_sensitivity_interval_low_95:.4f},{row.centered_sensitivity_interval_high_95:.4f}]"
            + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", r"\FloatBarrier",
              r"\begin{table}[htbp]", r"\centering", r"\footnotesize", r"\setlength{\tabcolsep}{2.0pt}",
              r"\caption{Signed expected-score bias by model and domain. Positive values indicate a higher expected directed response than the human derivative; these signs are descriptive, not normative.}\label{tab:signed-bias}",
              r"\begin{tabular}{@{}llrrrrr@{}}",
              r"\toprule Model & Domain & Bias & SE & 95\% BCa CI & $p_{\rm perm}$ & Holm $p$ \\", r"\midrule"]
    for row in bias.itertuples(index=False):
        lines.append(
            f"{row.model} & {row.domain} & {compact(row.mean_signed_bias)} & {compact(row.standard_error)} & "
            f"[{compact(row.ci_low_bca)},{compact(row.ci_high_bca)}] & "
            f"{compact(row.permutation_p_two_sided, 5)} & {compact(row.holm_p_within_model, 5)}" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}",
              r"\begin{table}[h]", r"\centering",
              r"\caption{Bootstrap-draw convergence. Values are the maximum absolute movement, across the two models, of either percentile-interval endpoint between 10,000 and 20,000 country resamples.}\label{tab:bootstrap-convergence}",
              r"\small", r"\begin{tabular}{lr}",
              r"\toprule Metric & Maximum endpoint movement \\", r"\midrule"]
    for metric in ("W1", "TVD", "CRG", "VDR", "CSR"):
        subset = convergence[convergence.quantity.str.endswith("_" + metric)]
        piv = subset.pivot(index="quantity", columns="draws_used", values=["percentile_ci_low", "percentile_ci_high"])
        shifts = []
        for _, row in piv.iterrows():
            shifts.extend([
                abs(row[("percentile_ci_low", 20000)] - row[("percentile_ci_low", 10000)]),
                abs(row[("percentile_ci_high", 20000)] - row[("percentile_ci_high", 10000)]),
            ])
        lines.append(f"{metric} & {max(shifts):.5f}" + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}",
              r"\begin{table}[h]", r"\centering", r"\caption{Within-cell run instability across five generations. Values summarize the SD across generations within each country--question cell.}",
              r"\label{tab:run-stability}", r"\small", r"\begin{tabular}{llrrr}",
              r"\toprule Model & Scope & Cells & Mean SD W1 & Mean SD TVD \\", r"\midrule"]
    for row in stability.itertuples(index=False):
        if row.scope == "All six anchors":
            lines.append(
                f"{row.model} & all anchors & {row.country_question_cells} & "
                f"{row.mean_within_cell_sd_w1:.4f} & {row.mean_within_cell_sd_tvd:.4f}" + r" \\"
            )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}", r"\FloatBarrier"]
    (PAPER_TABLES / "appendix_full_results.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def generated_spatial_tables() -> None:
    diagnostics = pd.read_csv(RESULTS / "spatial_diagnostics.csv")
    primary = diagnostics[(diagnostics.knn_k == 4) & (diagnostics.model_or_contrast == "GPT-5.6 Sol minus GPT-5.5")]
    sem = pd.read_csv(RESULTS / "spatial_error_models.csv")
    hac = pd.read_csv(RESULTS / "spatial_hac_contrasts.csv")
    lines = [
        r"\begin{table}[h]", r"\centering", r"\caption{Primary $k=4$ global spatial diagnostics for version contrasts. BH adjustment spans all 24 primary outcomes, including version-specific levels.}",
        r"\label{tab:spatial-global}", r"\small", r"\begin{tabular}{llrrrr}",
        r"\toprule Family & Outcome & Moran $I$ & BH $q$ & Geary $C$ & BH $q$ \\", r"\midrule",
    ]
    for row in primary.itertuples(index=False):
        lines.append(
            f"{row.outcome_family.replace('_',' ')} & {row.outcome} & {row.moran_i:.3f} & "
            f"{row.moran_bh_q_primary_family:.3f} & {row.geary_c:.3f} & "
            f"{row.geary_bh_q_primary_family:.3f}" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}",
              r"\begin{longtable}{llrrrrr}", r"\caption{Maximum-likelihood spatial-error models of W1 version contrasts. The coefficient is an intercept/mean; $\lambda$ captures residual spatial dependence.}\label{tab:sem-full}\\",
              r"\toprule $k$ & Scope & Mean & SE & 95\% CI & Holm $p$ & $\lambda$ ($p$) \\", r"\midrule\endfirsthead",
              r"\toprule $k$ & Scope & Mean & SE & 95\% CI & Holm $p$ & $\lambda$ ($p$) \\", r"\midrule\endhead"]
    for row in sem.itertuples(index=False):
        lines.append(
            f"{int(row.knn_k)} & {row.scope} & {row.mean_delta_w1:.4f} & {row.standard_error:.4f} & "
            f"[{row.ci_low_95:.4f},{row.ci_high_95:.4f}] & {row.holm_p_seven_scopes:.4f} & "
            f"{row.spatial_error_lambda:.3f} ({row.lambda_p_value_two_sided:.3f})" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{longtable}",
              r"\begin{table}[h]", r"\centering", r"\caption{Spatial-HAC sensitivity for the overall and government-responsibility W1 contrasts. Holm correction spans eight outcomes within each cutoff.}",
              r"\label{tab:hac-selected}", r"\small", r"\begin{tabular}{lrrrrr}",
              r"\toprule Scope & Cutoff km & Mean & HAC SE & 95\% CI & Holm $p$ \\", r"\midrule"]
    selected = hac[(hac.scope.isin(["All six anchors", "Market"])) & (hac.metric == "W1")]
    for row in selected.itertuples(index=False):
        lines.append(
            f"{row.scope} & {int(row.cutoff_km)} & {row.estimate:.4f} & "
            f"{row.spatial_hac_standard_error:.4f} & [{row.ci_low_95:.4f},{row.ci_high_95:.4f}] & "
            f"{row.holm_p_eight_outcomes_within_cutoff:.4f}" + r" \\"
        )
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{table}"]
    (PAPER_TABLES / "appendix_spatial_tables.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    style()
    PAPER_FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    PAPER_TABLES.mkdir(parents=True, exist_ok=True)
    figure_design_bridge()
    figure_results()
    figure_uncertainty()
    main_table()
    appendix_tables_and_data()
    generated_tutorial_tables()
    generated_full_results_tables()
    generated_spatial_tables()
    print("PASS: legacy table and appendix tutorial/coverage assets generated; v1.0 owns displayed figures")


if __name__ == "__main__":
    main()
