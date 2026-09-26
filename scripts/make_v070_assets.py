#!/usr/bin/env python3
"""Generate v0.7.0 figures and tables from released source data.

This script runs after ``make_wave1_assets.py`` and deliberately replaces the
visual assets and spatial summary table with versions that reflect
the joint 12-outcome inference, finite-five-generation composition diagnostic,
and exploratory creative-destruction margins.
"""

from __future__ import annotations

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

import make_wave1_assets as base
from make_visual_story_v070 import postprocess_svg


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"
RESULTS = EXP / "results"
FIGURES = ROOT / "results/figures"
RESULT_FIGURES = ROOT / "results/figures"
SOURCES = ROOT / "assets/figure_sources/data"

NAVY = "#17324D"
BLUE = "#2869A6"
TEAL = "#008F80"
MAGENTA = "#B23A6F"
ORANGE = "#C66A16"
GRAY = "#66717E"
LIGHT = "#F3F5F7"
GRID = "#D7DDE3"


def style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "font.size": 8.5,
        "axes.titlesize": 9.2,
        "axes.labelsize": 8.3,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.7,
        "legend.fontsize": 7.2,
        "axes.linewidth": 0.6,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ethosgpt-v0.7.0",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def save(fig: plt.Figure, stem: str) -> None:
    # These v0.7 stems were replaced in v1.0. Keep this stage for tables and
    # supporting analysis assets without restoring retired displayed figures.
    if stem in {"fig1_wave1_design", "fig2_wave1_results", "figS2_spatial_maps"}:
        return
    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    metadata = {"Creator": "EthosGPT v0.7.0 reproducible figure pipeline"}
    fig.savefig(RESULT_FIGURES / f"{stem}.pdf", metadata=metadata)
    fig.savefig(RESULT_FIGURES / f"{stem}.svg", metadata=metadata)
    postprocess_svg(RESULT_FIGURES / f"{stem}.svg", stem.replace("_", " "))


def _rounded_box(ax: plt.Axes, xy: tuple[float, float], wh: tuple[float, float],
                 edge: str, fill: str = "white", linestyle: str = "-") -> FancyBboxPatch:
    box = FancyBboxPatch(
        xy, *wh, boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=1.0, edgecolor=edge, facecolor=fill, linestyle=linestyle,
        transform=ax.transAxes,
    )
    ax.add_patch(box)
    return box


def _survey_icon(ax: plt.Axes, x: float, y: float, color: str) -> None:
    for shift in (0.018, 0.009, 0):
        ax.add_patch(Rectangle((x + shift, y + shift), .070, .105,
                               transform=ax.transAxes, fc="white", ec=color, lw=.75))
    for index, width in enumerate((.042, .052, .033)):
        ax.plot([x + .014, x + .014 + width], [y + .078 - index * .026] * 2,
                transform=ax.transAxes, color=color, lw=1.0)


def _chip_icon(ax: plt.Axes, x: float, y: float, color: str) -> None:
    ax.add_patch(FancyBboxPatch((x, y), .075, .075, boxstyle="round,pad=.007",
                                transform=ax.transAxes, fc=LIGHT, ec=color, lw=.85))
    for offset in (.012, .030, .048, .066):
        ax.plot([x + offset, x + offset], [y - .010, y], transform=ax.transAxes, color=color, lw=.7)
        ax.plot([x + offset, x + offset], [y + .075, y + .085], transform=ax.transAxes, color=color, lw=.7)
    ax.text(x + .0375, y + .038, "LM", ha="center", va="center", fontsize=6.8,
            color=color, weight="bold", transform=ax.transAxes)


def figure_evidence_boundary() -> None:
    """One-claim design figure with an explicit observed/derived boundary."""
    fig, ax = plt.subplots(figsize=(5.48, 1.62))
    ax.set_axis_off()
    ax.text(.01, .965, "What is measured, what is derived, and what is implied",
            transform=ax.transAxes, ha="left", va="top", fontsize=10.2,
            weight="bold", color=NAVY)

    cards = [
        (.015, "Survey evidence", "64 countries\n6 value anchors", NAVY),
        (.265, "Paired model audit", "GPT-5.5 vs\nGPT-5.6 Sol · 5 runs", BLUE),
        (.515, "Measured shifts", "fidelity, geometry,\nspace, composition", TEAL),
    ]
    for x, title, subtitle, color in cards:
        _rounded_box(ax, (x, .19), (.205, .60), color)
        ax.text(x + .1025, .42, title, transform=ax.transAxes, ha="center",
                va="center", color=NAVY, fontsize=8.4, weight="bold")
        ax.text(x + .1025, .29, subtitle, transform=ax.transAxes, ha="center",
                va="center", color=GRAY, fontsize=7.3, linespacing=1.12)
    _survey_icon(ax, .078, .565, NAVY)
    _chip_icon(ax, .303, .58, BLUE)
    _chip_icon(ax, .374, .58, BLUE)
    # Geometry/composition icon.
    nodes = [(.563, .603), (.617, .670), (.673, .589)]
    for first, second in ((0, 1), (1, 2), (0, 2)):
        ax.plot([nodes[first][0], nodes[second][0]], [nodes[first][1], nodes[second][1]],
                color=TEAL, lw=.9, transform=ax.transAxes)
    for x, y in nodes:
        ax.add_patch(Circle((x, y), .011, transform=ax.transAxes, fc=TEAL, ec="white", lw=.5))
    for x in (.232, .482):
        ax.annotate("", xy=(x + .025, .49), xytext=(x, .49), xycoords=ax.transAxes,
                    arrowprops=dict(arrowstyle="-|>", color=GRAY, lw=1.0))

    _rounded_box(ax, (.765, .19), (.215, .60), MAGENTA, fill="#FCF5F8", linestyle="--")
    ax.text(.8725, .66, "Economic implications", transform=ax.transAxes,
            ha="center", va="center", color=NAVY, fontsize=8.4, weight="bold")
    ax.text(.8725, .51, "opportunity\nadjustment\ncoordination", transform=ax.transAxes,
            ha="center", va="center", color=GRAY, fontsize=7.3, linespacing=1.12)
    # Three policy sliders.
    for i, position in enumerate((.827, .900, .857)):
        y = .325 - .045 * i
        ax.plot([.813, .932], [y, y], transform=ax.transAxes, color=GRID, lw=2.0,
                solid_capstyle="round")
        ax.add_patch(Circle((position, y), .008, transform=ax.transAxes,
                            fc=MAGENTA, ec="white", lw=.5))
    ax.annotate("", xy=(.758, .49), xytext=(.733, .49), xycoords=ax.transAxes,
                arrowprops=dict(arrowstyle="-|>", color=MAGENTA, lw=1.0, linestyle="--"))
    ax.text(.50, .07, "solid = directly estimated or algebraically derived     dashed = theory-indexed implication",
            transform=ax.transAxes, ha="center", va="center", color=GRAY, fontsize=7.1)
    save(fig, "fig1_wave1_design")
    plt.close(fig)

    # Minimal editable draw.io source for the conceptual figure.
    drawio = '''<mxfile host="app.diagrams.net" modified="2026-09-03T00:00:00.000Z" agent="EthosGPT" version="24.7.17">
  <diagram id="ethosgpt-evidence" name="Evidence boundary">
    <mxGraphModel dx="1200" dy="700" grid="1" gridSize="10" page="1" pageWidth="1100" pageHeight="500">
      <root><mxCell id="0"/><mxCell id="1" parent="0"/>
        <mxCell id="2" value="Survey evidence&#xa;64 countries · 6 anchors" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#17324D;fontFamily=Times New Roman;fontSize=16;" vertex="1" parent="1"><mxGeometry x="30" y="120" width="220" height="150" as="geometry"/></mxCell>
        <mxCell id="3" value="Paired model audit&#xa;2 versions × 5 runs" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#2869A6;fontFamily=Times New Roman;fontSize=16;" vertex="1" parent="1"><mxGeometry x="300" y="120" width="220" height="150" as="geometry"/></mxCell>
        <mxCell id="4" value="Measured shifts&#xa;fidelity · geometry · space · composition" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#008F80;fontFamily=Times New Roman;fontSize=16;" vertex="1" parent="1"><mxGeometry x="570" y="120" width="220" height="150" as="geometry"/></mxCell>
        <mxCell id="5" value="Economic implications&#xa;opportunity · adjustment · coordination" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#B23A6F;dashed=1;fillColor=#FCF5F8;fontFamily=Times New Roman;fontSize=16;" vertex="1" parent="1"><mxGeometry x="840" y="120" width="230" height="150" as="geometry"/></mxCell>
        <mxCell id="6" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#66717E;" edge="1" parent="1" source="2" target="3"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="7" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#66717E;" edge="1" parent="1" source="3" target="4"><mxGeometry relative="1" as="geometry"/></mxCell>
        <mxCell id="8" style="edgeStyle=orthogonalEdgeStyle;rounded=0;html=1;endArrow=block;strokeColor=#B23A6F;dashed=1;" edge="1" parent="1" source="4" target="5"><mxGeometry relative="1" as="geometry"/></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
    (FIGURES / "fig1_wave1_design.drawio").unlink(missing_ok=True)


def _forest(ax: plt.Axes, data: pd.DataFrame, label: str, estimate: str,
            low: str, high: str, significant: str, title: str,
            marker: str = "o", xlim: tuple[float, float] | None = None) -> None:
    frame = data.reset_index(drop=True)
    y = np.arange(len(frame))[::-1]
    ax.axvline(0, color=NAVY, lw=.8, zorder=0)
    for index, row in frame.iterrows():
        value = float(row[estimate])
        color = TEAL if value < 0 else MAGENTA
        ax.plot([row[low], row[high]], [y[index], y[index]], color=color,
                lw=1.55, solid_capstyle="round")
        filled = bool(row[significant])
        ax.scatter(value, y[index], marker=marker, s=31,
                   facecolor=color if filled else "white", edgecolor=color,
                   linewidth=1.0, zorder=3)
    ax.set_yticks(y, frame[label])
    if xlim:
        ax.set_xlim(*xlim)
    ax.grid(axis="x", color=GRID, lw=.45)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", color=NAVY, weight="bold", pad=3)


def figure_main_results() -> None:
    global_data = pd.read_csv(RESULTS / "metric_comparisons.csv")
    global_data["label"] = global_data["metric"].map({
        "W1": "W1", "TVD": "TVD", "CRG": "CRG", "VDR": "|VDR−1|", "CSR": "1−CSR",
    })
    global_data["sig"] = global_data["holm_p_five_metrics"] <= .05
    joint = pd.read_csv(RESULTS / "joint_item_inference.csv")
    short = {
        "Agency (Q48)": "Q48 Agency", "Trust (Q57)": "Q57 Trust",
        "Income distribution (Q106)": "Q106 Distribution",
        "Responsibility (Q108)": "Q108 Responsibility",
        "Immigration (Q121)": "Q121 Immigration*",
        "Science opportunity (Q159)": "Q159 Science",
    }
    joint["label"] = joint["display_label"].map(short)
    joint["sig"] = joint["joint_max_t_p_fwer"] <= .05
    w1 = joint[joint.metric == "W1"].copy()
    tvd = joint[joint.metric == "TVD"].copy()
    composition = pd.read_csv(RESULTS / "composition_summary.csv")

    fig = plt.figure(figsize=(5.48, 3.15))
    grid = fig.add_gridspec(2, 3, height_ratios=(.78, 1.35), width_ratios=(.90, 1.15, 1.15),
                           hspace=.45, wspace=.60)
    ax_a = fig.add_subplot(grid[0, 0])
    ax_c = fig.add_subplot(grid[0, 1:])
    ax_b1 = fig.add_subplot(grid[1, 0:2])
    ax_b2 = fig.add_subplot(grid[1, 2])

    _forest(ax_a, global_data, "label", "estimate", "ci_low_bca", "ci_high_bca", "sig",
            "A  Global metrics", marker="o", xlim=(-.060, .090))

    # Item results: W1 circles and TVD squares, with shared y positions.
    labels = list(w1["label"])
    y = np.arange(len(labels))[::-1]
    ax_b1.axvline(0, color=NAVY, lw=.8)
    for offset, frame, marker, metric in ((.12, w1, "o", "W1"), (-.12, tvd, "s", "TVD")):
        for index, row in frame.reset_index(drop=True).iterrows():
            value = row.delta_56_minus_55
            color = TEAL if value < 0 else MAGENTA
            yy = y[index] + offset
            ax_b1.plot([row.simultaneous_ci_low_95, row.simultaneous_ci_high_95], [yy, yy],
                       color=color, lw=1.35)
            filled = row.joint_max_t_p_fwer <= .05
            ax_b1.scatter(value, yy, s=27, marker=marker,
                          facecolor=color if filled else "white", edgecolor=color,
                          linewidth=.95, zorder=3)
    ax_b1.set_yticks(y, labels)
    ax_b1.set_xlim(-.043, .023)
    ax_b1.set_xlabel("Error change with simultaneous 95% interval")
    ax_b1.set_title("B  Item changes, joint 12-outcome family", loc="left",
                    color=NAVY, weight="bold", pad=3)
    ax_b1.grid(axis="x", color=GRID, lw=.45)
    ax_b1.spines[["top", "right", "left"]].set_visible(False)
    ax_b1.tick_params(axis="y", length=0)
    marker_legend = [
        Line2D([0], [0], marker="o", color="none", markeredgecolor=NAVY,
               markerfacecolor="white", label="W1", markersize=4.8),
        Line2D([0], [0], marker="s", color="none", markeredgecolor=NAVY,
               markerfacecolor="white", label="TVD", markersize=4.8),
        Line2D([0], [0], marker="o", color="none", markeredgecolor=TEAL,
               markerfacecolor=TEAL, label="joint p ≤ .05", markersize=4.8),
    ]

    # Composition diagnostic: exact decomposition of single-generation error.
    models = ["GPT-5.5", "GPT-5.6 Sol"]
    residual = []
    reducible = []
    shares = []
    for model in models:
        subset = composition[composition.comparison == model].set_index("component")
        residual.append(subset.loc["five_run_residual", "estimate"])
        reducible.append(subset.loc["reducible_generation_component", "estimate"])
        shares.append(subset.loc["share_of_individual_error_removed_by_five_generation_average", "estimate"])
    xpos = np.arange(2)
    ax_c.bar(xpos, residual, width=.52, color=BLUE, label="five-run residual")
    ax_c.bar(xpos, reducible, width=.52, bottom=residual, color=ORANGE,
             label="generation-varying part")
    ax_c.set_xticks(xpos, models)
    ax_c.set_xlim(-.5, 2.15)
    ax_c.set_ylim(0, max(np.add(residual, reducible)) * 1.18)
    ax_c.spines[["top", "right"]].set_visible(False)
    ax_c.grid(axis="y", color=GRID, lw=.45)
    ax_c.set_title("C  Squared error: residual vs varying", loc="left",
                   color=NAVY, weight="bold", pad=3)
    for index, share in enumerate(shares):
        ax_c.text(index, residual[index] + reducible[index] + .004,
                  f"{100*share:.2f}% removed", ha="center", va="bottom", fontsize=7.4,
                  color=NAVY)
    ax_c.legend(frameon=False, loc="center right", bbox_to_anchor=(1.0, .43))
    ax_b2.set_axis_off()
    ax_b2.text(.02, .92, "Interpretation", transform=ax_b2.transAxes, color=NAVY,
               weight="bold", fontsize=8.8)
    ax_b2.text(.02, .79,
               "Joint correction:\nQ108 W1/TVD;\nQ106 TVD.\n\nAveraging removes\nonly 1.2–1.3%.",
               transform=ax_b2.transAxes, ha="left", va="top", fontsize=7.6,
               color=GRAY, linespacing=1.18)
    ax_b2.legend(handles=marker_legend, frameon=False, ncol=1, loc="lower left",
                 bbox_to_anchor=(0, .01), handletextpad=.25, labelspacing=.18,
                 borderaxespad=0)
    save(fig, "fig2_wave1_results")
    plt.close(fig)


def _country_changes() -> pd.DataFrame:
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    aggregate = scores.groupby(["model", "country"], as_index=False).agg(tvd=("tvd", "mean"))
    wide = aggregate.pivot(index="country", columns="model", values="tvd")
    wide["delta_tvd"] = wide["GPT-5.6 Sol"] - wide["GPT-5.5"]
    crg = base.country_crg(scores).set_index("country")[["delta_crg"]]
    coords = pd.read_csv(EXP / "inputs/country_coordinates.csv").set_index("country")
    return wide[["delta_tvd"]].join(crg).join(coords).reset_index()


def figure_spatial_maps() -> None:
    changes = _country_changes()
    world_path = Path(gpd.__file__).resolve().parent / "datasets/naturalearth_lowres/naturalearth_lowres.shp"
    world = gpd.read_file(world_path)
    fig, axes = plt.subplots(2, 1, figsize=(5.48, 4.15))
    for ax, column, title in zip(
        axes, ("delta_tvd", "delta_crg"),
        ("A  Country-level change in distribution error (TVD)",
         "B  Country-level change in standardized profile gap (CRG)"), strict=True,
    ):
        world.plot(ax=ax, color="#F1F3F5", edgecolor="#C5CCD3", linewidth=.3)
        bound = float(changes[column].abs().max())
        threshold = .10 * bound
        groups = (
            (changes[column] < -threshold, TEAL, "v", "lower error"),
            (changes[column].abs() <= threshold, GRAY, "o", "near zero"),
            (changes[column] > threshold, MAGENTA, "^", "higher error"),
        )
        for mask, color, marker, _ in groups:
            subset = changes.loc[mask]
            sizes = 20 + 42 * subset[column].abs().to_numpy() / bound
            ax.scatter(subset.longitude, subset.latitude, c=color, s=sizes, marker=marker,
                       ec="white", lw=.35, zorder=3)
        ax.set_xlim(-177, 181); ax.set_ylim(-58, 85); ax.set_aspect("auto"); ax.set_axis_off()
        ax.set_title(title, loc="left", color=NAVY, weight="bold", pad=2)
        handles = [Line2D([0], [0], marker=marker, color="none", markerfacecolor=color,
                          markeredgecolor="white", markersize=6.2, label=label)
                   for _, color, marker, label in groups]
        ax.legend(handles=handles, frameon=False, loc="lower center", ncol=3,
                  bbox_to_anchor=(.5, -.02), handletextpad=.25, columnspacing=.9)
    fig.text(.01, .006, "Locations describe geographic patterning only; they do not identify spatial spillovers or culturally homogeneous regions.", fontsize=7.1, color=GRAY)
    fig.tight_layout(rect=(0, .03, 1, 1))
    save(fig, "figS2_spatial_maps")
    plt.close(fig)


def figure_economic_surface() -> None:
    data = pd.read_csv(RESULTS / "economic_weight_surface.csv")
    opportunity = data.weight_opportunity_participation.to_numpy()
    distribution = data.weight_distribution_adjustment.to_numpy()
    coordination = data.weight_coordination_legitimacy.to_numpy()
    x = distribution + .5 * coordination
    y = np.sqrt(3) / 2 * coordination
    values = data.delta_weighted_loss_56_minus_55.to_numpy()
    bound = max(abs(values.min()), abs(values.max()))
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
    cmap = LinearSegmentedColormap.from_list("ethos_econ", [TEAL, "#F7F7F7", MAGENTA])
    fig, ax = plt.subplots(figsize=(5.48, 3.72))
    triang = mpl.tri.Triangulation(x, y)
    levels = np.linspace(-bound, bound, 11)
    ax.tricontourf(triang, values, levels=levels, cmap=cmap, norm=norm, antialiased=True)
    triangle = np.array([[0, 0], [1, 0], [.5, np.sqrt(3)/2], [0, 0]])
    ax.plot(triangle[:, 0], triangle[:, 1], color=NAVY, lw=.8)
    # Boundary where the point estimate equals zero.
    ax.tricontour(triang, values, levels=[0], colors=[NAVY], linewidths=1.1, linestyles="--")
    ax.text(-.035, -.035, "Opportunity and\nparticipation", ha="left", va="top", color=NAVY, weight="bold")
    ax.text(1.035, -.035, "Distribution and\nadjustment", ha="right", va="top", color=NAVY, weight="bold")
    ax.text(.5, np.sqrt(3)/2 + .035, "Coordination and legitimacy", ha="center", va="bottom", color=NAVY, weight="bold")
    ax.set_xlim(-.08, 1.08); ax.set_ylim(-.09, .96); ax.set_aspect("equal"); ax.set_axis_off()
    ax.set_title("Creative-destruction margin sensitivity", loc="left", color=NAVY, weight="bold")
    fig.subplots_adjust(left=.08, right=.92, top=.90, bottom=.24)
    fig.text(.50, .125,
             f"teal: lower loss   ·   magenta: higher loss   ·   point-estimate range {values.min():.4f} to {values.max():+.4f}",
             ha="center", va="center", color=GRAY, fontsize=7.2)
    fig.text(.50, .080,
             "dashed line: equal point loss; intervals, not this line alone, determine robustness",
             ha="center", va="center", color=GRAY, fontsize=7.2)
    fig.text(.50, .025, "Exploratory, theory-indexed sensitivity over nonnegative weights summing to one; not an estimate of welfare or realized policy effects.", ha="center", fontsize=7.1, color=GRAY)
    save(fig, "figS3_economic_sensitivity")
    plt.close(fig)


def fmt(value: float, digits: int = 3) -> str:
    if pd.isna(value):
        return "--"
    return f"{float(value):.{digits}f}"


def copy_sources() -> None:
    SOURCES.mkdir(parents=True, exist_ok=True)
    names = [
        "metric_comparisons.csv", "metric_estimates.csv", "joint_item_inference.csv",
        "composition_summary.csv", "economic_margin_results.csv", "economic_scenarios.csv",
        "economic_weight_surface.csv", "economic_weight_surface_summary.csv",
        "leave_one_region_out.csv", "human_cell_count_quartile_sensitivity.csv",
        "spatial_error_models.csv", "spatial_hac_contrasts.csv", "spatial_diagnostics.csv",
        "conditional_uncertainty_contrasts.csv", "bootstrap_convergence.csv",
        "q121_prompt_deviation_sensitivity.csv", "country_coverage_and_human_cell_counts.csv",
        "run_stability.csv", "token_usage.csv",
    ]
    for name in names:
        shutil.copy2(RESULTS / name, SOURCES / name)
    _country_changes().to_csv(SOURCES / "country_level_spatial_changes.csv", index=False)


def main() -> None:
    copy_sources()
    print("PASS: derived figure-source CSV inputs regenerated")

if __name__ == "__main__":
    main()
