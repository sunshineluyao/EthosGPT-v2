#!/usr/bin/env python3
"""Build the v0.7 visual story from released source data.

The main paper uses three figures: an editable evidence-boundary diagram, a
dependence-aware results figure, and a theory-indexed economic sensitivity
figure.  The country maps remain a full-width appendix figure so that their
labels are legible and their descriptive status is not mistaken for a causal
result.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import xml.etree.ElementTree as ET

os.environ.setdefault("SOURCE_DATE_EPOCH", "1787961600")
os.environ.setdefault("TZ", "UTC")

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Rectangle
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "experiments/gpt55_gpt56_64country"
RESULTS = EXP / "results"
FIGURES = ROOT / "results/figures"
RESULT_FIGURES = ROOT / "results/figures"

INK = "#18324A"
PRIMARY = "#315EFB"
TEAL = "#14877D"
MAGENTA = "#A43E6C"
ORANGE = "#D97745"
GRAY = "#5F6B78"
SURFACE = "#F5F7FB"
COOL = "#EAF0FF"
TEAL_LIGHT = "#E5F4F1"
WARM = "#FFF3EC"
DIVIDER = "#CBD5E1"


def set_style() -> None:
    mpl.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Liberation Sans"],
        "font.size": 8.2,
        "axes.titlesize": 8.8,
        "axes.labelsize": 7.7,
        "xtick.labelsize": 7.3,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.3,
        "axes.linewidth": 0.7,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "ethosgpt-v0.7.0",
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.025,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
    })


def postprocess_svg(path: Path, title: str) -> None:
    """Add accessibility metadata and remove safe, plot-area clip attributes.

    Every plotted element is constructed inside its declared axes.  Removing
    Matplotlib's redundant clip-path attributes keeps the editable SVGs easy to
    inspect without changing the rendered geometry.
    """
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
        viewbox = (root.get("viewBox") or "0 0 240 180").split()
        root.set("width", viewbox[2])
        root.set("height", viewbox[3])
    tree.write(path, encoding="utf-8", xml_declaration=True)


def save(fig: plt.Figure, stem: str, title: str) -> None:
    metadata = {"Creator": "EthosGPT v0.7.0 reproducible visual-story pipeline"}
    FIGURES.mkdir(parents=True, exist_ok=True)
    RESULT_FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(RESULT_FIGURES / f"{stem}.pdf", metadata=metadata)
    fig.savefig(RESULT_FIGURES / f"{stem}.svg", metadata=metadata)
    fig.savefig(RESULT_FIGURES / f"{stem}.png", dpi=360, metadata=metadata)
    postprocess_svg(RESULT_FIGURES / f"{stem}.svg", title)


def box(ax, x, y, w, h, edge, fill="white", linestyle="-", lw=.9):
    patch = FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=.010,rounding_size=.018",
        transform=ax.transAxes, fc=fill, ec=edge, lw=lw, ls=linestyle,
    )
    ax.add_patch(patch)
    return patch


def survey_icon(ax, x, y, scale=1.0):
    for shift in (.020, .010, 0):
        ax.add_patch(Rectangle(
            (x + shift * scale, y + shift * scale), .075 * scale, .105 * scale,
            transform=ax.transAxes, fc="white", ec=INK, lw=.85,
        ))
    for index, width in enumerate((.045, .057, .035)):
        yy = y + (.079 - index * .026) * scale
        ax.plot([x + .014 * scale, x + (.014 + width) * scale], [yy, yy],
                transform=ax.transAxes, color=INK, lw=1.0)


def globe_icon(ax, x, y, radius):
    ax.add_patch(Circle((x, y), radius, transform=ax.transAxes,
                        fc=COOL, ec=PRIMARY, lw=1.0))
    for frac in (-.48, 0, .48):
        ax.plot([x-radius*.88, x+radius*.88], [y+frac*radius, y+frac*radius],
                transform=ax.transAxes, color=PRIMARY, lw=.45, alpha=.75)
    for width in (.38, .70):
        ax.add_patch(Arc((x, y), 2*radius*width, 2*radius,
                         transform=ax.transAxes, ec=PRIMARY, lw=.45))
    for dx, dy in ((-.55,.28),(-.26,-.45),(.05,.48),(.40,.15),(.54,-.37),(-.58,-.18)):
        ax.add_patch(Circle((x+dx*radius, y+dy*radius), radius*.065,
                            transform=ax.transAxes, fc=TEAL, ec="white", lw=.35))


def chip_icon(ax, x, y, color, label):
    ax.add_patch(FancyBboxPatch(
        (x, y), .074, .074, boxstyle="round,pad=.006",
        transform=ax.transAxes, fc="white", ec=color, lw=.9,
    ))
    for offset in (.012, .030, .048, .066):
        ax.plot([x+offset, x+offset], [y-.010, y], transform=ax.transAxes, color=color, lw=.7)
        ax.plot([x+offset, x+offset], [y+.074, y+.084], transform=ax.transAxes, color=color, lw=.7)
    for px, py in ((.022,.023),(.052,.023),(.022,.052),(.052,.052)):
        ax.add_patch(Circle((x+px, y+py), .0045, transform=ax.transAxes, fc=color, ec="none"))
    ax.text(x+.037, y-.026, label, transform=ax.transAxes, ha="center", va="top",
            fontsize=6.2, color=GRAY)


def distribution_icon(ax, x, y, width, height):
    first = (.62,.36,.78,.47,.28)
    second = (.51,.43,.66,.58,.34)
    step = width/6
    for i, (a, b) in enumerate(zip(first, second, strict=True)):
        xx = x + (i+.65)*step
        ax.add_patch(Rectangle((xx, y), step*.26, a*height, transform=ax.transAxes,
                               fc=GRAY, ec="none", alpha=.42))
        ax.add_patch(Rectangle((xx+step*.28, y), step*.26, b*height,
                               transform=ax.transAxes, fc=TEAL, ec="none"))
    ax.plot([x, x+width], [y, y], transform=ax.transAxes, color=INK, lw=.6)


def network_icon(ax, x, y, width, height):
    nodes = [(0,.25),(.28,.80),(.55,.38),(.83,.72),(1,.20)]
    pts = [(x+px*width, y+py*height) for px, py in nodes]
    for a, b in ((0,1),(0,2),(1,2),(1,3),(2,3),(2,4),(3,4)):
        ax.plot([pts[a][0], pts[b][0]], [pts[a][1], pts[b][1]],
                transform=ax.transAxes, color=PRIMARY, lw=.65, alpha=.72)
    for i, (px, py) in enumerate(pts):
        ax.add_patch(Circle((px, py), .009, transform=ax.transAxes,
                            fc=TEAL if i in (1,2,3) else "white", ec=PRIMARY, lw=.8))


def evidence_chip(ax, x, width, title, detail, color, icon):
    box(ax, x, .175, width, .150, color, lw=.8)
    if icon == "interval":
        ax.plot([x+.020, x+.074], [.245, .245], transform=ax.transAxes, color=color, lw=1.5)
        ax.add_patch(Circle((x+.047, .245), .006, transform=ax.transAxes,
                            fc=color, ec="white", lw=.4))
    elif icon == "items":
        for i, yy in enumerate((.270,.245,.220)):
            ax.add_patch(Circle((x+.038, yy), .0055, transform=ax.transAxes,
                                fc=color if i < 2 else "white", ec=color, lw=.6))
            ax.plot([x+.049, x+.078], [yy, yy], transform=ax.transAxes, color=DIVIDER, lw=.8)
    else:
        ax.add_patch(Rectangle((x+.018,.216), .062,.055, transform=ax.transAxes,
                               fc=PRIMARY, ec="none"))
        ax.add_patch(Rectangle((x+.077,.216), .0035,.055, transform=ax.transAxes,
                               fc=ORANGE, ec="none"))
    ax.text(x+.090, .272, title, transform=ax.transAxes, ha="left", va="center",
            color=INK, fontsize=6.8, weight="bold")
    ax.text(x+.090, .219, detail, transform=ax.transAxes, ha="left", va="center",
            color=GRAY, fontsize=6.1, linespacing=1.08)


def figure1() -> None:
    fig, ax = plt.subplots(figsize=(5.48, 2.36))
    ax.set_axis_off()
    ax.text(.015, .970, "Whose values enter a model update?", transform=ax.transAxes,
            ha="left", va="top", fontsize=10.4, weight="bold", color=INK)

    panels = [
        (.015, "a", "Human values", "64 countries\n6 survey items", PRIMARY, COOL),
        (.350, "b", "Model update", "2 versions\n5 runs per cell", PRIMARY, "white"),
        (.685, "c", "Measured change", "fidelity · geometry\nfinite-five", TEAL, TEAL_LIGHT),
    ]
    for x, label, title, detail, edge, fill in panels:
        box(ax, x, .485, .300, .330, edge, fill)
        ax.text(x + .016, .782, label, transform=ax.transAxes, fontsize=8.5,
                weight="bold", color=INK, va="top")
        ax.text(x + .057, .782, title, transform=ax.transAxes, fontsize=7.9,
                weight="bold", color=INK, va="top", ha="left")
        ax.text(x + .150, .535, detail, transform=ax.transAxes, fontsize=7.3,
                color=GRAY, ha="center", va="center", linespacing=1.15)

    globe_icon(ax, .105, .660, .062)
    survey_icon(ax, .177, .607, .78)
    chip_icon(ax, .410, .650, PRIMARY, "")
    chip_icon(ax, .520, .650, TEAL, "")
    distribution_icon(ax, .412, .585, .184, .050)
    distribution_icon(ax, .716, .675, .090, .054)
    network_icon(ax, .835, .665, .100, .060)
    ax.add_patch(Rectangle((.760, .585), .160, .025, transform=ax.transAxes,
                           fc=PRIMARY, ec="none"))
    ax.add_patch(Rectangle((.918, .585), .006, .025, transform=ax.transAxes,
                           fc=ORANGE, ec="none"))
    for x0, x1 in ((.321, .348), (.656, .683)):
        ax.add_patch(FancyArrowPatch((x0, .650), (x1, .650), transform=ax.transAxes,
                                     arrowstyle="-|>", mutation_scale=9, lw=1.0, color=GRAY))

    findings = [
        (.015, "Overall fidelity", "TVD Δ −0.0080\n95% CI below zero", TEAL),
        (.350, "Issue-specific gains", "Q106 TVD\nQ108 W1 and TVD", TEAL),
        (.685, "Averaging is limited", "Five-run mean removes\n1.18–1.31%", ORANGE),
    ]
    for x, title, detail, color in findings:
        box(ax, x, .225, .300, .175, color, "white", lw=.8)
        ax.text(x + .018, .365, title, transform=ax.transAxes, fontsize=7.7,
                color=INK, weight="bold", va="top")
        ax.text(x + .150, .252, detail, transform=ax.transAxes, fontsize=7.1,
                color=GRAY, va="center", ha="center", linespacing=1.12)

    box(ax, .015, .035, .970, .095, ORANGE, WARM, "--", .8)
    ax.text(.035, .083, "Theory-indexed lens:", transform=ax.transAxes,
            ha="left", va="center", color=ORANGE, fontsize=7.3, weight="bold")
    ax.text(.400, .083, "opportunity · adjustment · coordination",
            transform=ax.transAxes, ha="left", va="center", color=INK, fontsize=7.3)
    save(fig, "fig1_wave1_design", "EthosGPT study design and evidence boundary")
    plt.close(fig)
    write_drawio()
    write_vector_assets()


def forest(ax, frame, label_col, estimate_col, low_col, high_col, sig_col,
           title, xlim, marker="o"):
    data=frame.reset_index(drop=True)
    y=np.arange(len(data))[::-1]
    ax.axvspan(xlim[0],0,color=TEAL_LIGHT,zorder=0)
    ax.axvline(0,color=INK,lw=.8,zorder=1)
    for i,row in data.iterrows():
        value=float(row[estimate_col]); color=TEAL if value<0 else MAGENTA
        ax.plot([row[low_col],row[high_col]],[y[i],y[i]],color=color,lw=1.55,zorder=2)
        filled=bool(row[sig_col])
        ax.scatter(value,y[i],s=31,marker=marker,fc=color if filled else "white",
                   ec=color,lw=1.0,zorder=3)
    ax.set_yticks(y,data[label_col]); ax.set_xlim(*xlim)
    ax.grid(axis="x",color=DIVIDER,lw=.45,zorder=0)
    ax.spines[["top","right","left"]].set_visible(False)
    ax.tick_params(axis="y",length=0)
    ax.set_title(title,loc="left",color=INK,weight="bold",pad=3)


def figure2() -> None:
    global_data=pd.read_csv(RESULTS/"metric_comparisons.csv")
    global_data["label"]=global_data.metric.map({
        "W1":"W1","TVD":"TVD","CRG":"CRG","VDR":"|VDR-1|","CSR":"1-CSR",
    })
    global_data["sig"]=global_data.holm_p_five_metrics<=.05
    joint=pd.read_csv(RESULTS/"joint_item_inference.csv")
    joint["label"]=joint.question_id.map({
        "Q48":"Q48 Agency","Q57":"Q57 Trust","Q106":"Q106 Distribution",
        "Q108":"Q108 Responsibility","Q121":"Q121 Immigration*","Q159":"Q159 Science",
    })
    composition=pd.read_csv(RESULTS/"composition_summary.csv")

    fig=plt.figure(figsize=(5.48,2.42))
    gs=fig.add_gridspec(1,3,width_ratios=(.92,1.78,1.12),wspace=.80)
    ax_a=fig.add_subplot(gs[0,0]); ax_b=fig.add_subplot(gs[0,1]); ax_c=fig.add_subplot(gs[0,2])
    forest(ax_a,global_data,"label","estimate","ci_low_bca","ci_high_bca","sig",
           "a  Global (Holm)",(-.060,.090))
    ax_a.set_xlabel("Target-loss Δ")
    ax_a.set_xticks([-.06,0,.06])

    w1=joint[joint.metric=="W1"].reset_index(drop=True)
    tvd=joint[joint.metric=="TVD"].reset_index(drop=True)
    labels=list(w1.label); y=np.arange(len(labels))[::-1]
    ax_b.axvspan(-.043,0,color=TEAL_LIGHT,zorder=0); ax_b.axvline(0,color=INK,lw=.8,zorder=1)
    for i,label in enumerate(labels):
        if label.startswith("Distribution") or label.startswith("Responsibility"):
            ax_b.axhspan(y[i]-.42,y[i]+.42,color=COOL,zorder=.2)
    for offset,frame,marker in ((.12,w1,"o"),(-.12,tvd,"s")):
        for i,row in frame.iterrows():
            value=row.delta_56_minus_55; color=TEAL if value<0 else MAGENTA
            yy=y[i]+offset
            ax_b.plot([row.simultaneous_ci_low_95,row.simultaneous_ci_high_95],[yy,yy],
                      color=color,lw=1.35,zorder=2)
            filled=row.joint_max_t_p_fwer<=.05
            ax_b.scatter(value,yy,s=27,marker=marker,fc=color if filled else "white",
                         ec=color,lw=.95,zorder=3)
    ax_b.set_yticks(y,labels); ax_b.set_xlim(-.043,.023)
    ax_b.set_xlabel("Error Δ (simultaneous 95% CI)")
    ax_b.set_title("b  Item family  ○ W1   □ TVD",loc="left",color=INK,weight="bold",pad=3)
    ax_b.grid(axis="x",color=DIVIDER,lw=.45); ax_b.spines[["top","right","left"]].set_visible(False)
    ax_b.tick_params(axis="y",length=0)
    models=["GPT-5.5","GPT-5.6 Sol"]
    shares=[]; lows=[]; highs=[]
    for model in models:
        part=composition[composition.comparison==model].set_index("component")
        row=part.loc["share_of_individual_error_removed_by_five_generation_average"]
        shares.append(100*float(row["estimate"]))
        lows.append(100*float(row["ci_low_bca"]))
        highs.append(100*float(row["ci_high_bca"]))
    ybar=np.arange(2)[::-1]
    for yy,value,low,high in zip(ybar,shares,lows,highs,strict=True):
        ax_c.plot([low,high],[yy,yy],color=ORANGE,lw=1.8,solid_capstyle="round")
        ax_c.scatter(value,yy,s=38,fc=ORANGE,ec="white",lw=.7,zorder=3)
        ax_c.text(value,yy+.24,f"{value:.2f}%",ha="center",va="bottom",
                  color=INK,fontsize=7.3,weight="bold")
    ax_c.set_yticks(ybar,models); ax_c.set_xlim(.85,1.65)
    ax_c.set_xlabel("Single-run error removed (%)")
    ax_c.set_title("c  Five-run averaging",loc="left",color=INK,weight="bold",pad=3)
    ax_c.grid(axis="x",color=DIVIDER,lw=.45)
    ax_c.spines[["top","right","left"]].set_visible(False); ax_c.tick_params(axis="y",length=0)
    ax_c.set_ylim(-.55,1.55)
    ax_c.text(.98,-.42,"≈99% remains",ha="left",va="center",color=GRAY,fontsize=7.2)
    fig.subplots_adjust(left=.082,right=.995,top=.91,bottom=.20)
    save(fig,"fig2_wave1_results","Global, item-level, and finite-five composition results")
    plt.close(fig)


def figure3() -> None:
    data=pd.read_csv(RESULTS/"economic_weight_surface.csv")
    margins=pd.read_csv(RESULTS/"economic_margin_results.csv")
    summary=pd.read_csv(RESULTS/"economic_weight_surface_summary.csv").iloc[0]
    distribution=data.weight_distribution_adjustment.to_numpy()
    coordination=data.weight_coordination_legitimacy.to_numpy()
    x=distribution+.5*coordination; y=np.sqrt(3)/2*coordination

    fig=plt.figure(figsize=(5.48,1.65))
    gs=fig.add_gridspec(1,3,width_ratios=(1.48,1.16,1.02),wspace=.54)
    ax_a=fig.add_subplot(gs[0,0]); ax_b=fig.add_subplot(gs[0,1]); ax_c=fig.add_subplot(gs[0,2])
    short={"Opportunity and participation":"Opportunity",
           "Distribution and adjustment":"Adjustment",
           "Coordination and legitimacy":"Coordination"}
    yy=np.arange(len(margins))[::-1]
    ax_a.axvspan(-.032,0,color=TEAL_LIGHT,zorder=0); ax_a.axvline(0,color=INK,lw=.8)
    for i,row in margins.reset_index(drop=True).iterrows():
        color=TEAL if row.delta_estimate<0 else MAGENTA
        sig=row.holm_p_three_margins<=.05
        ax_a.plot([row.delta_ci_low_bca,row.delta_ci_high_bca],[yy[i],yy[i]],color=color,lw=1.7)
        ax_a.scatter(row.delta_estimate,yy[i],s=34,fc=color if sig else "white",
                     ec=color,lw=1.0,zorder=3)
    ax_a.set_yticks(yy,[short[v] for v in margins.margin]); ax_a.set_xlim(-.031,.008)
    ax_a.set_xlabel("Squared-TVD loss Δ")
    ax_a.set_title("a  Economic margins",loc="left",color=INK,weight="bold",pad=2)
    ax_a.spines[["top","right","left"]].set_visible(False); ax_a.tick_params(axis="y",length=0)
    ax_a.grid(axis="x",color=DIVIDER,lw=.45)

    robust=data.classification.str.startswith("GPT-5.6 lower").to_numpy()
    ax_b.scatter(x[robust],y[robust],c=TEAL,s=12,marker="h",linewidth=0,
                 label="95% CI favors 5.6")
    ax_b.scatter(x[~robust],y[~robust],c="#B8C0C8",s=12,marker="h",linewidth=0,
                 label="uncertain")
    triangle=np.array([[0,0],[1,0],[.5,np.sqrt(3)/2],[0,0]])
    ax_b.plot(triangle[:,0],triangle[:,1],color=INK,lw=.8)
    ax_b.text(-.02,-.02,"O",ha="left",va="top",color=INK,fontsize=7.3,weight="bold")
    ax_b.text(1.02,-.02,"A",ha="right",va="top",color=INK,fontsize=7.3,weight="bold")
    ax_b.text(.5,np.sqrt(3)/2+.02,"C",ha="center",va="bottom",
              color=INK,fontsize=7.3,weight="bold")
    ax_b.set_xlim(-.06,1.06); ax_b.set_ylim(-.08,.94); ax_b.set_aspect("equal"); ax_b.set_axis_off()
    ax_b.set_title("b  All 1,326 weight CIs",loc="left",color=INK,weight="bold",pad=2)

    fav=100*float(summary.fraction_ci_favors_gpt56)
    uncertain=100*float(summary.fraction_uncertain)
    ax_c.set_axis_off()
    ax_c.set_title("c  Interval conclusion",loc="left",color=INK,weight="bold",pad=2)
    ax_c.text(.02,.71,f"{fav:.2f}%",transform=ax_c.transAxes,ha="left",va="center",
              color=TEAL,fontsize=13.0,weight="bold")
    ax_c.text(.02,.52,"95% intervals entirely\nfavor GPT-5.6",transform=ax_c.transAxes,
              ha="left",va="center",color=INK,fontsize=7.4,linespacing=1.15)
    ax_c.text(.02,.25,f"{uncertain:.2f}% uncertain · 0% favor 5.5",
              transform=ax_c.transAxes,ha="left",va="center",color=GRAY,fontsize=7.3)
    ax_c.add_patch(Rectangle((.02,.08),.84*fav/100,.050,transform=ax_c.transAxes,fc=TEAL,ec="none"))
    ax_c.add_patch(Rectangle((.02+.84*fav/100,.08),.84*uncertain/100,.050,
                             transform=ax_c.transAxes,fc="#B8C0C8",ec="none"))
    fig.subplots_adjust(left=.105,right=.99,top=.88,bottom=.23)
    save(fig,"fig3_economic_story","Theory-indexed economic margins and weight sensitivity")
    plt.close(fig)


def write_drawio() -> None:
    drawio='''<mxfile host="app.diagrams.net" modified="2026-09-03T00:00:00.000Z" agent="EthosGPT-v0.7" version="24.7.17">
  <diagram id="ethosgpt-visual-story" name="Figure 1 graphical abstract">
    <mxGraphModel dx="1400" dy="800" grid="1" gridSize="10" page="1" pageWidth="1200" pageHeight="620"><root><mxCell id="0"/><mxCell id="1" parent="0"/>
      <mxCell id="title" value="Whose values enter a model update?" style="text;html=1;fontFamily=Arial;fontSize=24;fontStyle=1;fontColor=#18324A;align=left;" vertex="1" parent="1"><mxGeometry x="40" y="25" width="620" height="40" as="geometry"/></mxCell>
      <mxCell id="human" value="a  Human comparison&#xa;64 countries · 6 survey items" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#315EFB;fillColor=#EAF0FF;fontFamily=Arial;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="40" y="90" width="330" height="190" as="geometry"/></mxCell>
      <mxCell id="audit" value="b  Paired version audit&#xa;GPT-5.5 vs GPT-5.6 Sol · 5 runs" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#315EFB;fillColor=#FFFFFF;fontFamily=Arial;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="435" y="90" width="330" height="190" as="geometry"/></mxCell>
      <mxCell id="changes" value="c  Three diagnostic lenses&#xa;fidelity · geometry · finite-five" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#14877D;fillColor=#E5F4F1;fontFamily=Arial;fontSize=16;fontColor=#18324A;spacing=14;" vertex="1" parent="1"><mxGeometry x="830" y="90" width="330" height="190" as="geometry"/></mxCell>
      <mxCell id="e1" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#5F6B78;strokeWidth=2;" edge="1" parent="1" source="human" target="audit"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="e2" style="edgeStyle=orthogonalEdgeStyle;rounded=1;html=1;endArrow=block;strokeColor=#5F6B78;strokeWidth=2;" edge="1" parent="1" source="audit" target="changes"><mxGeometry relative="1" as="geometry"/></mxCell>
      <mxCell id="f1" value="Overall fidelity&#xa;TVD Δ −0.0080 · 95% CI below 0" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#14877D;fillColor=#FFFFFF;fontFamily=Arial;fontSize=14;fontColor=#18324A;" vertex="1" parent="1"><mxGeometry x="40" y="315" width="330" height="105" as="geometry"/></mxCell>
      <mxCell id="f2" value="Issue-specific gains&#xa;Q106 TVD · Q108 W1/TVD" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#14877D;fillColor=#FFFFFF;fontFamily=Arial;fontSize=14;fontColor=#18324A;" vertex="1" parent="1"><mxGeometry x="435" y="315" width="330" height="105" as="geometry"/></mxCell>
      <mxCell id="f3" value="Averaging is limited&#xa;Five-run mean removes 1.18–1.31%" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#D97745;fillColor=#FFFFFF;fontFamily=Arial;fontSize=14;fontColor=#18324A;" vertex="1" parent="1"><mxGeometry x="830" y="315" width="330" height="105" as="geometry"/></mxCell>
      <mxCell id="lens" value="Theory-indexed interpretation: opportunity · adjustment · coordination" style="rounded=1;whiteSpace=wrap;html=1;strokeColor=#D97745;dashed=1;fillColor=#FFF3EC;fontFamily=Arial;fontSize=14;fontColor=#18324A;" vertex="1" parent="1"><mxGeometry x="40" y="460" width="1120" height="70" as="geometry"/></mxCell>
    </root></mxGraphModel>
  </diagram>
</mxfile>'''
    (FIGURES/"fig1_wave1_design.drawio").write_text(drawio+"\n",encoding="utf-8")


def write_vector_assets() -> None:
    root=ROOT/"assets/figure_sources/clip-art-set"; assets=root/"assets"
    assets.mkdir(parents=True,exist_ok=True)
    svgs={
      "asset-survey-globe.svg":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180"><g fill="none" stroke="#18324A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><circle cx="80" cy="90" r="52" fill="#EAF0FF" stroke="#315EFB"/><path d="M29 90h102M80 38c-25 22-25 82 0 104M80 38c25 22 25 82 0 104M37 65h86M37 115h86" stroke="#315EFB" stroke-width="2"/><g fill="#14877D" stroke="white" stroke-width="2"><circle cx="50" cy="70" r="6"/><circle cx="71" cy="115" r="6"/><circle cx="96" cy="60" r="6"/><circle cx="112" cy="103" r="6"/></g><rect x="128" y="53" width="76" height="94" rx="4" fill="white"/><rect x="139" y="42" width="76" height="94" rx="4" fill="white"/><path d="M153 70h48M153 90h38M153 110h44"/></g></svg>',
      "asset-paired-audit.svg":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180"><g fill="none" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><rect x="30" y="35" width="64" height="64" rx="10" fill="white" stroke="#315EFB"/><rect x="146" y="35" width="64" height="64" rx="10" fill="white" stroke="#14877D"/><g fill="#315EFB"><circle cx="50" cy="55" r="5"/><circle cx="74" cy="55" r="5"/><circle cx="50" cy="79" r="5"/><circle cx="74" cy="79" r="5"/></g><g fill="#14877D"><circle cx="166" cy="55" r="5"/><circle cx="190" cy="55" r="5"/><circle cx="166" cy="79" r="5"/><circle cx="190" cy="79" r="5"/></g><path d="M96 67h48" stroke="#5F6B78"/><circle cx="120" cy="67" r="28" stroke="#18324A"/><path d="M140 87l24 24" stroke="#18324A"/><path d="M36 137h168" stroke="#18324A"/></g></svg>',
      "asset-measurement-lenses.svg":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180"><g fill="none" stroke="#18324A" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 138h58"/><g fill="#14877D" stroke="none"><rect x="28" y="94" width="8" height="44"/><rect x="42" y="73" width="8" height="65"/><rect x="56" y="105" width="8" height="33"/></g><g stroke="#315EFB"><path d="M96 124l25-54 31 38 27-58 39 72"/><g fill="white"><circle cx="96" cy="124" r="6"/><circle cx="121" cy="70" r="6"/><circle cx="152" cy="108" r="6"/><circle cx="179" cy="50" r="6"/><circle cx="218" cy="122" r="6"/></g></g><rect x="26" y="151" width="185" height="12" fill="#315EFB" stroke="none"/><rect x="202" y="151" width="9" height="12" fill="#D97745" stroke="none"/></g></svg>',
      "asset-economic-margins.svg":'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 180"><g fill="none" stroke="#D97745" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M120 25L35 145h170z" fill="#FFF3EC"/><path d="M120 25v120M35 145l127-60M205 145L78 85" stroke="#CBD5E1" stroke-width="2"/><circle cx="95" cy="111" r="9" fill="#14877D" stroke="white"/><circle cx="151" cy="95" r="7" fill="#315EFB" stroke="white"/><circle cx="124" cy="65" r="6" fill="#D97745" stroke="white"/></g></svg>',
    }
    concepts={
        "asset-survey-globe.svg":("survey evidence across countries","data"),
        "asset-paired-audit.svg":("paired model comparison","instrument"),
        "asset-measurement-lenses.svg":("distribution, geometry, and persistence measurements","hero"),
        "asset-economic-margins.svg":("theory-indexed economic margins","process"),
    }
    records=[]
    for name,svg in svgs.items():
        path=assets/name; path.write_text(svg+"\n",encoding="utf-8")
        concept,role=concepts[name]
        postprocess_svg(path, concept)
        records.append({
            "id":name[:-4],"concept":concept,"semantic_role":role,
            "source_locator":"manuscript Sections 1-4","evidence_status":"conceptual-mechanism",
            "file":f"assets/{name}","format":"svg","source_type":"original-vector",
            "description":concept,"alt_text":f"Unlabeled vector micro-scene for {concept}.",
            "visual_recipe":["recognizable scientific objects","one visible operation cue","matched outline and palette"],
            "unsupported_implications":["causal effect","certification","measured magnitude"],
            "palette_roles":["ink","surface","primary","secondary","status_accent"],
            "viewpoint":"front","placement":{"preferred_panel":"Figure 1","anchor":"center",
                "min_width_px":180,"clear_space_percent":12,"background_compatibility":"light"},
            "provenance":{"authoring_method":"Native SVG geometry","created_on":"2026-09-03",
                "editable_master":f"assets/{name}"},
            "checksum_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        })
    fig,axes=plt.subplots(2,2,figsize=(5.2,3.6))
    for ax,label,color in zip(axes.ravel(),["Survey evidence","Paired audit","Measurement lenses","Economic margins"],
                              [PRIMARY,PRIMARY,TEAL,ORANGE],strict=True):
        ax.set_axis_off(); box(ax,.06,.12,.88,.70,color,SURFACE)
        ax.text(.5,.60,label,ha="center",va="center",transform=ax.transAxes,
                color=INK,fontsize=9,weight="bold")
        ax.text(.5,.39,"original SVG master",ha="center",va="center",
                transform=ax.transAxes,color=GRAY,fontsize=7)
    fig.tight_layout(); fig.savefig(root/"contact-sheet.png",dpi=240); plt.close(fig)
    manifest={
        "schema_version":"1.0","set_id":"ethosgpt-figure1-vector-set-v070",
        "title":"EthosGPT Figure 1 semantic vector set",
        "purpose":"Supply coherent, editable scientific micro-scenes for the Figure 1 graphical abstract.",
        "source":{"kind":"paper","title":"EthosGPT v0.7.0","locator":"Sections 1-4"},
        "target_figure":{"type":"graphical abstract","background":"light",
                         "placement":"Figure 1 at full manuscript width"},
        "evidence_boundary":"These vector assets identify concepts and operations. They do not encode measured values, causal effects, certification, or implementation status.",
        "art_direction":{"mode":"editorial-vector","viewpoint":"front",
            "outline":"2 px equivalent, round caps and joins","lighting":"flat scientific vector",
            "detail_level":"medium","palette":{"ink":INK,"surface":SURFACE,
                "primary":PRIMARY,"secondary":TEAL,"status_accent":ORANGE,"divider":DIVIDER}},
        "hero_asset_id":"asset-measurement-lenses",
        "contact_sheet":"contact-sheet.png","assets":records,
    }
    (root/"clip-art-manifest.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    (root/"usage-note.md").write_text(
        "# EthosGPT Figure 1 vector set\n\n"
        "These original SVG micro-scenes support the graphical abstract. "
        "All labels, connectors, evidence states, and numeric claims remain in the figure layer.\n",
        encoding="utf-8",
    )


def normalize_supplementary_svgs() -> None:
    titles = {
        "figS1_uncertainty_sources.svg": "Conditional uncertainty sources",
        "figS2_spatial_maps.svg": "Cross-sectional country-level changes",
        "figS3_economic_sensitivity.svg": "Full economic weight sensitivity",
    }
    for name, title in titles.items():
        for directory in (FIGURES, RESULT_FIGURES):
            path = directory / name
            if path.exists():
                postprocess_svg(path, title)


def main() -> None:
    set_style()
    figure1()
    figure2()
    figure3()
    normalize_supplementary_svgs()
    print("PASS: v0.7.0 visual story generated")


if __name__ == "__main__":
    main()
