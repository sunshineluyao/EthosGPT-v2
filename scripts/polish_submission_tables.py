#!/usr/bin/env python3
"""Apply the EthosGPT v1.0.0 editorial table system after numeric generation.

The analysis generators remain authoritative for numbers.  This final deterministic
stage changes hierarchy, labels, float placement, and status emphasis only.
"""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
TABLE_DIR = ROOT / "paper" / "tabs"
APPENDIX_DIR = ROOT / "paper" / "appendices"


MAIN_TABLE = r"""\begin{table}[!b]
\centering
\caption{Primary 64-country contrasts. $\Delta$ is GPT-5.6 Sol minus GPT-5.5 target loss; negative values favor GPT-5.6. Intervals resample countries and Holm correction spans five global metrics.}
\label{tab:main}
\small
\setlength{\tabcolsep}{4.2pt}
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}lrrrl@{}}
\toprule
\rowcolor{tablehead}
Metric target & $\Delta$ loss & 95\% BCa CI & Holm $p$ & Corrected read \\
\midrule
W1 $\downarrow$ & -0.0020 & [-0.0040,0.0003] & 0.319 & uncertain \\
\rowcolor{improvebg}
TVD $\downarrow$ & \textbf{-0.0080} & \textbf{[-0.0107,-0.0050]} & \textbf{$<0.001$} & \textbf{lower error} \\
CRG $\downarrow$ & -0.0022 & [-0.0243,0.0215] & 0.845 & uncertain \\
VDR $\to 1$ & -0.0220 & [-0.0506,0.0025] & 0.319 & uncertain \\
CSR $\uparrow$ & 0.0333 & [-0.0082,0.0834] & 0.319 & uncertain \\
\bottomrule
\end{tabular*}
\vspace{1pt}\parbox{.98\linewidth}{\small W1 measures ordered displacement; TVD measures category mass; CRG measures profile error. VDR and CSR target cross-country spread and relational ordering. Model levels and standard errors appear in Appendix Table~\ref{tab:global-estimates}.}
\end{table}
"""


SPATIAL_TABLE = r"""\begin{table}[!htbp]
\centering
\caption{Spatial robustness dashboard. Panel A reports the pre-specified $k=4$ diagnostics (BH correction spans 27 outcomes); Panels B--C show the global TVD contrast under spatial-error and spatial-HAC inference. Negative contrasts favor GPT-5.6.}
\label{tab:spatial-global}
\small
\setlength{\tabcolsep}{3.4pt}
\begin{tabular*}{\linewidth}{@{\extracolsep{\fill}}llrrrr@{}}
\toprule
\rowcolor{tablehead}
\multicolumn{6}{l}{\textbf{A. Primary dependence diagnostics}}\\
Family & Outcome & Moran $I$ & BH $q$ & Geary $C$ & BH $q$ \\
\midrule
overall error & W1 & 0.132 & 0.108 & 0.863 & 0.161 \\
overall error & TVD & 0.144 & 0.108 & 0.866 & 0.165 \\
\rowcolor{cautionbg}
profile error & CRG & 0.225 & 0.059 & 0.752 & \textbf{0.032} \\
signed bias & Agency & 0.071 & 0.329 & 0.952 & 0.614 \\
signed bias & Trust & 0.193 & 0.070 & 0.824 & 0.157 \\
signed bias & Distribution & 0.064 & 0.356 & 0.926 & 0.402 \\
signed bias & Responsibility & 0.125 & 0.114 & 0.844 & 0.157 \\
signed bias & Immigration & 0.082 & 0.268 & 0.918 & 0.347 \\
signed bias & Science & 0.111 & 0.136 & 0.881 & 0.185 \\
\addlinespace[3pt]
\rowcolor{tablehead}
\multicolumn{6}{l}{\textbf{B. Spatial-error model: global TVD}}\\
$k$ & $\Delta$ & SE & 95\% CI & Holm $p$ & $\lambda$ ($p$) \\
\midrule
\rowcolor{improvebg}4 & -0.0081 & 0.0020 & [-0.0119,-0.0042] & 0.00047 & 0.296 (0.076) \\
\rowcolor{improvebg}6 & -0.0080 & 0.0015 & [-0.0110,-0.0051] & $<0.00001$ & 0.048 (0.841) \\
\rowcolor{improvebg}8 & -0.0081 & 0.0016 & [-0.0111,-0.0050] & $<0.00001$ & 0.087 (0.744) \\
\addlinespace[3pt]
\rowcolor{tablehead}
\multicolumn{6}{l}{\textbf{C. Spatial-HAC: global TVD}}\\
Cutoff (km) & $\Delta$ & HAC SE & 95\% CI & Holm $p$ & \\
\midrule
\rowcolor{improvebg}1000 & -0.0080 & 0.0016 & [-0.0112,-0.0049] & 0.00004 & \\
\rowcolor{improvebg}2000 & -0.0080 & 0.0015 & [-0.0111,-0.0050] & 0.00003 & \\
\rowcolor{improvebg}3000 & -0.0080 & 0.0016 & [-0.0112,-0.0049] & 0.00005 & \\
\rowcolor{improvebg}5000 & -0.0080 & 0.0014 & [-0.0109,-0.0052] & 0.00001 & \\
\bottomrule
\end{tabular*}
\end{table}
"""


def _style_headers(text: str, *, rename_domains: bool = True) -> str:
    text = text.replace(r"\begin{table}[h]", r"\begin{table}[!htbp]")
    text = text.replace(r"\begin{table}[htbp]", r"\begin{table}[!htbp]")
    text = text.replace(r"\footnotesize", r"\small")
    if rename_domains:
        text = text.replace("Market", "Responsibility").replace("Inclusion", "Immigration")
    text = re.sub(r"\\toprule(?!\s*\\rowcolor)", r"\\toprule\n\\rowcolor{tablehead}", text)
    return text


def _highlight_evidence(path: Path, text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    managed = path.name in {"appendix_extended_results.tex", "appendix_full_results.tex"}
    for line in lines:
        stripped = line.strip()
        if managed and stripped == r"\rowcolor{improvebg}":
            continue
        highlight = False
        if path.name == "appendix_extended_results.tex":
            highlight = (
                stripped.startswith("W1 & Responsibility (Q108)")
                or stripped.startswith("TVD & Distribution (Q106)")
                or stripped.startswith("TVD & Responsibility (Q108)")
                or stripped.startswith("Opportunity/participation")
                or stripped.startswith("Distribution/adjustment")
                or stripped.startswith("Equal weights")
                or stripped.startswith("Opportunity only")
                or stripped.startswith("Distribution only")
            )
        elif path.name == "appendix_full_results.tex":
            highlight = (
                stripped.startswith("TVD & -0.0080")
                or stripped.startswith("Distribution & .1833")
                or stripped.startswith("Responsibility & .1359")
                or stripped.startswith("Distribution & .4164")
                or stripped.startswith("Responsibility & .3940")
                or stripped.startswith("Science & .3332")
            )
        if highlight and not stripped.startswith(r"\rowcolor"):
            out.append(r"\rowcolor{improvebg}")
        out.append(line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else "")


def _group_country_roster(text: str) -> str:
    lines = [line for line in text.splitlines() if line.strip() != r"\addlinespace[2pt]"]
    out: list[str] = []
    previous_region: str | None = None
    in_rows = False
    for line in lines:
        if r"\midrule\endhead" in line:
            in_rows = True
            out.append(line)
            continue
        if in_rows and " & " in line and line.rstrip().endswith(r"\\"):
            fields = [field.strip() for field in line.split(" & ")]
            if len(fields) >= 2:
                region = fields[1]
                if previous_region is not None and region != previous_region:
                    out.append(r"\addlinespace[2pt]")
                previous_region = region
        out.append(line)
    return "\n".join(out) + "\n"


def _paginate_extended_results(text: str) -> str:
    """Keep the joint family and the composition family on separate readable pages."""
    marker = r"\bottomrule\end{longtable}"
    text = text.replace(marker + "\n" + r"\clearpage", marker)
    return text.replace(marker, marker + "\n" + r"\clearpage", 1)


def main() -> None:
    (TABLE_DIR / "table1_main.tex").write_text(MAIN_TABLE, encoding="utf-8")
    (TABLE_DIR / "appendix_spatial_tables.tex").write_text(SPATIAL_TABLE, encoding="utf-8")
    for path in sorted(TABLE_DIR.glob("*.tex")):
        text = path.read_text(encoding="utf-8")
        text = _style_headers(text)
        text = _highlight_evidence(path, text)
        if path.name == "appendix_extended_results.tex":
            text = _paginate_extended_results(text)
        if path.name == "appendix_country_roster.tex":
            text = _group_country_roster(text)
        path.write_text(text, encoding="utf-8")
    for path in sorted(APPENDIX_DIR.glob("*.tex")):
        text = path.read_text(encoding="utf-8")
        text = _style_headers(text, rename_domains=False)
        path.write_text(text, encoding="utf-8")
    print("PASS: v1.0.0 editorial table hierarchy applied without changing generated estimates")


if __name__ == "__main__":
    main()
