#!/usr/bin/env python3
"""Build the EthosGPT v1.0.0 acceptance-oriented visual system.

The visual sequence follows the paper's evidence path:

1. a nested benchmark-to-audit-to-frontier argument with an editable draw.io master,
2. a four-view statistical synthesis using decision-tree-selected idioms,
3. the theory-indexed economic sensitivity summary,
4. conditional-versus-country uncertainty diagnostics,
5. an appendix methods overview, and
6. the continuous economic-weight surface.

Every quantitative mark is regenerated from released CSV files.  PDF and SVG
are authoritative; PNG files are previews only.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET
import warnings
from urllib.parse import quote

os.environ.setdefault("SOURCE_DATE_EPOCH", "1788566400")
os.environ.setdefault("TZ", "UTC")

import geopandas as gpd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.lines import Line2D
from matplotlib.patches import (
    Arc,
    Circle,
    ConnectionPatch,
    FancyArrowPatch,
    FancyBboxPatch,
    Rectangle,
)
import numpy as np
import pandas as pd
from scipy.stats import gaussian_kde


ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"
RESULTS = EXP / "results"
FIGURES = ROOT / "paper/figs"
RESULT_FIGURES = ROOT / "results/figures"
SOURCES = ROOT / "paper/figure_sources"
SOURCE_DATA = SOURCES / "data"

VERSION = "1.0.0"

# Named-role palette: energetic enough for scanning, restrained enough for print.
INK = "#18324A"
PRIMARY = "#3B5CCC"       # GPT-5.5 / comparison path
TEAL = "#078C82"          # GPT-5.6 / lower error
MAGENTA = "#B33B72"       # higher error / contrasting direction
AMBER = "#D88A24"         # finite-run component / status
GRAY = "#6B7786"
GRAY_DARK = "#4E5B68"
GRAY_LIGHT = "#AAB4BF"
DIST = "#667687"          # neutral distribution summaries
DIST_LIGHT = "#EEF2F5"
SURFACE = "#F6F8FB"
COOL = "#EAF0FF"
TEAL_LIGHT = "#E5F4F1"
WARM = "#FFF3E8"
DIVIDER = "#D6DEE7"
WHITE = "#FFFFFF"


def set_style() -> None:
    """Lock final-size typography and vector export behavior."""
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Nimbus Roman", "Times New Roman", "Times", "Liberation Serif"],
        "font.size": 7.8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 7.6,
        "xtick.labelsize": 7.1,
        "ytick.labelsize": 7.1,
        "legend.fontsize": 7.0,
        "axes.linewidth": 0.65,
        "axes.edgecolor": INK,
        "text.color": INK,
        "axes.labelcolor": INK,
        "xtick.color": GRAY_DARK,
        "ytick.color": GRAY_DARK,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ethosgpt-v1.0.0",
        "savefig.bbox": None,
        "savefig.pad_inches": 0,
        "figure.facecolor": WHITE,
        "axes.facecolor": WHITE,
    })


def postprocess_svg(path: Path, title: str) -> None:
    """Retain live text, add an accessible title, and simplify safe clipping."""
    tree = ET.parse(path)
    root = tree.getroot()
    namespace = "http://www.w3.org/2000/svg"
    ET.register_namespace("", namespace)
    for element in list(root):
        if element.tag == f"{{{namespace}}}title":
            root.remove(element)
    for element in root.iter():
        element.attrib.pop("clip-path", None)
    title_element = ET.Element(f"{{{namespace}}}title")
    title_element.text = title
    root.insert(0, title_element)
    if not root.get("width") or not root.get("height"):
        viewbox = (root.get("viewBox") or "0 0 395 250").split()
        root.set("width", viewbox[2])
        root.set("height", viewbox[3])
    tree.write(path, encoding="utf-8", xml_declaration=True)


def save(fig: plt.Figure, stem: str, title: str) -> None:
    """Write synchronized publication and preview formats."""
    metadata = {"Creator": f"EthosGPT v{VERSION} reproducible visual pipeline"}
    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    for directory in (RESULT_FIGURES,):
        fig.savefig(directory / f"{stem}.pdf", metadata=metadata)
        fig.savefig(directory / f"{stem}.svg", metadata=metadata)
        fig.savefig(directory / f"{stem}.png", dpi=360, metadata=metadata)
        postprocess_svg(directory / f"{stem}.svg", title)
    for suffix in (".pdf", ".svg", ".png"):
        shutil.copy2(RESULT_FIGURES / f"{stem}{suffix}", FIGURES / f"{stem}{suffix}")


def panel_title(ax: plt.Axes, label: str, title: str, pad: float = 3.0) -> None:
    ax.set_title(f"{label}  {title}", loc="left", pad=pad, color=INK, weight="bold")


def clean_axes(ax: plt.Axes, *, left: bool = False, bottom: bool = True) -> None:
    hidden = ["top", "right"]
    if not left:
        hidden.append("left")
        ax.tick_params(axis="y", length=0)
    if not bottom:
        hidden.append("bottom")
        ax.tick_params(axis="x", length=0)
    ax.spines[hidden].set_visible(False)


def _country_changes() -> pd.DataFrame:
    """Rebuild country-level TVD and CRG changes from the released score file."""
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    domains = ["Agency", "Trust", "Distribution", "Market", "Inclusion", "Science"]
    human = (
        scores.drop_duplicates(["country", "domain"])
        .pivot(index="country", columns="domain", values="human_directed")
        .reindex(columns=domains)
    )
    sigma = human.std(ddof=1)
    crg_columns: dict[str, pd.Series] = {}
    for model in ("GPT-5.5", "GPT-5.6 Sol"):
        values = (
            scores[scores.model == model]
            .pivot(index="country", columns="domain", values="model_directed")
            .reindex(columns=domains)
        )
        crg_columns[model] = np.sqrt(np.square((values - human) / sigma).mean(axis=1))
    crg = pd.DataFrame(crg_columns)
    crg["delta_crg"] = crg["GPT-5.6 Sol"] - crg["GPT-5.5"]

    tvd = (
        scores.groupby(["model", "country"], as_index=False)
        .agg(tvd=("tvd", "mean"))
        .pivot(index="country", columns="model", values="tvd")
    )
    tvd["delta_tvd"] = tvd["GPT-5.6 Sol"] - tvd["GPT-5.5"]
    coords = (
        pd.read_csv(EXP / "inputs/country_coordinates.csv")
        .set_index("country")[["longitude", "latitude"]]
    )
    regions = (
        scores.drop_duplicates("country")[["country", "cultural_region"]]
        .set_index("country")
    )
    frame = tvd[["delta_tvd"]].join(crg[["delta_crg"]]).join(coords).join(regions)
    frame = frame.reset_index()
    assert len(frame) == 64 and frame[["delta_tvd", "delta_crg", "longitude", "latitude"]].notna().all().all()
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    frame.to_csv(SOURCE_DATA / "country_level_spatial_changes.csv", index=False)
    return frame


PROFILE_DOMAINS = ["Agency", "Trust", "Distribution", "Market", "Inclusion", "Science"]
PROFILE_LABELS = ["Agency", "Trust", "Distrib.", "Responsib.", "Immigr.", "Science"]
PROFILE_MODELS = ("GPT-5.5", "GPT-5.6 Sol")


def _medoid(frame: pd.DataFrame) -> str:
    """Return the observed row minimizing mean Euclidean distance to its peers."""
    ordered = frame.sort_index()
    values = ordered.to_numpy(float)
    distances = np.sqrt(np.square(values[:, None, :] - values[None, :, :]).sum(axis=2))
    mean_distance = pd.Series(distances.mean(axis=1), index=ordered.index)
    return str(mean_distance.sort_values(kind="mergesort").index[0])


def _country_profile_cases() -> tuple[
    pd.DataFrame, dict[str, pd.DataFrame], pd.DataFrame, pd.DataFrame, float
]:
    """Select reproducible country-profile cases without calling them populations.

    The main case is the medoid of standardized *human-only* survey coordinates,
    so model outcomes cannot influence its selection. Appendix cases first use
    the declared CRG-change classes and then select the medoid of the two models'
    standardized residual profiles within each class. All 64 countries remain in
    every estimate; these cases are descriptive views, not inferential subsamples.
    """
    scores = pd.read_csv(RESULTS / "country_question_scores.csv")
    human = (
        scores.drop_duplicates(["country", "domain"])
        .pivot(index="country", columns="domain", values="human_directed")
        .reindex(columns=PROFILE_DOMAINS)
        .sort_index()
    )
    model_profiles = {
        model: (
            scores[scores.model == model]
            .pivot(index="country", columns="domain", values="model_directed")
            .reindex(index=human.index, columns=PROFILE_DOMAINS)
        )
        for model in PROFILE_MODELS
    }
    sigma = human.std(ddof=1)
    human_z = (human - human.mean()) / sigma
    main_country = _medoid(human_z)

    crg = pd.DataFrame({
        model: np.sqrt(np.square((model_profiles[model] - human) / sigma).mean(axis=1))
        for model in PROFILE_MODELS
    })
    crg["delta_crg"] = crg["GPT-5.6 Sol"] - crg["GPT-5.5"]
    threshold = .10 * crg.delta_crg.abs().max()
    crg["display_class"] = np.where(
        crg.delta_crg < -threshold,
        "lower",
        np.where(crg.delta_crg > threshold, "higher", "near zero"),
    )

    residual_features = pd.concat(
        [((model_profiles[model] - human) / sigma).add_prefix(f"{model}__")
         for model in PROFILE_MODELS],
        axis=1,
    )
    records = [{
        "selection_role": "main",
        "country": main_country,
        "display_class": str(crg.loc[main_country, "display_class"]),
        "selection_rule": (
            "medoid of the six standardized human-survey coordinates; "
            "model outcomes excluded from selection"
        ),
    }]
    for display_class in ("lower", "near zero", "higher"):
        eligible = crg.index[crg.display_class == display_class]
        country = _medoid(residual_features.loc[eligible])
        records.append({
            "selection_role": f"appendix_{display_class.replace(' ', '_')}",
            "country": country,
            "display_class": display_class,
            "selection_rule": (
                "medoid of the two standardized model-minus-human residual profiles "
                f"within the threshold-defined {display_class} CRG-change class"
            ),
        })
    cases = pd.DataFrame(records)
    cases["crg_gpt55"] = cases.country.map(crg["GPT-5.5"])
    cases["crg_gpt56"] = cases.country.map(crg["GPT-5.6 Sol"])
    cases["delta_crg"] = cases.country.map(crg.delta_crg)
    cases["crg_class_threshold"] = threshold
    assert cases.country.is_unique and len(cases) == 4
    assert cases.set_index("selection_role").country.to_dict() == {
        "main": "India",
        "appendix_lower": "Greece",
        "appendix_near_zero": "Indonesia",
        "appendix_higher": "Argentina",
    }
    cases.to_csv(SOURCE_DATA / "country_radar_case_selection.csv", index=False)

    profile_rows: list[dict[str, object]] = []
    for case in cases.itertuples(index=False):
        for model in ("Human survey", *PROFILE_MODELS):
            values = human.loc[case.country] if model == "Human survey" else model_profiles[model].loc[case.country]
            for domain, directed_score in values.items():
                profile_rows.append({
                    "selection_role": case.selection_role,
                    "country": case.country,
                    "display_class": case.display_class,
                    "source": model,
                    "domain": domain,
                    "directed_score": float(directed_score),
                    "human_directed": float(human.loc[case.country, domain]),
                    "model_minus_human": 0.0 if model == "Human survey" else float(
                        directed_score - human.loc[case.country, domain]
                    ),
                    "crg": 0.0 if model == "Human survey" else float(crg.loc[case.country, model]),
                    "delta_crg": float(case.delta_crg),
                    "crg_class_threshold": threshold,
                })
    pd.DataFrame(profile_rows).to_csv(SOURCE_DATA / "country_radar_profiles.csv", index=False)
    return human, model_profiles, crg, cases, threshold


def _draw_country_residual_radar(
    ax: plt.Axes,
    human: pd.DataFrame,
    model_profiles: dict[str, pd.DataFrame],
    country: str,
    *,
    residual_limit: float = .20,
    label_size: float = 7.0,
    profile_labels: list[str] | None = None,
) -> None:
    """Draw one country's signed model-minus-human profile on a fixed scale."""
    angles = np.linspace(0, 2 * np.pi, len(PROFILE_DOMAINS), endpoint=False)
    closed_angles = np.r_[angles, angles[0]]
    residual_origin = residual_limit
    baseline_angles = np.linspace(0, 2 * np.pi, 361)
    ax.plot(
        baseline_angles,
        np.full_like(baseline_angles, residual_origin),
        color=INK,
        lw=1.15,
        zorder=2,
        label="Human survey = 0",
    )
    profile_style = {
        "GPT-5.6 Sol": (TEAL, "-", "D", 2.05, 4.2, TEAL, 3),
        "GPT-5.5": (PRIMARY, (0, (3.0, 2.0)), "o", 1.30, 3.2, WHITE, 4),
    }
    # The wider GPT-5.6 line is drawn first and the hollow GPT-5.5 line last;
    # no coordinate is moved to manufacture visual separation.
    radar_draw_order = ["GPT-5.6 Sol", "GPT-5.5"]
    human_profile = human.loc[country, PROFILE_DOMAINS].to_numpy(float)
    for source in radar_draw_order:
        values = model_profiles[source].loc[country, PROFILE_DOMAINS].to_numpy(float)
        residuals = values - human_profile
        closed_values = np.r_[residuals + residual_origin, residuals[0] + residual_origin]
        color, linestyle, marker, linewidth, markersize, markerface, zorder = profile_style[source]
        ax.plot(
            closed_angles,
            closed_values,
            color=color,
            ls=linestyle,
            lw=linewidth,
            marker=marker,
            ms=markersize,
            markerfacecolor=markerface,
            markeredgecolor=color,
            markeredgewidth=.85 if source == "GPT-5.5" else .35,
            zorder=zorder,
            label=source,
        )
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_thetagrids(
        np.degrees(angles),
        PROFILE_LABELS if profile_labels is None else profile_labels,
        fontsize=label_size,
    )
    ax.tick_params(axis="x", pad=0)
    ax.set_ylim(0, 2 * residual_limit)
    ax.set_yticks([.05, residual_origin, .35])
    ax.set_yticklabels(["−0.15", "0", "+0.15"], fontsize=7.0, color=GRAY)
    ax.set_rlabel_position(330)
    for tick_label in ax.get_yticklabels():
        tick_label.set_bbox({"facecolor": WHITE, "edgecolor": "none", "alpha": .82, "pad": .08})
    ax.grid(color=DIVIDER, lw=.4)
    ax.spines["polar"].set_color(DIVIDER)


def _country_radar_handles() -> list[Line2D]:
    return [
        Line2D([0], [0], color=INK, lw=1.3, label="Human survey = 0"),
        Line2D([0], [0], color=PRIMARY, marker="o", markerfacecolor=WHITE,
               markeredgewidth=.85, ls=(0, (3.0, 2.0)), lw=1.3, markersize=4,
               label="GPT-5.5"),
        Line2D([0], [0], color=TEAL, marker="D", markeredgewidth=.35,
               lw=2.05, markersize=4.5, label="GPT-5.6 Sol"),
    ]


def _world_layers(changes: pd.DataFrame) -> tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        world_path = gpd.datasets.get_path("naturalearth_lowres")
    world = gpd.read_file(world_path)
    points = gpd.GeoDataFrame(
        changes.copy(),
        geometry=gpd.points_from_xy(changes.longitude, changes.latitude),
        crs="EPSG:4326",
    )
    robinson = "+proj=robin +datum=WGS84 +units=m +no_defs"
    return world.to_crs(robinson), points.to_crs(robinson)


def _prior_benchmark_tables() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create a source ledger for published benchmarks and the archived geometry reanalysis."""
    published = pd.DataFrame([
        {
            "study": "WorldValuesBench",
            "model": "Alpaca-7B",
            "metric": "questions with normalized W1 < 0.2",
            "value": 11.1,
            "unit": "percent",
            "source_url": "https://aclanthology.org/2024.lrec-main.1539/",
        },
        {
            "study": "WorldValuesBench",
            "model": "Vicuna-7B-v1.5",
            "metric": "questions with normalized W1 < 0.2",
            "value": 25.0,
            "unit": "percent",
            "source_url": "https://aclanthology.org/2024.lrec-main.1539/",
        },
        {
            "study": "WorldValuesBench",
            "model": "Mixtral-8x7B",
            "metric": "questions with normalized W1 < 0.2",
            "value": 72.2,
            "unit": "percent",
            "source_url": "https://aclanthology.org/2024.lrec-main.1539/",
        },
        {
            "study": "WorldValuesBench",
            "model": "GPT-3.5-Turbo",
            "metric": "questions with normalized W1 < 0.2",
            "value": 75.0,
            "unit": "percent",
            "source_url": "https://aclanthology.org/2024.lrec-main.1539/",
        },
        {
            "study": "Tao et al. (PNAS Nexus)",
            "model": "GPT-4 / GPT-4-Turbo / GPT-4o",
            "metric": "countries or territories with improved alignment under country prompting",
            "value": 71.0,
            "value_upper": 81.0,
            "unit": "percent range",
            "source_url": "https://doi.org/10.1093/pnasnexus/pgae346",
        },
    ])
    metrics = pd.read_parquet(ROOT / "data/analysis_ready/country_model_language_metrics.parquet")
    archived = (
        metrics[metrics.domains.eq(6)]
        .groupby("model", as_index=False)
        .agg(
            countries=("country", "nunique"),
            mean_crg=("crg", "mean"),
            median_crg=("crg", "median"),
            vdr=("vdr", "first"),
            csr=("csr", "first"),
            csr_permutation_p=("csr_perm_p", "first"),
        )
    )
    archived["source_protocol"] = "WorldValuesBench archived outputs; complete six-domain profiles only"
    archived["comparability"] = "descriptive historical context; not pooled with the new API experiment"
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    published.to_csv(SOURCE_DATA / "prior_study_benchmark.csv", index=False)
    archived.to_csv(SOURCE_DATA / "archived_geometry_benchmark.csv", index=False)
    return published, archived


def _draw_prior_benchmarks(
    fig: plt.Figure,
    published: pd.DataFrame,
    archived: pd.DataFrame,
    positions: tuple[list[float], list[float], list[float]],
) -> None:
    """Draw the two published baselines and the protocol-separated archived geometry lens."""
    ax_wvb = fig.add_axes(positions[0])
    wvb = published[published.study.eq("WorldValuesBench")].copy()
    wvb["short"] = wvb.model.replace({
        "Alpaca-7B": "Alpaca",
        "Vicuna-7B-v1.5": "Vicuna",
        "Mixtral-8x7B": "Mixtral",
        "GPT-3.5-Turbo": "GPT-3.5",
    })
    wvb = wvb.sort_values("value")
    y = np.arange(len(wvb))
    ax_wvb.hlines(y, 0, wvb.value, color=DIVIDER, lw=1.5, zorder=1)
    ax_wvb.scatter(wvb.value, y, s=29, color=PRIMARY, edgecolor=WHITE, linewidth=.5, zorder=3)
    for yy, value in zip(y, wvb.value, strict=True):
        ax_wvb.text(value + 2.3, yy, f"{value:.1f}%", ha="left", va="center", fontsize=7.0)
    ax_wvb.set_yticks(y, wvb.short)
    ax_wvb.set_xlim(0, 102)
    ax_wvb.set_xticks([0, 50, 100])
    ax_wvb.set_xlabel("Questions with W1 < 0.2 (%)", labelpad=1)
    ax_wvb.grid(axis="x", color=DIVIDER, lw=.4)
    clean_axes(ax_wvb)
    panel_title(ax_wvb, "A", "WorldValuesBench · 4 models")

    ax_crg = fig.add_axes(positions[1])
    arch = archived.copy()
    arch["short"] = arch.model.replace({
        "Alpaca-7B": "Alpaca",
        "Vicuna-7B-v1.5": "Vicuna",
        "Mixtral-8x7B": "Mixtral",
        "GPT-3.5-Turbo": "GPT-3.5",
    })
    arch = arch.sort_values("mean_crg", ascending=False)
    y = np.arange(len(arch))
    ax_crg.hlines(y, 1.45, arch.mean_crg, color=DIVIDER, lw=1.5, zorder=1)
    ax_crg.scatter(arch.mean_crg, y, s=31, marker="D", color=TEAL,
                   edgecolor=WHITE, linewidth=.5, zorder=3)
    for yy, value in zip(y, arch.mean_crg, strict=True):
        ax_crg.text(value + .035, yy, f"{value:.2f}", ha="left", va="center", fontsize=7.0)
    ax_crg.set_yticks(y, arch.short)
    ax_crg.set_xlim(1.45, 2.65)
    ax_crg.set_xticks([1.5, 2.0, 2.5])
    ax_crg.set_xlabel("Mean CRG (lower = closer)", labelpad=1)
    ax_crg.grid(axis="x", color=DIVIDER, lw=.4)
    clean_axes(ax_crg)
    panel_title(ax_crg, "B", "Archived CRG reanalysis")
    ax_crg.text(.99, .96, "N=50–51 · not pooled", transform=ax_crg.transAxes,
                ha="right", va="top", fontsize=7.0, color=GRAY_DARK)

    ax_pnas = fig.add_axes(positions[2])
    ax_pnas.set_xlim(0, 1)
    ax_pnas.set_ylim(0, 1)
    ax_pnas.text(.00, .52, "PNAS Nexus · 5 GPT versions", ha="left", va="center",
                 fontsize=7.0, color=INK, weight="bold")
    ax_pnas.vlines(.40, .18, .84, color=AMBER, lw=.9)
    ax_pnas.text(.43, .52, "71–81%", ha="left", va="center",
                 fontsize=7.0, color=AMBER, weight="bold")
    ax_pnas.text(.55, .52, "improved with country prompts (later models)",
                 ha="left", va="center", fontsize=7.0, color=GRAY_DARK)
    ax_pnas.set_axis_off()


def _draw_map_and_examples(
    fig: plt.Figure,
    world: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
    column: str,
    panel_label: str,
    title: str,
    map_position: list[float],
    callout_position: list[float],
    examples: tuple[str, str, str],
) -> tuple[float, list[dict[str, object]]]:
    """Draw one map with three non-overlapping, outside-map exemplar callouts."""
    ax = fig.add_axes(map_position)
    call_ax = fig.add_axes(callout_position)
    call_ax.set_axis_off()
    world.plot(ax=ax, color="#F0F3F7", edgecolor="#C8D1DB", linewidth=.24, zorder=0)
    bound = float(points[column].abs().max())
    threshold = .10 * bound
    groups = [
        (points[column] < -threshold, TEAL, "v", "lower"),
        (points[column].abs() <= threshold, GRAY, "o", "near zero"),
        (points[column] > threshold, MAGENTA, "^", "higher"),
    ]
    for mask, color, marker, _ in groups:
        subset = points.loc[mask]
        sizes = 12 + 35 * np.sqrt(subset[column].abs().to_numpy() / bound)
        ax.scatter(subset.geometry.x, subset.geometry.y, s=sizes, marker=marker,
                   c=color, edgecolors=WHITE, linewidths=.38, zorder=3)
    panel_title(ax, panel_label, title, pad=1.0)
    ax.set_axis_off()

    styles = [
        (TEAL, "v", f"Δ < −{threshold:.4f}", "Lower"),
        (GRAY, "o", f"|Δ| ≤ {threshold:.4f}", "Near zero"),
        (MAGENTA, "^", f"Δ > +{threshold:.4f}", "Higher"),
    ]
    x_positions = [.04, .37, .70]
    ledger_rows = []
    for xpos, country, (color, marker, rule, type_label) in zip(x_positions, examples, styles, strict=True):
        row = points.loc[points.country.eq(country)].iloc[0]
        shown = country.replace(" SAR", "")
        call_ax.scatter([xpos], [.72], s=26, marker=marker, color=color,
                        edgecolor=WHITE, linewidth=.4, transform=call_ax.transAxes, zorder=4)
        call_ax.text(xpos + .050, .80, type_label, transform=call_ax.transAxes,
                     ha="left", va="center", fontsize=7.0, color=INK, weight="bold")
        call_ax.text(xpos + .050, .51, rule, transform=call_ax.transAxes,
                     ha="left", va="center", fontsize=7.0, color=GRAY_DARK)
        call_ax.text(xpos + .050, .20, f"{shown}\n{float(row[column]):+.4f}",
                     transform=call_ax.transAxes, ha="left", va="center", fontsize=7.0,
                     color=GRAY_DARK, linespacing=1.05)
        connector = ConnectionPatch(
            xyA=(xpos, .98), coordsA=call_ax.transAxes, axesA=call_ax,
            xyB=(float(row.geometry.x), float(row.geometry.y)), coordsB=ax.transData, axesB=ax,
            arrowstyle="-|>", mutation_scale=7.5, lw=.72, color=color,
            connectionstyle="arc3,rad=0.0", shrinkA=2, shrinkB=2, zorder=5,
        )
        fig.add_artist(connector)
        ledger_rows.append({
            "metric": column,
            "threshold": threshold,
            "type": type_label,
            "rule": rule,
            "example_country": country,
            "example_delta": float(row[column]),
        })
    return threshold, ledger_rows


def _draw_economic_bridge(
    fig: plt.Figure,
    margins: pd.DataFrame,
    interval_position: list[float],
    future_position: list[float],
) -> None:
    """Connect observed representation-loss changes to explicitly prospective economic tests."""
    short = {
        "Opportunity and participation": "Opportunity",
        "Distribution and adjustment": "Adjustment",
        "Coordination and legitimacy": "Coordination",
    }
    ax = fig.add_axes(interval_position)
    y = np.arange(len(margins))[::-1]
    ax.axvspan(-.030, 0, color=TEAL_LIGHT, zorder=0)
    ax.axvline(0, color=INK, lw=.7)
    for i, row in margins.reset_index(drop=True).iterrows():
        color = TEAL if row.delta_estimate < 0 else MAGENTA
        ax.plot([row.delta_ci_low_bca, row.delta_ci_high_bca], [y[i], y[i]],
                color=color, lw=1.65, solid_capstyle="round")
        passed = float(row.holm_p_three_margins) <= .05
        ax.scatter(row.delta_estimate, y[i], s=29, color=color if passed else WHITE,
                   edgecolor=color, linewidth=.9, zorder=3)
    ax.set_yticks(y, [short[x] for x in margins.margin])
    ax.set_xlim(-.030, .007)
    ax.set_xlabel("GPT-5.6 − GPT-5.5 squared-TVD loss", labelpad=1)
    ax.grid(axis="x", color=DIVIDER, lw=.4)
    clean_axes(ax)
    panel_title(ax, "E", "Creative-destruction margins")

    future = fig.add_axes(future_position)
    future.set_axis_off()
    future.add_patch(FancyBboxPatch(
        (.02, .06), .96, .86, boxstyle="round,pad=.018,rounding_size=.025",
        transform=future.transAxes, fc=WARM, ec=AMBER, lw=.8, ls="--",
    ))
    future.text(.50, .82, "Future causal economics tests", transform=future.transAxes,
                ha="center", va="center", fontsize=7.4, weight="bold", color=INK)
    future.text(.50, .49,
                "adoption & entrepreneurship\n"
                "labor adjustment & compensation\n"
                "legitimacy & coordination",
                transform=future.transAxes, ha="center", va="center", fontsize=7.0,
                color=GRAY_DARK, linespacing=1.35)
    future.text(.50, .14, "prospective research program", transform=future.transAxes,
                ha="center", va="center", fontsize=7.0, color=AMBER, weight="bold")
    fig.add_artist(FancyArrowPatch(
        (interval_position[0] + interval_position[2] + .018,
         interval_position[1] + .50 * interval_position[3]),
        (future_position[0] - .010, future_position[1] + .50 * future_position[3]),
        transform=fig.transFigure, arrowstyle="-|>", mutation_scale=8,
        lw=.8, color=AMBER, ls="--",
    ))


def _save_fig1_part(fig: plt.Figure, stem: str, title: str) -> None:
    part_dir = SOURCES / "fig1_spatial_story" / "parts"
    part_dir.mkdir(parents=True, exist_ok=True)
    metadata = {"Creator": f"EthosGPT v{VERSION} Figure 1 child chart"}
    for suffix in (".pdf", ".svg", ".png"):
        kwargs = {"dpi": 300} if suffix == ".png" else {}
        fig.savefig(part_dir / f"{stem}{suffix}", metadata=metadata, **kwargs)
    postprocess_svg(part_dir / f"{stem}.svg", title)


def _panel_background(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    accent: str,
    *,
    facecolor: str = WHITE,
    dashed: bool = False,
) -> None:
    x, y, width, height = bounds
    fig.add_artist(FancyBboxPatch(
        (x, y), width, height,
        boxstyle="round,pad=.006,rounding_size=.012",
        transform=fig.transFigure, fc=facecolor, ec=accent, lw=.75,
        ls="--" if dashed else "-", zorder=-5,
    ))


def _draw_prior_context(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    published: pd.DataFrame,
    archived: pd.DataFrame,
) -> None:
    """Compact, protocol-separated context from two existing studies."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, PRIMARY, facecolor=SURFACE)
    fig.text(x + .06 * width, y + .955 * height, "A  Prior evidence",
             ha="left", va="top", fontsize=8.4, color=INK, weight="bold")
    fig.text(x + .06 * width, y + .875 * height, "benchmark context",
             ha="left", va="top", fontsize=7.0, color=GRAY_DARK)

    ax = fig.add_axes([x + .32 * width, y + .505 * height, .58 * width, .275 * height])
    wvb = published[published.study.eq("WorldValuesBench")].copy().sort_values("value")
    wvb["short"] = wvb.model.replace({
        "Alpaca-7B": "Alpaca", "Vicuna-7B-v1.5": "Vicuna",
        "Mixtral-8x7B": "Mixtral", "GPT-3.5-Turbo": "GPT-3.5",
    })
    yy = np.arange(len(wvb))
    ax.hlines(yy, 0, wvb.value, color=DIVIDER, lw=1.25)
    ax.scatter(wvb.value, yy, s=18, color=PRIMARY, edgecolor=WHITE, lw=.35, zorder=3)
    for ypos, value in zip(yy, wvb.value, strict=True):
        ax.text(value + 2.2, ypos, f"{value:.0f}%", ha="left", va="center", fontsize=7.0)
    ax.set_yticks(yy, wvb.short)
    ax.tick_params(axis="y", labelsize=7.0, pad=1)
    ax.set_xlim(0, 105)
    ax.set_xticks([0, 50, 100])
    ax.tick_params(axis="x", labelsize=7.0, pad=1)
    ax.set_xlabel("W1<0.2 share (%)", fontsize=7.0, labelpad=1)
    ax.grid(axis="x", color=DIVIDER, lw=.35)
    clean_axes(ax)

    cards = [
        ("71–81%", "country prompting", "helped later GPTs", AMBER),
        (f"{archived.mean_crg.min():.2f}–{archived.mean_crg.max():.2f}",
         "archived mean CRG", "N=50–51", TEAL),
    ]
    for i, (number, line_one, line_two, color) in enumerate(cards):
        cy = y + (.285 - .16 * i) * height
        fig.add_artist(FancyBboxPatch(
            (x + .07 * width, cy), .86 * width, .145 * height,
            boxstyle="round,pad=.003,rounding_size=.006",
            transform=fig.transFigure, fc=WHITE, ec=DIVIDER, lw=.55,
        ))
        fig.text(x + .50 * width, cy + .105 * height, number, ha="center", va="center",
                 fontsize=7.0, color=color, weight="bold")
        fig.text(x + .50 * width, cy + .060 * height, line_one, ha="center", va="center",
                 fontsize=7.0, color=GRAY_DARK)
        fig.text(x + .50 * width, cy + .022 * height, line_two, ha="center", va="center",
                 fontsize=7.0, color=GRAY_DARK)
    fig.text(x + .50 * width, y + .035 * height, "separate protocols",
             ha="center", va="bottom", fontsize=7.0, color=GRAY)


def _draw_technical_flow(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    world: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
) -> tuple[float, list[dict[str, object]]]:
    """Original vector survey-to-model-to-audit micro-scene above the main map."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, TEAL)
    fig.text(x + .035 * width, y + .955 * height, "B  Update audit",
             ha="left", va="top", fontsize=8.4, color=INK, weight="bold")
    fig.text(x + .965 * width, y + .955 * height, "paired · 64 countries",
             ha="right", va="top", fontsize=7.0, color=GRAY_DARK)

    flow = fig.add_axes([x + .035 * width, y + .690 * height, .93 * width, .170 * height])
    flow.set_xlim(0, 1)
    flow.set_ylim(0, 1)
    flow.set_axis_off()
    # Survey/globe icon.
    flow.add_patch(Circle((.09, .58), .105, fc=COOL, ec=PRIMARY, lw=.85))
    flow.add_patch(Arc((.09, .58), .13, .20, theta1=80, theta2=280, color=PRIMARY, lw=.55))
    flow.plot([.00, .18], [.58, .58], color=PRIMARY, lw=.5)
    flow.plot([.03, .15], [.53, .53], color=PRIMARY, lw=.45)
    flow.add_patch(Rectangle((.13, .25), .105, .19, fc=WHITE, ec=INK, lw=.6))
    for idx, bar in enumerate((.04, .075, .055)):
        flow.add_patch(Rectangle((.15 + .025 * idx, .28), .014, bar, fc=TEAL, ec="none"))
    flow.text(.09, .06, "survey\nprofiles", ha="center", va="center", fontsize=7.0,
              linespacing=1.12)

    flow.add_patch(FancyArrowPatch((.235, .55), (.325, .55), arrowstyle="-|>",
                                   mutation_scale=7, lw=.75, color=GRAY_DARK))
    # Paired model cards.
    for cy, label, color, marker in ((.68, "GPT-5.5", PRIMARY, "o"), (.40, "GPT-5.6", TEAL, "D")):
        flow.add_patch(FancyBboxPatch((.33, cy - .105), .225, .19,
                                     boxstyle="round,pad=.01,rounding_size=.025",
                                     fc=WHITE, ec=color, lw=.8))
        flow.scatter([.375], [cy - .01], s=18, marker=marker, c=color,
                     ec=WHITE, lw=.3, zorder=4)
        flow.text(.395, cy - .01, label, ha="left", va="center", fontsize=7.0, weight="bold")
    flow.text(.44, .06, "paired prompts", ha="center", va="center", fontsize=7.0)
    flow.add_patch(FancyArrowPatch((.56, .55), (.65, .55), arrowstyle="-|>",
                                   mutation_scale=7, lw=.75, color=GRAY_DARK))
    # Audit ruler/gauge icon.
    flow.add_patch(FancyBboxPatch((.67, .28), .25, .48,
                                 boxstyle="round,pad=.012,rounding_size=.022",
                                 fc=TEAL_LIGHT, ec=TEAL, lw=.8))
    for idx, (label, color) in enumerate((("fidelity", TEAL), ("geometry", AMBER), ("composition", TEAL))):
        cy = .65 - .13 * idx
        flow.scatter([.705], [cy], s=9, c=color, ec=WHITE, lw=.25, zorder=3)
        flow.text(.73, cy, label, ha="left", va="center", fontsize=7.0)
    flow.text(.80, .06, "signed audit", ha="center", va="center", fontsize=7.0)

    threshold, ledger = _draw_map_and_examples(
        fig, world, points, "delta_tvd", "", "Country ΔTVD · mean −0.0080",
        [x + .025 * width, y + .300 * height, .95 * width, .275 * height],
        [x + .015 * width, y + .025 * height, .97 * width, .225 * height],
        ("Ecuador", "Kenya", "Vietnam"),
    )
    fig.text(x + .50 * width, y + .270 * height,
             f"classes: Δ<−τ  |  |Δ|≤τ  |  Δ>τ; τ={threshold:.4f}",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    return threshold, ledger


def _draw_weight_simplex(
    ax: plt.Axes,
    data: pd.DataFrame,
    *,
    compact: bool = False,
    show_labels: bool = True,
) -> tuple[object, float]:
    """Continuous theory-weight surface with point- and interval-boundaries."""
    distribution = data.weight_distribution_adjustment.to_numpy()
    coordination = data.weight_coordination_legitimacy.to_numpy()
    x = distribution + .5 * coordination
    y = np.sqrt(3) / 2 * coordination
    values = data.delta_weighted_loss_56_minus_55.to_numpy()
    upper = data.ci_high_95.to_numpy()
    bound = max(abs(values.min()), abs(values.max()))
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
    cmap = LinearSegmentedColormap.from_list("ethosgpt_diverging", [TEAL, "#F7F8FA", MAGENTA])
    triang = mpl.tri.Triangulation(x, y)
    surface = ax.tricontourf(triang, values, levels=np.linspace(-bound, bound, 15),
                            cmap=cmap, norm=norm, antialiased=True)
    ax.tricontour(triang, upper, levels=[0], colors=[INK], linewidths=.85 if compact else 1.1)
    ax.tricontour(triang, values, levels=[0], colors=[AMBER], linewidths=.75 if compact else .95,
                  linestyles="--")
    triangle = np.array([[0, 0], [1, 0], [.5, np.sqrt(3) / 2], [0, 0]])
    ax.plot(triangle[:, 0], triangle[:, 1], color=INK, lw=.65 if compact else .8)
    ax.scatter(.5, np.sqrt(3) / 6, s=28 if compact else 40, marker="*",
               fc=WHITE, ec=INK, lw=.65, zorder=5)
    if show_labels:
        label_size = 7.0
        ax.text(-.035, -.040, "Opportunity", ha="left", va="top",
                fontsize=label_size, weight="bold")
        ax.text(1.035, -.255 if compact else -.145, "Adjustment", ha="right", va="top",
                fontsize=label_size, weight="bold")
        ax.text(.5, np.sqrt(3) / 2 + .028, "Coordination", ha="center", va="bottom",
                fontsize=label_size, weight="bold")
    ax.set_xlim(-.07, 1.07)
    ax.set_ylim(-.33 if compact and show_labels else -.12, .96)
    ax.set_aspect("equal")
    ax.set_axis_off()
    return surface, bound


def _draw_frontiers(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    surface_data: pd.DataFrame,
    summary: pd.Series,
) -> None:
    x, y, width, height = bounds
    _panel_background(fig, bounds, AMBER, facecolor=WARM, dashed=True)
    fig.text(x + .05 * width, y + .955 * height, "C  Economic implications",
             ha="left", va="top", fontsize=7.5, color=INK, weight="bold")
    fig.text(x + .05 * width, y + .885 * height, "creative destruction",
             ha="left", va="top", fontsize=7.0, color=GRAY_DARK)
    ax = fig.add_axes([x + .09 * width, y + .545 * height, .82 * width, .275 * height])
    _draw_weight_simplex(ax, surface_data, compact=True)
    fig.text(x + .50 * width, y + .505 * height,
             f"CI favors 5.6 for {100 * float(summary.fraction_ci_favors_gpt56):.2f}%",
             ha="center", va="top", fontsize=7.0, color=TEAL, weight="bold")
    fig.text(x + .50 * width, y + .452 * height, "CI line · equal-loss dash",
             ha="center", va="top", fontsize=7.0, color=GRAY_DARK)

    cards = [
        (.265, "Research frontier", "agent norms", "causal economics", INK),
        (.060, "Deployment studies", "update validation", "localization", TEAL),
    ]
    for cy, heading, line_one, line_two, color in cards:
        fig.add_artist(FancyBboxPatch(
            (x + .07 * width, y + cy * height), .86 * width, .155 * height,
            boxstyle="round,pad=.003,rounding_size=.006",
            transform=fig.transFigure, fc=WHITE, ec=color, lw=.65,
        ))
        fig.text(x + .50 * width, y + (cy + .110) * height, heading,
                 ha="center", va="center", fontsize=7.0, color=color, weight="bold")
        fig.text(x + .50 * width, y + (cy + .065) * height, line_one,
                 ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
        fig.text(x + .50 * width, y + (cy + .025) * height, line_two,
                 ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.add_artist(FancyArrowPatch(
        (x + .50 * width, y + .410 * height), (x + .50 * width, y + .397 * height),
        transform=fig.transFigure, arrowstyle="-|>", mutation_scale=6.5,
        lw=.65, color=AMBER, ls="--",
    ))


def _draw_prior_strip(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    published: pd.DataFrame,
    archived: pd.DataFrame,
) -> None:
    """Published and archived context sized for a short, wide evidence module."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, PRIMARY, facecolor=SURFACE)
    fig.text(x + .045 * width, y + .925 * height, "A  Prior evidence",
             ha="left", va="top", fontsize=8.2, color=INK, weight="bold")
    fig.text(x + .500 * width, y + .745 * height, "WorldValuesBench · W1 < 0.2",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)

    ax = fig.add_axes([x + .285 * width, y + .300 * height, .640 * width, .365 * height])
    wvb = published[published.study.eq("WorldValuesBench")].copy().sort_values("value")
    wvb["short"] = wvb.model.replace({
        "Alpaca-7B": "Alpaca", "Vicuna-7B-v1.5": "Vicuna",
        "Mixtral-8x7B": "Mixtral", "GPT-3.5-Turbo": "GPT-3.5",
    })
    yy = np.arange(len(wvb))
    ax.hlines(yy, 0, wvb.value, color=DIVIDER, lw=1.15)
    ax.scatter(wvb.value, yy, s=17, color=PRIMARY, edgecolor=WHITE, lw=.35, zorder=3)
    for ypos, value in zip(yy, wvb.value, strict=True):
        ax.text(value + 8.0, ypos, f"{value:.0f}%", ha="left", va="center", fontsize=7.0)
    ax.set_yticks(yy, wvb.short)
    ax.tick_params(axis="y", labelsize=7.0, pad=1)
    ax.set_xlim(0, 110)
    ax.set_xticks([])
    clean_axes(ax, bottom=False)

    fig.add_artist(Line2D([x + .50 * width, x + .50 * width],
                          [y + .045 * height, y + .220 * height],
                          transform=fig.transFigure, color=DIVIDER, lw=.6))
    fig.text(x + .255 * width, y + .170 * height, "71–81%", ha="center", va="center",
             fontsize=7.1, color=AMBER, weight="bold")
    fig.text(x + .255 * width, y + .060 * height, "prompt gain",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.text(x + .745 * width, y + .170 * height,
             f"CRG {archived.mean_crg.min():.2f}–{archived.mean_crg.max():.2f}",
             ha="center", va="center", fontsize=7.1, color=TEAL, weight="bold")
    fig.text(x + .745 * width, y + .060 * height, "N=50–51",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)


def _draw_audit_strip(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
) -> None:
    """Paired survey-to-model-to-metric mechanism with protected label lanes."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, TEAL)
    fig.text(x + .030 * width, y + .925 * height, "B  Paired comparison",
             ha="left", va="top", fontsize=8.2, color=INK, weight="bold")
    fig.text(x + .970 * width, y + .815 * height, "3,840 outputs · 64 countries · K=5",
             ha="right", va="top", fontsize=7.0, color=GRAY_DARK)

    flow = fig.add_axes([x + .030 * width, y + .060 * height, .94 * width, .735 * height])
    flow.set_xlim(0, 1)
    flow.set_ylim(0, 1)
    flow.set_axis_off()

    # Survey profile micro-scene.
    flow.add_patch(Circle((.090, .61), .083, fc=COOL, ec=PRIMARY, lw=.8))
    flow.add_patch(Arc((.090, .61), .105, .16, theta1=80, theta2=280,
                       color=PRIMARY, lw=.5))
    flow.plot([.020, .160], [.61, .61], color=PRIMARY, lw=.48)
    flow.add_patch(Rectangle((.125, .39), .090, .16, fc=WHITE, ec=INK, lw=.55))
    for idx, bar in enumerate((.035, .065, .048)):
        flow.add_patch(Rectangle((.142 + .021 * idx, .42), .011, bar,
                                 fc=TEAL, ec="none"))
    flow.text(.100, .10, "survey", ha="center", va="center", fontsize=7.0)

    flow.add_patch(FancyArrowPatch((.215, .57), (.285, .57), arrowstyle="-|>",
                                   mutation_scale=7, lw=.75, color=GRAY_DARK))
    for cy, label, color, marker in ((.69, "GPT-5.5", PRIMARY, "o"),
                                     (.43, "GPT-5.6", TEAL, "D")):
        flow.add_patch(FancyBboxPatch((.300, cy - .090), .245, .17,
                                     boxstyle="round,pad=.008,rounding_size=.022",
                                     fc=WHITE, ec=color, lw=.75))
        flow.scatter([.340], [cy - .005], s=16, marker=marker, c=color,
                     ec=WHITE, lw=.3, zorder=4)
        flow.text(.370, cy - .005, label, ha="left", va="center",
                  fontsize=7.0, weight="bold")
    flow.text(.423, .10, "model pair", ha="center", va="center",
              fontsize=7.0)

    flow.add_patch(FancyArrowPatch((.560, .57), (.635, .57), arrowstyle="-|>",
                                   mutation_scale=7, lw=.75, color=GRAY_DARK))
    flow.add_patch(FancyBboxPatch((.655, .29), .315, .51,
                                 boxstyle="round,pad=.010,rounding_size=.020",
                                 fc=TEAL_LIGHT, ec=TEAL, lw=.75))
    for idx, (label, color) in enumerate((("fidelity", TEAL),
                                          ("geometry", AMBER),
                                          ("persistence", TEAL))):
        cy = .69 - .145 * idx
        flow.scatter([.700], [cy], s=8.5, c=color, ec=WHITE, lw=.25, zorder=3)
        flow.text(.735, cy, label, ha="left", va="center", fontsize=7.0)
    flow.text(.813, .10, "measure views", ha="center", va="center", fontsize=7.0)


def _draw_frontier_strip(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    surface_data: pd.DataFrame,
    summary: pd.Series,
) -> None:
    """Compact creative-destruction sensitivity with separate future directions."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, AMBER, facecolor=WARM, dashed=True)
    fig.text(x + .045 * width, y + .925 * height, "C  Economic implications",
             ha="left", va="top", fontsize=8.0, color=INK, weight="bold")

    ax = fig.add_axes([x + .035 * width, y + .310 * height, .440 * width, .470 * height])
    _draw_weight_simplex(ax, surface_data, compact=True, show_labels=False)
    fig.text(x + .710 * width, y + .655 * height,
             f"{100 * float(summary.fraction_ci_favors_gpt56):.2f}%",
             ha="center", va="center", fontsize=7.7, color=TEAL, weight="bold")
    fig.text(x + .710 * width, y + .515 * height, "weight CIs favor",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.text(x + .710 * width, y + .405 * height, "GPT-5.6",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.add_artist(Line2D([x + .080 * width, x + .920 * width],
                          [y + .285 * height, y + .285 * height],
                          transform=fig.transFigure, color=DIVIDER, lw=.55))
    fig.text(x + .500 * width, y + .185 * height, "Research · norms / tests",
             ha="center", va="center", fontsize=7.0, color=INK, weight="bold")
    fig.text(x + .500 * width, y + .070 * height, "Deploy · validate / localize",
             ha="center", va="center", fontsize=7.0, color=TEAL, weight="bold")


def _draw_country_update_panel(
    fig: plt.Figure,
    bounds: tuple[float, float, float, float],
    world: gpd.GeoDataFrame,
    points: gpd.GeoDataFrame,
) -> tuple[float, list[dict[str, object]]]:
    """Full-width map with all definitions and examples outside its viewport."""
    x, y, width, height = bounds
    _panel_background(fig, bounds, TEAL, facecolor=WHITE)
    values = points["delta_tvd"]
    bound = float(values.abs().max())
    threshold = .10 * bound
    fig.text(x + .025 * width, y + .945 * height, "D  Country-level TVD change",
             ha="left", va="top", fontsize=8.2, color=INK, weight="bold")
    fig.text(x + .975 * width, y + .945 * height,
             f"mean Δ = −0.0080 · descriptive · τ = {threshold:.4f}",
             ha="right", va="top", fontsize=7.0, color=GRAY_DARK)

    ax = fig.add_axes([x + .025 * width, y + .080 * height, .630 * width, .780 * height])
    world.plot(ax=ax, color="#F0F3F7", edgecolor="#C8D1DB", linewidth=.24, zorder=0)
    groups = [
        (values < -threshold, TEAL, "v"),
        (values.abs() <= threshold, GRAY, "o"),
        (values > threshold, MAGENTA, "^"),
    ]
    for mask, color, marker in groups:
        subset = points.loc[mask]
        sizes = 14 + 38 * np.sqrt(subset["delta_tvd"].abs().to_numpy() / bound)
        ax.scatter(subset.geometry.x, subset.geometry.y, s=sizes, marker=marker,
                   c=color, edgecolors=WHITE, linewidths=.36, zorder=3)
    ax.set_axis_off()

    fig.add_artist(Line2D([x + .675 * width, x + .675 * width],
                          [y + .080 * height, y + .845 * height],
                          transform=fig.transFigure, color=DIVIDER, lw=.65))
    call_ax = fig.add_axes([x + .700 * width, y + .070 * height, .270 * width, .785 * height])
    call_ax.set_axis_off()
    styles = [
        ("Ecuador", TEAL, "v", "Lower", "Δ < −τ"),
        ("Kenya", GRAY, "o", "Near zero", "|Δ| ≤ τ"),
        ("Vietnam", MAGENTA, "^", "Higher", "Δ > τ"),
    ]
    y_positions = [.78, .50, .22]
    ledger_rows: list[dict[str, object]] = []
    masks = [values < -threshold, values.abs() <= threshold, values > threshold]
    for ypos, mask, (country, color, marker, label, rule) in zip(
            y_positions, masks, styles, strict=True):
        row = points.loc[points.country.eq(country)].iloc[0]
        call_ax.add_patch(FancyBboxPatch(
            (.01, ypos - .130), .98, .260,
            boxstyle="round,pad=.006,rounding_size=.018",
            transform=call_ax.transAxes, fc=SURFACE, ec=DIVIDER, lw=.55,
        ))
        call_ax.scatter([.075], [ypos + .030], s=25, marker=marker, color=color,
                        edgecolor=WHITE, linewidth=.4, transform=call_ax.transAxes, zorder=5)
        call_ax.text(.155, ypos + .075, f"{label}  (n={int(mask.sum())})",
                     transform=call_ax.transAxes,
                     ha="left", va="center", fontsize=7.0, color=INK, weight="bold")
        call_ax.text(.155, ypos, rule, transform=call_ax.transAxes,
                     ha="left", va="center", fontsize=7.0, color=GRAY_DARK)
        call_ax.text(.155, ypos - .075, f"{country}  {float(row['delta_tvd']):+.4f}",
                     transform=call_ax.transAxes, ha="left", va="center",
                     fontsize=7.0, color=GRAY_DARK)
        fig.add_artist(ConnectionPatch(
            xyA=(.005, ypos), coordsA=call_ax.transAxes, axesA=call_ax,
            xyB=(float(row.geometry.x), float(row.geometry.y)), coordsB=ax.transData, axesB=ax,
            arrowstyle="-|>", mutation_scale=7.0, lw=.70, color=color,
            connectionstyle="arc3,rad=0.0", shrinkA=2, shrinkB=2, zorder=4,
        ))
        ledger_rows.append({
            "metric": "delta_tvd",
            "threshold": threshold,
            "type": label,
            "rule": rule,
            "example_country": country,
            "example_delta": float(row["delta_tvd"]),
        })
    return threshold, ledger_rows


def _write_fig1_drawio() -> None:
    """Write an editable Draw.io master with four regenerated SVG modules."""
    part_dir = SOURCES / "fig1_spatial_story" / "parts"
    encoded = {}
    for stem in ("prior_context", "current_audit", "economic_frontiers",
                 "country_heterogeneity"):
        svg = (part_dir / f"{stem}.svg").read_text(encoding="utf-8")
        encoded[stem] = "data:image/svg+xml," + quote(svg, safe="")
    drawio = f'''<mxfile host="app.diagrams.net" modified="2026-09-05T00:00:00.000Z" agent="EthosGPT-v1.0" version="24.7.17">
  <diagram id="ethosgpt-figure1" name="Prior evidence, paired comparison, and implications">
    <mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" page="1" pageWidth="1200" pageHeight="760"><root><mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="title" value="Country-conditioned survey representation: evidence → comparison → implications" style="text;html=1;fontFamily=Times New Roman;fontSize=23;fontStyle=1;fontColor=#18324A;align=left;" vertex="1" parent="1"><mxGeometry x="30" y="18" width="1120" height="38" as="geometry"/></mxCell>
      <mxCell id="prior" value="" style="shape=image;imageAspect=0;aspect=fixed;image={encoded['prior_context']};" vertex="1" parent="1"><mxGeometry x="25" y="70" width="290" height="205" as="geometry"/></mxCell>
      <mxCell id="audit" value="" style="shape=image;imageAspect=0;aspect=fixed;image={encoded['current_audit']};" vertex="1" parent="1"><mxGeometry x="340" y="70" width="530" height="205" as="geometry"/></mxCell>
      <mxCell id="frontier" value="" style="shape=image;imageAspect=0;aspect=fixed;image={encoded['economic_frontiers']};" vertex="1" parent="1"><mxGeometry x="895" y="70" width="280" height="205" as="geometry"/></mxCell>
      <mxCell id="country" value="" style="shape=image;imageAspect=0;aspect=fixed;image={encoded['country_heterogeneity']};" vertex="1" parent="1"><mxGeometry x="25" y="310" width="1150" height="390" as="geometry"/></mxCell>
      <mxCell id="flow1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#3B5CCC;strokeWidth=2;" edge="1" parent="1" source="prior" target="audit"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="flow2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#D88A24;strokeWidth=2;dashed=1;" edge="1" parent="1" source="audit" target="frontier"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="flow3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#078C82;strokeWidth=2;" edge="1" parent="1" source="audit" target="country"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="note" value="Solid = published/current evidence · dashed = theory-guided future pathway · child SVG modules regenerate from released data" style="text;html=1;fontFamily=Times New Roman;fontSize=12;fontColor=#4E5B68;align=center;" vertex="1" parent="1"><mxGeometry x="130" y="710" width="940" height="25" as="geometry"/></mxCell>
    </root></mxGraphModel>
  </diagram>
</mxfile>'''
    target = FIGURES / "fig1_spatial_story.drawio"
    target.write_text(drawio + "\n", encoding="utf-8")
    shutil.copy2(target, RESULT_FIGURES / target.name)


def figure1_spatial_story() -> None:
    """Nested evidence, audit, frontier, and country-result hero figure."""
    published, archived = _prior_benchmark_tables()
    changes = _country_changes()
    world, points = _world_layers(changes)
    surface = pd.read_csv(RESULTS / "economic_weight_surface.csv")
    summary = pd.read_csv(RESULTS / "economic_weight_surface_summary.csv").iloc[0]

    fig = plt.figure(figsize=(5.48, 3.45))
    fig.text(.01, .992, "Country-conditioned survey representation: evidence → comparison → implications",
             ha="left", va="top", fontsize=9.0, color=INK, weight="bold")
    prior_bounds = (.01, .615, .250, .305)
    audit_bounds = (.285, .615, .455, .305)
    frontier_bounds = (.765, .615, .225, .305)
    country_bounds = (.01, .045, .980, .520)
    _draw_prior_strip(fig, prior_bounds, published, archived)
    _draw_audit_strip(fig, audit_bounds)
    _draw_frontier_strip(fig, frontier_bounds, surface, summary)
    _, rows_tvd = _draw_country_update_panel(fig, country_bounds, world, points)
    for start, end, color, dashed in (
        ((.262, .767), (.282, .767), PRIMARY, False),
        ((.742, .767), (.762, .767), AMBER, True),
        ((.512, .610), (.512, .570), TEAL, False),
    ):
        fig.add_artist(FancyArrowPatch(start, end, transform=fig.transFigure,
                                      arrowstyle="-|>", mutation_scale=7.5, lw=.8,
                                      color=color, ls="--" if dashed else "-"))
    save(fig, "fig1_spatial_story", "Country-conditioned survey representation across benchmarks, the paired update comparison, and future economic and agent research")
    plt.close(fig)

    # Editable Draw.io master: each nested module remains a regenerated SVG child.
    child_specs = [
        ("prior_context", (1.55, 1.08),
         lambda f: _draw_prior_strip(f, (.02, .02, .96, .96), published, archived),
         "Published benchmark context"),
        ("current_audit", (2.75, 1.08),
         lambda f: _draw_audit_strip(f, (.02, .02, .96, .96)),
         "Survey-to-model technical audit"),
        ("economic_frontiers", (1.40, 1.08),
         lambda f: _draw_frontier_strip(f, (.02, .02, .96, .96), surface, summary),
         "Creative-destruction sensitivity and research implications"),
        ("country_heterogeneity", (5.50, 1.92),
         lambda f: _draw_country_update_panel(f, (.02, .02, .96, .96), world, points),
         "Country-level TVD heterogeneity and external examples"),
    ]
    for stem, size, draw, title in child_specs:
        child = plt.figure(figsize=size)
        draw(child)
        _save_fig1_part(child, stem, title)
        plt.close(child)
    _write_fig1_drawio()

    # Full two-metric map remains available for appendix inspection.
    maps_fig = plt.figure(figsize=(5.48, 2.12))
    t_tvd, appendix_tvd = _draw_map_and_examples(
        maps_fig, world, points, "delta_tvd", "a", "TVD change · mean −0.0080",
        [.015, .46, .470, .41], [.018, .080, .465, .30],
        ("Ecuador", "Kenya", "Vietnam"),
    )
    t_crg, appendix_crg = _draw_map_and_examples(
        maps_fig, world, points, "delta_crg", "b", "CRG change · mean −0.0022",
        [.515, .46, .470, .41], [.518, .080, .465, .30],
        ("Colombia", "Vietnam", "Kenya"),
    )
    maps_fig.text(.50, .025,
                  f"Classes use τ=10% max|Δ| within metric: TVD {t_tvd:.4f}; CRG {t_crg:.4f}.",
                  ha="center", va="bottom", fontsize=7.0, color=GRAY_DARK)
    save(maps_fig, "figS4_country_maps", "Country-level TVD and CRG update maps with external examples")
    plt.close(maps_fig)
    pd.DataFrame(rows_tvd + appendix_crg).to_csv(
        SOURCE_DATA / "figure1_error_type_examples.csv", index=False,
    )


def _raincloud(ax: plt.Axes, values: np.ndarray) -> None:
    grid = np.linspace(values.min() - .003, values.max() + .003, 240)
    density = gaussian_kde(values)(grid)
    density = .50 * density / density.max()
    baseline = .57
    ax.fill_between(grid, baseline, baseline + density, color=DIST_LIGHT, alpha=1.0, lw=0)
    ax.plot(grid, baseline + density, color=DIST, lw=1.0)
    rng = np.random.default_rng(20260905)
    jitter = rng.uniform(.10, .39, size=len(values))
    threshold = .10 * np.abs(values).max()
    colors = np.where(values < -threshold, TEAL,
                      np.where(values > threshold, MAGENTA, GRAY))
    markers = np.where(values < -threshold, "v",
                       np.where(values > threshold, "^", "o"))
    for marker in ("v", "o", "^"):
        mask = markers == marker
        ax.scatter(values[mask], jitter[mask], s=18, marker=marker, c=colors[mask],
                   ec=WHITE, lw=.35, alpha=.84, zorder=3)
    q1, median, q3 = np.quantile(values, [.25, .50, .75])
    ax.plot([values.min(), values.max()], [.50, .50], color=GRAY, lw=.75, zorder=3)
    ax.vlines([values.min(), values.max()], .455, .545, color=GRAY, lw=.65, zorder=3)
    ax.add_patch(Rectangle((q1, .425), q3 - q1, .150,
                           fc=COOL, ec=DIST, lw=.75, zorder=4))
    ax.vlines(median, .425, .575, color=INK, lw=1.05, zorder=5)
    ax.axvline(0, color=GRAY_LIGHT, lw=.70, zorder=0)
    ax.set_ylim(0, 1.13)
    ax.set_yticks([])
    ax.grid(axis="x", color=DIVIDER, lw=.45, zorder=0)
    clean_axes(ax)


def figure2_multiview() -> None:
    """Four coordinated idioms for heterogeneity, composition, inference, and shape."""
    joint = pd.read_csv(RESULTS / "joint_item_inference.csv")
    joint["label"] = joint.question_id.map({
        "Q48": "Agency (Q48)", "Q57": "Trust (Q57)", "Q106": "Distribution (Q106)",
        "Q108": "Responsibility (Q108)", "Q121": "Immigration* (Q121)",
        "Q159": "Science (Q159)",
    })
    composition = pd.read_csv(RESULTS / "composition_estimates.csv")
    composition = composition[composition.metric == "squared_probability_error"].copy()
    changes = _country_changes()
    human_profiles, country_models, country_crg, profile_cases, _ = _country_profile_cases()
    main_case = profile_cases.set_index("selection_role").loc["main"]
    main_country = str(main_case.country)

    fig = plt.figure(figsize=(5.48, 3.36))
    ax_a = fig.add_axes([.075, .705, .465, .155])
    ax_b = fig.add_axes([.650, .675, .325, .205])
    ax_c = fig.add_axes([.175, .125, .470, .275])
    ax_d = fig.add_axes([.710, .115, .250, .300], projection="polar")

    # A: country-level raincloud for the headline contrast.
    country_values = changes.delta_tvd.to_numpy(float)
    _raincloud(ax_a, country_values)
    ax_a.set_xlim(-.035, .031)
    ax_a.set_xticks([-.03, 0, .03])
    ax_a.set_xlabel("Country ΔTVD (GPT-5.6 − GPT-5.5)")
    panel_title(ax_a, "a", "Country ΔTVD distribution")
    examples = [
        (.150, "Ecuador", "lower", "−0.0233", TEAL, "v"),
        (.305, "Kenya", "near zero", "−0.0007", GRAY, "o"),
        (.460, "Vietnam", "higher", "+0.0066", MAGENTA, "^"),
    ]
    for center, country, group, value, color, marker in examples:
        fig.add_artist(Line2D([center - .045], [.580], transform=fig.transFigure, marker=marker,
                              markersize=5.5, markerfacecolor=color, markeredgecolor=WHITE,
                              color="none"))
        fig.text(center + .012, .580, group, ha="center", va="center",
                 fontsize=7.0, color=color, weight="bold")
        fig.text(center, .548, country, ha="center", va="center",
                 fontsize=7.0, color=GRAY_DARK)
        fig.text(center, .518, value, ha="center", va="center",
                 fontsize=7.0, color=GRAY_DARK)
    fig.text(.305, .482, "Types use τ = 0.1 max|Δ| = 0.0030",
             ha="center", va="center", fontsize=7.0, color=GRAY)

    # B: slope graph of finite-pool error remaining as K increases.
    model_style = {
        "GPT-5.5": (PRIMARY, "o", "5.5"),
        "GPT-5.6 Sol": (TEAL, "D", "5.6"),
    }
    for model, (color, marker, short) in model_style.items():
        frame = composition[composition.model == model].sort_values("ensemble_size")
        first = float(frame.iloc[0].estimate)
        pct = 100 * frame.estimate.to_numpy(float) / first
        x = frame.ensemble_size.to_numpy(int)
        ax_b.plot(x, pct, color=color, marker=marker, ms=3.8, lw=1.45, label=short)
        label_y = pct[-1] + (.15 if short == "5.5" else -.15)
        ax_b.plot([5.04, 5.55], [pct[-1], label_y], color=color, lw=.55,
                  solid_capstyle="round", zorder=2)
        ax_b.text(6.08, label_y, f"{short}: {pct[-1]:.2f}%", color=color,
                  va="center", ha="right", fontsize=7.0, weight="bold")
    ax_b.set_xlim(.8, 6.15)
    ax_b.set_ylim(98.38, 100.25)
    ax_b.set_xticks([1, 3, 5])
    ax_b.set_xlabel("Repeated outputs averaged (K)")
    ax_b.grid(color=DIVIDER, lw=.45)
    clean_axes(ax_b, left=True)
    ax_b.set_ylabel("Error remaining (%)", labelpad=3)
    panel_title(ax_b, "b", "Pre-interaction residual")

    # C: simultaneous interval forest for the 12-outcome family.
    order = ["Q48", "Q57", "Q106", "Q108", "Q121", "Q159"]
    base = np.arange(len(order))[::-1]
    ax_c.axvspan(-.044, 0, color=TEAL_LIGHT, zorder=0)
    ax_c.axvline(0, color=INK, lw=.75, zorder=1)
    for offset, metric, marker in ((.13, "W1", "o"), (-.13, "TVD", "s")):
        frame = joint[joint.metric == metric].set_index("question_id").loc[order]
        for idx, (question, row) in enumerate(frame.iterrows()):
            yy = base[idx] + offset
            value = float(row.delta_56_minus_55)
            color = TEAL if value < 0 else MAGENTA
            ax_c.plot([row.simultaneous_ci_low_95, row.simultaneous_ci_high_95], [yy, yy],
                      color=color, lw=1.5, solid_capstyle="round", zorder=3)
            passed = float(row.joint_max_t_p_fwer) <= .05
            ax_c.scatter(value, yy, s=29, marker=marker, fc=color if passed else WHITE,
                         ec=color, lw=.95, zorder=4)
    labels = [
        "Agency (Q48)", "Trust (Q57)", "Distrib. (Q106)",
        "Responsib. (Q108)", "Immigr.* (Q121)", "Science (Q159)",
    ]
    ax_c.set_yticks(base, labels)
    ax_c.tick_params(axis="y", labelsize=7.0)
    ax_c.set_xlim(-.044, .024)
    ax_c.set_xlabel("Δ error (GPT-5.6 − GPT-5.5)  ← lower", fontsize=7.0, labelpad=1)
    ax_c.grid(axis="x", color=DIVIDER, lw=.45, zorder=0)
    clean_axes(ax_c)
    panel_title(ax_c, "c", "Joint simultaneous intervals")
    ax_c.legend(handles=[
        Line2D([0], [0], marker="o", color=GRAY_DARK, markerfacecolor=WHITE,
               markersize=5, lw=0, label="W1"),
        Line2D([0], [0], marker="s", color=GRAY_DARK, markerfacecolor=WHITE,
               markersize=5, lw=0, label="TVD"),
    ], loc="upper left", ncol=2, frameon=True, facecolor=WHITE, edgecolor=DIVIDER,
        framealpha=.90, borderpad=.15, handletextpad=.2, columnspacing=.5, fontsize=7.0)

    # D: one outcome-independent country case avoids cancellation across the
    # 64 comparison units. India is selected solely from the human survey as
    # the standardized six-coordinate medoid, never from model performance.
    _draw_country_residual_radar(ax_d, human_profiles, country_models, main_country)
    ax_d.set_title(f"d  {main_country} profile", loc="left", pad=8,
                   color=INK, weight="bold", fontsize=8.5)
    crg55 = float(country_crg.loc[main_country, "GPT-5.5"])
    crg56 = float(country_crg.loc[main_country, "GPT-5.6 Sol"])
    ax_d.text(.5, -.205, f"human-profile medoid\nCRG {crg55:.3f} → {crg56:.3f}",
              transform=ax_d.transAxes, ha="center", va="top", fontsize=7.0,
              color=GRAY_DARK, linespacing=1.12)

    fig.legend(handles=_country_radar_handles(), ncol=3, frameon=False, loc="upper center",
               bbox_to_anchor=(.73, .995), columnspacing=.65, handletextpad=.25,
               fontsize=7.0)
    save(fig, "fig2_multiview_results", "Four complementary views of EthosGPT model-update results")
    plt.close(fig)


def figure7_country_profiles() -> None:
    """Appendix profile cases spanning lower, near-zero, and higher CRG change."""
    human, model_profiles, crg, cases, threshold = _country_profile_cases()
    selected = cases.set_index("selection_role")
    roles = ["appendix_lower", "appendix_near_zero", "appendix_higher"]
    labels = ["Lower CRG", "Near-zero CRG", "Higher CRG"]
    panel_letters = ["a", "b", "c"]

    fig = plt.figure(figsize=(5.48, 2.62))
    positions = [[.045, .205, .270, .630], [.365, .205, .270, .630], [.685, .205, .270, .630]]
    for position, role, class_label, panel_letter in zip(
        positions, roles, labels, panel_letters, strict=True
    ):
        row = selected.loc[role]
        country = str(row.country)
        ax = fig.add_axes(position, projection="polar")
        _draw_country_residual_radar(
            ax,
            human,
            model_profiles,
            country,
            label_size=7.0,
            profile_labels=["Agency", "Tr.", "Distrib.", "Responsib.", "Immigr.", "Sci."],
        )
        center = position[0] + position[2] / 2
        fig.text(center, .970, f"{panel_letter}  {class_label}: {country}",
                 ha="center", va="top", fontsize=8.3, color=INK, weight="bold")
        fig.text(
            center,
            .910,
            f"CRG {crg.loc[country, 'GPT-5.5']:.3f} → "
            f"{crg.loc[country, 'GPT-5.6 Sol']:.3f}  "
            f"(Δ {crg.loc[country, 'delta_crg']:+.3f})",
            ha="center",
            va="top",
            fontsize=7.0,
            color=GRAY_DARK,
        )
    fig.text(.5, .115,
             f"Shared residual scale −0.20 to +0.20; CRG class threshold τ = {threshold:.4f}",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.legend(handles=_country_radar_handles(), ncol=3, frameon=False, loc="lower center",
               bbox_to_anchor=(.5, .010), columnspacing=.85, handletextpad=.3,
               fontsize=7.0)
    save(fig, "figS5_country_profiles", "Threshold-class medoid country profiles for CRG change")
    plt.close(fig)


def figure3_economic_story() -> None:
    margins = pd.read_csv(RESULTS / "economic_margin_results.csv")
    surface = pd.read_csv(RESULTS / "economic_weight_surface.csv")
    summary = pd.read_csv(RESULTS / "economic_weight_surface_summary.csv").iloc[0]
    short = {
        "Opportunity and participation": "Opportunity",
        "Distribution and adjustment": "Adjustment",
        "Coordination and legitimacy": "Coordination",
    }
    fig = plt.figure(figsize=(5.48, 2.68))
    ax_a = fig.add_axes([.145, .275, .265, .575])
    ax_b = fig.add_axes([.500, .275, .190, .575])
    ax_c = fig.add_axes([.715, .315, .275, .545])

    # A: horizontal dumbbells compare model-specific losses without label collisions.
    y_a = np.arange(len(margins))[::-1]
    for ypos, (_, row) in zip(y_a, margins.iterrows(), strict=True):
        color = TEAL if row.delta_estimate < 0 else MAGENTA
        ax_a.plot([row.gpt55_estimate, row.gpt56_estimate], [ypos, ypos],
                  color=color, lw=1.65, solid_capstyle="round")
        ax_a.scatter(row.gpt55_estimate, ypos, s=27, fc=PRIMARY, ec=WHITE,
                     lw=.5, zorder=3)
        ax_a.scatter(row.gpt56_estimate, ypos, s=28, marker="D", fc=TEAL,
                     ec=WHITE, lw=.5, zorder=3)
    ax_a.set_yticks(y_a, [short[x] for x in margins.margin])
    ax_a.set_xlim(.02, .195)
    ax_a.set_xticks([.05, .10, .15])
    ax_a.set_xlabel("Squared-TVD loss  ← lower")
    ax_a.grid(axis="x", color=DIVIDER, lw=.45)
    clean_axes(ax_a)
    panel_title(ax_a, "a", "Model losses")
    ax_a.legend(handles=[
        Line2D([0], [0], marker="o", color="none", markerfacecolor=PRIMARY,
               markeredgecolor=WHITE, markersize=5.5, label="GPT-5.5"),
        Line2D([0], [0], marker="D", color="none", markerfacecolor=TEAL,
               markeredgecolor=WHITE, markersize=5.5, label="GPT-5.6"),
    ], loc="upper left", ncol=1, frameon=False,
        borderaxespad=.15, handletextpad=.25, labelspacing=.20)

    # B: interval lollipops for the paired contrast.
    y = np.arange(len(margins))[::-1]
    ax_b.axvspan(-.030, 0, color=TEAL_LIGHT, zorder=0)
    ax_b.axvline(0, color=INK, lw=.75)
    for i, row in margins.reset_index(drop=True).iterrows():
        value = float(row.delta_estimate)
        color = TEAL if value < 0 else MAGENTA
        ax_b.plot([0, value], [y[i], y[i]], color=color, alpha=.45, lw=1.1)
        ax_b.plot([row.delta_ci_low_bca, row.delta_ci_high_bca], [y[i], y[i]],
                  color=color, lw=1.7, solid_capstyle="round")
        passed = float(row.holm_p_three_margins) <= .05
        ax_b.scatter(value, y[i], s=33, fc=color if passed else WHITE, ec=color, lw=1.0, zorder=3)
    ax_b.set_yticks(y, [short[x] for x in margins.margin])
    ax_b.set_xlim(-.030, .007)
    ax_b.set_xlabel("Δ loss  ← lower")
    ax_b.grid(axis="x", color=DIVIDER, lw=.45)
    clean_axes(ax_b)
    panel_title(ax_b, "b", "Paired 95% CIs")

    # C: Figure-6-quality continuous surface with both decision boundaries.
    surface_artist, bound = _draw_weight_simplex(ax_c, surface, compact=False)
    ax_c.set_title("c  Weight surface", loc="left", pad=5,
                   color=INK, weight="bold", fontsize=8.5)
    cax = fig.add_axes([.755, .075, .205, .018])
    colorbar = fig.colorbar(surface_artist, cax=cax, orientation="horizontal")
    colorbar.set_ticks([-bound, 0, bound])
    colorbar.set_ticklabels([f"−{bound:.3f}", "0", f"+{bound:.3f}"])
    colorbar.ax.tick_params(labelsize=7.0, pad=1)
    colorbar.outline.set_linewidth(.4)
    fig.text(.858, .145, f"{100*summary.fraction_ci_favors_gpt56:.2f}%: CI favors 5.6",
             ha="center", va="center", fontsize=7.0, color=TEAL, weight="bold")
    fig.text(.858, .235, "CI boundary (solid)",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.text(.858, .195, "equal loss (dash) · star = weights",
             ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    fig.text(.055, .018,
             f"1,326 declared weights · {100*summary.fraction_uncertain:.2f}% uncertain · none favor GPT-5.5",
             ha="left", va="bottom", fontsize=7.0, color=GRAY)
    save(fig, "fig3_economic_story", "Theory-indexed economic margins and declared-weight sensitivity")
    plt.close(fig)


def figure4_uncertainty() -> None:
    conditional = pd.read_csv(RESULTS / "conditional_uncertainty_contrasts.csv")
    primary = pd.read_csv(RESULTS / "metric_comparisons.csv").set_index("metric")
    metrics = ["W1", "TVD", "CRG", "VDR", "CSR"]
    human_name = "human multinomial cells, fixed countries and model means"
    runs_name = "five-generation resampling, fixed countries and human cells"
    ratio_rows = []
    for metric in metrics:
        country_se = float(primary.loc[metric, "standard_error"])
        h = conditional[(conditional.metric == metric) & (conditional.uncertainty_source == human_name)].iloc[0]
        r = conditional[(conditional.metric == metric) & (conditional.uncertainty_source == runs_name)].iloc[0]
        ratio_rows.append((metric, 100 * h.conditional_standard_error / country_se,
                           100 * r.conditional_standard_error / country_se))
    ratio = pd.DataFrame(ratio_rows, columns=["metric", "human", "runs"])
    ratio.to_csv(SOURCE_DATA / "conditional_to_country_se_ratios.csv", index=False)

    fig = plt.figure(figsize=(5.48, 2.18))
    ax_a = fig.add_axes([.075, .245, .390, .620])
    ax_b = fig.add_axes([.655, .245, .325, .620])

    y = np.arange(len(ratio))[::-1]
    for i, row in ratio.iterrows():
        ax_a.plot([row.human, row.runs], [y[i], y[i]], color=DIVIDER, lw=2.0, zorder=1)
        ax_a.scatter(row.human, y[i], s=32, fc=PRIMARY, ec=WHITE, lw=.55, zorder=3)
        ax_a.scatter(row.runs, y[i], s=33, marker="D", fc=TEAL, ec=WHITE, lw=.55, zorder=3)
    ax_a.axvline(100, color=INK, lw=.75, ls="--")
    ax_a.set_yticks(y, ratio.metric)
    ax_a.set_xlim(0, 115)
    ax_a.set_xlabel("Conditional SE / country-bootstrap SE (%)")
    ax_a.grid(axis="x", color=DIVIDER, lw=.45)
    clean_axes(ax_a)
    panel_title(ax_a, "a", "Conditional / country SE")
    ax_a.legend(
        handles=[
            Line2D([0], [0], marker="o", color="none", markerfacecolor=PRIMARY,
                   markeredgecolor=WHITE, markersize=5.5, label="human cells"),
            Line2D([0], [0], marker="D", color="none", markerfacecolor=TEAL,
                   markeredgecolor=WHITE, markersize=5.5, label="five runs"),
        ], ncol=1, frameon=False, loc="upper right", bbox_to_anchor=(.99, .99),
        borderaxespad=0, handletextpad=.25, labelspacing=.25,
    )

    tvd_primary = primary.loc["TVD"]
    h = conditional[(conditional.metric == "TVD") & (conditional.uncertainty_source == human_name)].iloc[0]
    r = conditional[(conditional.metric == "TVD") & (conditional.uncertainty_source == runs_name)].iloc[0]
    interval_rows = [
        ("country bootstrap", tvd_primary.estimate, tvd_primary.ci_low_bca, tvd_primary.ci_high_bca, INK, "o"),
        ("human-cell sensitivity", h.point_loss_delta_56_minus_55,
         h.centered_sensitivity_interval_low_95, h.centered_sensitivity_interval_high_95, PRIMARY, "o"),
        ("five-run sensitivity", r.point_loss_delta_56_minus_55,
         r.centered_sensitivity_interval_low_95, r.centered_sensitivity_interval_high_95, TEAL, "D"),
    ]
    yb = np.arange(3)[::-1]
    ax_b.axvline(0, color=INK, lw=.75)
    for yy, (name, value, low, high, color, marker) in zip(yb, interval_rows, strict=True):
        ax_b.plot([low, high], [yy, yy], color=color, lw=1.9, solid_capstyle="round")
        ax_b.scatter(value, yy, s=36, marker=marker, fc=color, ec=WHITE, lw=.6, zorder=3)
    ax_b.set_yticks(yb, [row[0] for row in interval_rows])
    ax_b.set_xlim(-.0122, -.0036)
    ax_b.set_xlabel("Δ TVD with 95% interval")
    ax_b.grid(axis="x", color=DIVIDER, lw=.45)
    clean_axes(ax_b)
    panel_title(ax_b, "b", "TVD interval comparison")

    fig.text(.985, .025, "Conditional resampling holds countries fixed; country-bootstrap inference remains primary.",
             ha="right", va="bottom", fontsize=7.0, color=GRAY)
    save(fig, "figS1_uncertainty_sources", "Country, human-cell, and repeated-run uncertainty diagnostics")
    plt.close(fig)


def _rounded_panel(ax: plt.Axes, x: float, y: float, w: float, h: float,
                   edge: str, fill: str, linestyle: str = "-") -> None:
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=.010,rounding_size=.018",
        transform=ax.transAxes, fc=fill, ec=edge, lw=.85, ls=linestyle,
    ))


def _survey_globe(ax: plt.Axes, x: float, y: float, radius: float) -> None:
    ax.add_patch(Circle((x, y), radius, transform=ax.transAxes, fc=COOL, ec=PRIMARY, lw=.9))
    for frac in (-.45, 0, .45):
        ax.plot([x - .86 * radius, x + .86 * radius], [y + frac * radius] * 2,
                transform=ax.transAxes, color=PRIMARY, lw=.4)
    for width in (.40, .72):
        ax.add_patch(Arc((x, y), 2 * radius * width, 2 * radius,
                         transform=ax.transAxes, ec=PRIMARY, lw=.4))
    for dx, dy in ((-.45, .30), (-.22, -.44), (.12, .45), (.48, .10), (.39, -.38)):
        ax.add_patch(Circle((x + dx * radius, y + dy * radius), .07 * radius,
                            transform=ax.transAxes, fc=TEAL, ec=WHITE, lw=.3))
    for shift in (.016, .008, 0):
        ax.add_patch(Rectangle((x + .82 * radius + shift, y - .48 * radius + shift),
                               .070, .090, transform=ax.transAxes, fc=WHITE, ec=INK, lw=.55))


def _chip(ax: plt.Axes, x: float, y: float, color: str) -> None:
    ax.add_patch(FancyBboxPatch((x, y), .064, .064, boxstyle="round,pad=.005",
                                transform=ax.transAxes, fc=WHITE, ec=color, lw=.8))
    for p in (.017, .047):
        for q in (.017, .047):
            ax.add_patch(Circle((x + p, y + q), .004, transform=ax.transAxes, fc=color, ec="none"))
    for offset in (.012, .028, .044, .060):
        ax.plot([x + offset, x + offset], [y - .007, y], transform=ax.transAxes, color=color, lw=.55)
        ax.plot([x + offset, x + offset], [y + .064, y + .071], transform=ax.transAxes, color=color, lw=.55)


def figure5_study_design() -> None:
    """Move a simplified, more natural methods overview to the appendix."""
    fig = plt.figure(figsize=(5.48, 2.10))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.text(.01, .96, "How the comparison is built", transform=ax.transAxes,
            ha="left", va="top", fontsize=9.0, color=INK, weight="bold")
    xs = [.015, .265, .515, .765]
    titles = ["Survey\npatterns", "Paired model\noutputs", "Three\nmeasurements", "Economic\nlens"]
    details = [
        "64 countries\n6 WVS items",
        "2 versions\n5 responses per cell",
        "fidelity\ngeometry · persistence",
        "opportunity\nadjustment\ncoordination",
    ]
    edges = [PRIMARY, PRIMARY, TEAL, AMBER]
    fills = [COOL, WHITE, TEAL_LIGHT, WARM]
    for i, (x, title, detail, edge, fill) in enumerate(zip(xs, titles, details, edges, fills, strict=True)):
        _rounded_panel(ax, x, .20, .205, .57, edge, fill, "--" if i == 3 else "-")
        ax.text(x + .1025, .665, title, transform=ax.transAxes, ha="center", va="center",
                fontsize=7.5, color=INK, weight="bold", linespacing=1.18)
        ax.text(x + .1025, .300, detail, transform=ax.transAxes, ha="center", va="center",
                fontsize=7.0, color=GRAY_DARK, linespacing=1.18)
    _survey_globe(ax, .090, .505, .052)
    _chip(ax, .309, .475, PRIMARY)
    _chip(ax, .389, .475, TEAL)
    # Measurement micro-scene: bars, network, and a small persistence strip.
    for i, h in enumerate((.045, .082, .060)):
        ax.add_patch(Rectangle((.547 + .019 * i, .465), .010, h, transform=ax.transAxes,
                               fc=TEAL, ec="none"))
    nodes = [(.624, .485), (.654, .555), (.694, .490)]
    for a, b in ((0, 1), (1, 2), (0, 2)):
        ax.plot([nodes[a][0], nodes[b][0]], [nodes[a][1], nodes[b][1]],
                transform=ax.transAxes, color=PRIMARY, lw=.65)
    for px, py in nodes:
        ax.add_patch(Circle((px, py), .007, transform=ax.transAxes, fc=WHITE, ec=PRIMARY, lw=.65))
    ax.add_patch(Rectangle((.548, .405), .142, .012, transform=ax.transAxes, fc=PRIMARY, ec="none"))
    ax.add_patch(Rectangle((.681, .405), .009, .012, transform=ax.transAxes, fc=AMBER, ec="none"))
    # Economic triangle.
    triangle = np.array([[.806, .435], [.932, .435], [.869, .585], [.806, .435]])
    ax.plot(triangle[:, 0], triangle[:, 1], transform=ax.transAxes, color=AMBER, lw=.85)
    ax.add_patch(Circle((.875, .493), .010, transform=ax.transAxes, fc=TEAL, ec=WHITE, lw=.5))
    for start, end, color, ls in ((.220, .262, GRAY, "-"), (.470, .512, GRAY, "-"), (.720, .762, AMBER, "--")):
        ax.add_patch(FancyArrowPatch((start, .49), (end, .49), transform=ax.transAxes,
                                     arrowstyle="-|>", mutation_scale=8, lw=.9, ls=ls, color=color))
    ax.text(.5, .075, "Solid = observed / computed    ·    Dashed = theory-guided interpretation",
            transform=ax.transAxes, ha="center", va="center", fontsize=7.0, color=GRAY_DARK)
    save(fig, "figS2_study_design", "How the EthosGPT comparison is built")
    plt.close(fig)
    write_drawio()


def write_drawio() -> None:
    drawio = '''<mxfile host="app.diagrams.net" modified="2026-09-05T00:00:00.000Z" agent="EthosGPT-v1.0" version="24.7.17">
  <diagram id="ethosgpt-methods" name="How the comparison is built">
    <mxGraphModel dx="1400" dy="800" grid="1" gridSize="10" page="1" pageWidth="1200" pageHeight="500"><root><mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="title" value="How the comparison is built" style="text;html=1;fontFamily=Times New Roman;fontSize=24;fontStyle=1;fontColor=#18324A;align=left;" vertex="1" parent="1"><mxGeometry x="35" y="25" width="500" height="40" as="geometry"/></mxCell>
      <mxCell id="survey" value="Survey patterns&#xa;64 countries · 6 WVS items" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#3B5CCC;fillColor=#EAF0FF;fontFamily=Times New Roman;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="35" y="95" width="245" height="220" as="geometry"/></mxCell>
      <mxCell id="models" value="Paired model outputs&#xa;2 versions · 5 responses per cell" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#3B5CCC;fillColor=#FFFFFF;fontFamily=Times New Roman;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="325" y="95" width="245" height="220" as="geometry"/></mxCell>
      <mxCell id="measures" value="Three measurements&#xa;fidelity · geometry · run persistence" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#078C82;fillColor=#E5F4F1;fontFamily=Times New Roman;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="615" y="95" width="245" height="220" as="geometry"/></mxCell>
      <mxCell id="economics" value="Economic reading&#xa;opportunity · adjustment · coordination" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#D88A24;dashed=1;fillColor=#FFF3E8;fontFamily=Times New Roman;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="905" y="95" width="245" height="220" as="geometry"/></mxCell>
      <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#6B7786;strokeWidth=2;" edge="1" parent="1" source="survey" target="models"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#6B7786;strokeWidth=2;" edge="1" parent="1" source="models" target="measures"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="e3" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#D88A24;strokeWidth=2;dashed=1;" edge="1" parent="1" source="measures" target="economics"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="note" value="Solid: observed and computed    ·    Dashed: theory-guided interpretation" style="text;html=1;fontFamily=Times New Roman;fontSize=14;fontColor=#4E5B68;align=center;" vertex="1" parent="1"><mxGeometry x="220" y="350" width="760" height="35" as="geometry"/></mxCell>
    </root></mxGraphModel>
  </diagram>
</mxfile>'''
    (FIGURES / "figS2_study_design.drawio").write_text(drawio + "\n", encoding="utf-8")


def figure6_economic_surface() -> None:
    data = pd.read_csv(RESULTS / "economic_weight_surface.csv")
    distribution = data.weight_distribution_adjustment.to_numpy()
    coordination = data.weight_coordination_legitimacy.to_numpy()
    x = distribution + .5 * coordination
    y = np.sqrt(3) / 2 * coordination
    values = data.delta_weighted_loss_56_minus_55.to_numpy()
    upper = data.ci_high_95.to_numpy()
    bound = max(abs(values.min()), abs(values.max()))
    norm = TwoSlopeNorm(vmin=-bound, vcenter=0, vmax=bound)
    cmap = LinearSegmentedColormap.from_list("ethosgpt_diverging", [TEAL, "#F7F8FA", MAGENTA])

    fig = plt.figure(figsize=(5.48, 3.42))
    ax = fig.add_axes([.115, .315, .770, .585])
    triang = mpl.tri.Triangulation(x, y)
    levels = np.linspace(-bound, bound, 17)
    surface = ax.tricontourf(triang, values, levels=levels, cmap=cmap, norm=norm, antialiased=True)
    robust_boundary = ax.tricontour(triang, upper, levels=[0], colors=[INK], linewidths=1.35)
    zero_boundary = ax.tricontour(triang, values, levels=[0], colors=[AMBER], linewidths=1.1, linestyles="--")
    triangle = np.array([[0, 0], [1, 0], [.5, np.sqrt(3) / 2], [0, 0]])
    ax.plot(triangle[:, 0], triangle[:, 1], color=INK, lw=.85)
    equal_x = .5
    equal_y = np.sqrt(3) / 6
    ax.scatter(equal_x, equal_y, s=48, marker="*", fc=WHITE, ec=INK, lw=.8, zorder=5)
    ax.annotate("equal weights", (equal_x, equal_y), xytext=(8, -9), textcoords="offset points",
                fontsize=7.1, color=INK, ha="left", va="top",
                arrowprops=dict(arrowstyle="-", color=INK, lw=.55))
    ax.text(-.035, -.035, "Opportunity and\nparticipation", ha="left", va="top", weight="bold",
            fontsize=7.5, linespacing=1.18)
    ax.text(1.035, -.035, "Distribution and\nadjustment", ha="right", va="top", weight="bold",
            fontsize=7.5, linespacing=1.18)
    ax.text(.5, np.sqrt(3) / 2 + .035, "Coordination and legitimacy", ha="center", va="bottom",
            weight="bold", fontsize=7.5)
    ax.set_xlim(-.09, 1.09)
    ax.set_ylim(-.10, .98)
    ax.set_aspect("equal")
    ax.set_axis_off()
    fig.text(.5, .970, "Creative-destruction margin sensitivity", ha="center", va="top",
             color=INK, weight="bold", fontsize=9.0)

    cax = fig.add_axes([.265, .105, .470, .026])
    colorbar = fig.colorbar(surface, cax=cax, orientation="horizontal")
    colorbar.set_ticks(np.linspace(-bound, bound, 5))
    colorbar.set_ticklabels([f"{value:.3f}" for value in np.linspace(-bound, bound, 5)])
    colorbar.set_label("Δ weighted squared-TVD loss  ← lower error for GPT-5.6", labelpad=2)
    colorbar.ax.tick_params(labelsize=7.0, pad=1)
    colorbar.outline.set_linewidth(.5)
    handles = [
        Line2D([0], [0], color=INK, lw=1.35, label="95% interval boundary"),
        Line2D([0], [0], color=AMBER, lw=1.1, ls="--", label="equal point loss"),
        Line2D([0], [0], marker="*", color="none", markeredgecolor=INK,
               markerfacecolor=WHITE, markersize=7, label="equal weights"),
    ]
    fig.legend(handles=handles, ncol=3, frameon=False, loc="lower center",
               bbox_to_anchor=(.5, .185), handletextpad=.3, columnspacing=.8)
    save(fig, "figS3_economic_sensitivity", "Continuous economic-weight sensitivity with interval boundary")
    plt.close(fig)


def cleanup_obsolete_assets() -> None:
    old_stems = ["fig1_wave1_design", "fig2_wave1_results", "figS2_spatial_maps"]
    for directory in (FIGURES, RESULT_FIGURES):
        for stem in old_stems:
            for suffix in (".pdf", ".svg", ".png", ".drawio"):
                path = directory / f"{stem}{suffix}"
                if path.exists():
                    path.unlink()
    part_dir = SOURCES / "fig1_spatial_story" / "parts"
    for stem in ("prior_benchmarks", "country_maps", "economic_bridge"):
        for suffix in (".pdf", ".svg", ".png"):
            path = part_dir / f"{stem}{suffix}"
            if path.exists():
                path.unlink()


def write_source_contract() -> None:
    """Write the manuscript-level style, evidence, and source manifest."""
    figures = [
        {
            "stem": "fig1_spatial_story", "number_role": "Figure 1", "reader_task": "framing/evidence",
            "evidence_class": "published context, descriptive reanalysis, current evidence, and theory-guided directions",
            "question": "How do prior benchmarks connect to a paired country-conditioned survey comparison and its economic, agent, and deployment implications?",
            "source_data": ["data/prior_study_benchmark.csv", "data/archived_geometry_benchmark.csv",
                            "data/country_level_spatial_changes.csv", "data/figure1_error_type_examples.csv",
                            "economic_weight_surface.csv", "Natural Earth 1:110m public-domain geometry"],
            "final_size_inches": [5.48, 3.45],
            "master": "figs/fig1_spatial_story.drawio; Python child charts: scripts/make_visual_story_v100.py",
        },
        {
            "stem": "fig2_multiview_results", "number_role": "Figure 2", "reader_task": "evidence",
            "evidence_class": "inferential and descriptive panels",
            "question": "How does the update change country heterogeneity, simultaneous item inference, one outcome-independent country profile, and repeated-output error before interaction?",
            "source_data": ["joint_item_inference.csv", "composition_estimates.csv",
                            "country_question_scores.csv", "country_level_spatial_changes.csv",
                            "data/country_radar_case_selection.csv", "data/country_radar_profiles.csv"],
            "final_size_inches": [5.48, 3.36], "master": "scripts/make_visual_story_v100.py",
        },
        {
            "stem": "fig3_economic_story", "number_role": "Figure 3", "reader_task": "implication",
            "evidence_class": "exploratory theory-indexed inference",
            "question": "Which declared economic margins change and how robust is the sign across weights?",
            "source_data": ["economic_margin_results.csv", "economic_weight_surface.csv",
                            "economic_weight_surface_summary.csv"],
            "final_size_inches": [5.48, 2.68], "master": "scripts/make_visual_story_v100.py",
        },
        {
            "stem": "figS1_uncertainty_sources", "number_role": "Appendix Figure 4", "reader_task": "evidence",
            "evidence_class": "sensitivity analysis",
            "question": "How narrow are conditional sources relative to country-level uncertainty?",
            "source_data": ["conditional_uncertainty_contrasts.csv", "metric_comparisons.csv"],
            "final_size_inches": [5.48, 2.18], "master": "scripts/make_visual_story_v100.py",
        },
        {
            "stem": "figS2_study_design", "number_role": "Appendix Figure 5", "reader_task": "mechanism",
            "evidence_class": "methodological/conceptual", "question": "How is the comparison constructed and interpreted?",
            "source_data": ["protocol metadata and manuscript Sections 1-4"],
            "final_size_inches": [5.48, 2.10], "master": "figs/figS2_study_design.drawio",
        },
        {
            "stem": "figS3_economic_sensitivity", "number_role": "Appendix Figure 8", "reader_task": "implication",
            "evidence_class": "exploratory sensitivity analysis",
            "question": "How does the point estimate and interval conclusion vary continuously over declared weights?",
            "source_data": ["economic_weight_surface.csv"],
            "final_size_inches": [5.48, 3.42], "master": "scripts/make_visual_story_v100.py",
        },
        {
            "stem": "figS4_country_maps", "number_role": "Appendix Figure 6", "reader_task": "heterogeneity",
            "evidence_class": "descriptive country-level sensitivity",
            "question": "Where do TVD and CRG version changes fall across the three predeclared display classes?",
            "source_data": ["country_level_spatial_changes.csv", "figure1_error_type_examples.csv",
                            "Natural Earth 1:110m public-domain geometry"],
            "final_size_inches": [5.48, 2.12], "master": "scripts/make_visual_story_v100.py",
        },
        {
            "stem": "figS5_country_profiles", "number_role": "Appendix Figure 7", "reader_task": "heterogeneity",
            "evidence_class": "descriptive country-level profile cases",
            "question": "What signed six-item residual profiles characterize the lower, near-zero, and higher CRG-change classes without cross-country cancellation?",
            "source_data": ["country_question_scores.csv", "data/country_radar_case_selection.csv",
                            "data/country_radar_profiles.csv"],
            "final_size_inches": [5.48, 2.62], "master": "scripts/make_visual_story_v100.py",
        },
    ]
    for record in figures:
        stem = record["stem"]
        record["exports"] = {suffix[1:]: f"figs/{stem}{suffix}" for suffix in (".pdf", ".svg", ".png")}
        record["sha256"] = {
            suffix[1:]: hashlib.sha256((FIGURES / f"{stem}{suffix}").read_bytes()).hexdigest()
            for suffix in (".pdf", ".svg", ".png")
        }
    manifest = {
        "version": VERSION,
        "iconography_mode": "rich-editorial",
        "semantic_graphics": [
            {
                "concept": "prior multi-model benchmark context",
                "visual_encoding": "published WorldValuesBench success shares, protocol-separated archived CRG points, and the PNAS country-prompting range",
                "shape_ids": ["fig1-published-benchmark", "fig1-archived-crg", "fig1-pnas-range"],
                "origin": "published WorldValuesBench and PNAS Nexus results plus a declared reanalysis of archived complete profiles",
                "evidence_implication": "historical context only; archived results are not pooled with the new API experiment",
            },
            {
                "concept": "country-level change direction and magnitude",
                "visual_encoding": "triangle orientation and color encode direction; area encodes absolute change; external arrows identify lower, near-zero, and higher threshold-defined examples",
                "shape_ids": ["fig1-country-marks", "fig1-country-labels"],
                "origin": "computed from released country-question scores and pinned coordinates",
                "evidence_implication": "descriptive heterogeneity only; no diffusion or causal claim",
            },
            {
                "concept": "survey-to-version audit flow",
                "visual_encoding": "original vector survey, paired-model, and three-lens audit icons form the technical center of the hero figure",
                "shape_ids": ["fig1-survey-profile", "fig1-model-pair", "fig1-audit-lenses"],
                "origin": "study protocol and released paired outputs",
                "evidence_implication": "clarifies what is observed, compared, and computed",
            },
            {
                "concept": "country contrast distribution",
                "visual_encoding": "raincloud combines a neutral density, softly filled quartile box, median line, whiskers, and three threshold-defined point types",
                "shape_ids": ["fig2-country-density", "fig2-country-points"],
                "origin": "64 paired country-level TVD changes",
                "evidence_implication": "shows heterogeneity behind the country-mean contrast",
            },
            {
                "concept": "joint item-family inference",
                "visual_encoding": "aligned forest intervals show signed effects and simultaneous intervals; marker shape separates W1 and TVD and fill shows corrected status",
                "shape_ids": ["fig2-item-intervals", "fig2-item-markers"],
                "origin": "released joint max-T inference table",
                "evidence_implication": "localizes familywise-supported and uncertain item changes",
            },
            {
                "concept": "outcome-independent country directed-profile deviation",
                "visual_encoding": "India is selected as the standardized human-survey profile medoid without using model outcomes; a black circular zero ring is the country human survey, and model-minus-human lines share a symmetric -0.20 to +0.20 scale with redundant model encodings",
                "shape_ids": ["fig2-profile-radar", "fig2-profile-labels"],
                "origin": "released India country-question profiles and reproducible human-only medoid selection",
                "evidence_implication": "the descriptive case avoids cancellation across countries but is neither a national-population estimate nor a claim that India represents any cultural region",
            },
            {
                "concept": "threshold-class country profile cases",
                "visual_encoding": "three appendix radars use one shared symmetric residual scale; lower, near-zero, and higher labels follow the declared CRG-change threshold and each country is the residual-profile medoid within its class",
                "shape_ids": ["fig8-lower-profile", "fig8-near-zero-profile", "fig8-higher-profile"],
                "origin": "released country-question profiles and threshold-class medoid selection ledger",
                "evidence_implication": "the three cases expose heterogeneous signed profiles without replacing the all-country estimand or implying cultural representativeness",
            },
            {
                "concept": "creative-destruction research bridge",
                "visual_encoding": "observed economic-margin intervals lead by a dashed arrow to a bounded box of prospective causal questions",
                "shape_ids": ["fig1-economic-margins", "fig1-prospective-tests"],
                "origin": "released economic-margin results and theory-indexed future-research questions",
                "evidence_implication": "the dashed path is prospective and does not convert representation-loss estimates into welfare or causal effects",
            },
            {
                "concept": "theory-indexed economic robustness",
                "visual_encoding": "simplex position encodes declared weights and fill encodes interval classification",
                "shape_ids": ["fig3-weight-simplex", "fig3-interval-classes"],
                "origin": "released 1,326-vector economic weight surface",
                "evidence_implication": "sensitivity of representation loss, not welfare or policy effects",
            },
            {
                "concept": "uncertainty-source comparison",
                "visual_encoding": "dumbbell ratios and aligned interval lines separate country, human-cell, and run variation",
                "shape_ids": ["fig4-se-ratios", "fig4-tvd-intervals"],
                "origin": "released conditional and country-bootstrap uncertainty tables",
                "evidence_implication": "conditional resampling complements rather than replaces country inference",
            },
        ],
        "hero_graphic": {
            "concept": "prior evidence to paired update comparison to economic and deployment implications",
            "shape_ids": ["fig1-published-benchmark", "fig1-survey-profile",
                          "fig1-country-marks", "fig1-economic-margins"],
        },
        "panel_graphics": {
            "figure1_prior": ["fig1-published-benchmark", "fig1-pnas-range"],
            "figure1_audit": ["fig1-survey-profile", "fig1-model-pair", "fig1-audit-lenses"],
            "figure1_country_evidence": ["fig1-country-marks", "fig1-country-labels"],
            "figure1_frontiers": ["fig1-economic-margins", "fig1-prospective-tests"],
            "figure2_results": ["fig2-country-density", "fig2-item-intervals", "fig2-profile-radar"],
            "appendix_country_profiles": ["fig8-lower-profile", "fig8-near-zero-profile", "fig8-higher-profile"],
        },
        "palette": {
            "ink": INK,
            "surface": SURFACE,
            "primary": PRIMARY,
            "secondary": TEAL,
            "distribution_neutral": DIST,
            "status_accent": AMBER,
            "divider": DIVIDER,
        },
        "composition_mechanism": "Figure 1 uses a protected top row for protocol-separated benchmarks, the paired survey-to-version comparison, and theory-guided implications; the comparison then points into a full-width country-evidence band whose definitions and examples remain outside the map viewport.",
        "grayscale_encoding": "Model and direction remain distinguishable through circle/diamond and up/down-triangle shapes, solid/dashed lines, fill status, and lightness contrast.",
        "authoritative_generators": ["scripts/make_wave1_assets.py", "scripts/make_v070_assets.py",
                                     "scripts/make_visual_story_v100.py", "scripts/polish_submission_tables.py"],
        "style_contract": {
            "insertion_width_inches": 5.48,
            "font_family": "Nimbus Roman (Times-compatible), matching the manuscript body",
            "effective_type_target_pt": 8.0,
            "effective_type_floor_pt": 7.0,
            "background": "white",
            "palette": {
                "ink": INK, "gpt55_primary": PRIMARY, "gpt56_or_lower_error": TEAL,
                "higher_error": MAGENTA, "status": AMBER, "neutral": GRAY,
                "distribution_neutral": DIST, "surface": SURFACE, "divider": DIVIDER,
            },
            "redundant_encoding": "model uses color plus marker/line style; direction uses color plus triangle orientation; significance uses fill plus caption",
        },
        "format_contract": {
            "authoritative": ["PDF", "SVG", "Python or draw.io master"],
            "preview_only": "PNG",
            "embedded_raster_images": False,
            "live_svg_text": True,
        },
        "figures": figures,
    }
    (SOURCES / "semantic_graphics_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    readme = [
        f"# Figure-source contract (v{VERSION})", "",
        "Run `python scripts/make_visual_story_v100.py` after the analysis and supporting table-generation stages.",
        "PDF and SVG are authoritative; PNG is preview-only. All quantitative marks map to released CSV files.", "",
        "## House style", "",
        f"- Ink `{INK}`; GPT-5.5 `{PRIMARY}`; GPT-5.6/lower error `{TEAL}`; higher error `{MAGENTA}`; status `{AMBER}`.",
        "- Nimbus Roman (Times-compatible), 8 pt target and 7 pt fail-closed floor at 5.48-inch insertion width.",
        "- White background, restrained grid, no rainbow scale, and redundant shape/line encoding.", "",
        "## Figure map", "",
        "| Figure | Reader task | Evidence class | Authoritative source |",
        "|---|---|---|---|",
    ]
    for record in figures:
        readme.append(f"| {record['number_role']} | {record['reader_task']} | {record['evidence_class']} | `{record['master']}` |")
    readme += ["", "See `semantic_graphics_manifest.json` for per-export hashes, data lineage, final dimensions, and scientific questions.", ""]
    (SOURCES / "README.md").write_text("\n".join(readme), encoding="utf-8")

    for record in figures:
        directory = SOURCES / record["stem"]
        directory.mkdir(parents=True, exist_ok=True)
        lines = [
            f"# {record['number_role']}: {record['stem']}", "",
            f"- Reader task: {record['reader_task']}",
            f"- Evidence class: {record['evidence_class']}",
            f"- Scientific question: {record['question']}",
            f"- Final size: {record['final_size_inches'][0]} x {record['final_size_inches'][1]} inches",
            f"- Editable/reproducible master: `{record['master']}`", "",
            "Source data:", "",
        ]
        lines.extend(f"- `{item}`" for item in record["source_data"])
        lines += ["", "Exports: live-text SVG, vector PDF, and preview PNG in `paper/figs/`.", ""]
        (directory / "README.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    set_style()
    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    SOURCE_DATA.mkdir(parents=True, exist_ok=True)
    cleanup_obsolete_assets()
    figure1_spatial_story()
    figure2_multiview()
    figure3_economic_story()
    figure4_uncertainty()
    figure5_study_design()
    figure6_economic_surface()
    figure7_country_profiles()
    write_source_contract()
    # Run the stale-artifact guard again after all export writers. This makes the
    # final contract insensitive to older generators invoked earlier in a rebuild.
    cleanup_obsolete_assets()
    print("PASS: EthosGPT v1.0.0 visual sequence generated")


if __name__ == "__main__":
    main()
