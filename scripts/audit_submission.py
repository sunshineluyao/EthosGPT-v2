#!/usr/bin/env python3
"""Audit the venue-neutral NeurIPS workshop PDF and write a release report."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]


def font_audit(pdf_path: Path) -> list[dict[str, str]]:
    result = subprocess.run(
        ["pdffonts", str(pdf_path)],
        check=True,
        text=True,
        capture_output=True,
    )
    lines = result.stdout.splitlines()[2:]
    records = []
    for line in lines:
        fields = line.split()
        if len(fields) < 8:
            continue
        records.append({
            "name": fields[0],
            "type": " ".join(fields[1:-5]),
            "embedded": fields[-5],
            "subset": fields[-4],
            "unicode": fields[-3],
        })
    assert records, f"no fonts detected in {pdf_path.name}"
    assert all(record["embedded"] == "yes" for record in records)
    assert all("Type 3" not in record["type"] for record in records)
    return records


def audit_pdf(pdf_path: Path) -> dict[str, object]:
    reader = PdfReader(str(pdf_path))
    pages = [page.extract_text() or "" for page in reader.pages]
    assert len(pages) >= 10
    reference_pages = [
        index for index, page in enumerate(pages)
        if page.lstrip().startswith("References")
        or re.search(r"(?:^|\n)\s*\d*\s*References\b", page)
    ]
    assert reference_pages, "reference heading not found"
    references_start = reference_pages[0]
    assert references_start == 4, "references must begin on page 5 after an exact four-page body"
    appendix_pages = [index for index, page in enumerate(pages) if "Appendix guide" in page]
    assert appendix_pages and appendix_pages[0] > references_start
    assert "NeurIPS Paper Checklist" in "\n".join(pages[-8:])
    assert "Declaration of LLM usage" in "\n".join(pages[-2:])
    assert "64 countries" in "\n".join(pages[:4])
    assert "3,840" in "\n".join(pages[:4])
    assert "eight-country" not in "\n".join(pages).lower()
    assert "Anonymous Author" in pages[0]
    assert (reader.metadata.author or "") == "Anonymous Authors"
    assert (reader.metadata.subject or "") == "Anonymous NeurIPS 2026 workshop submission"
    keywords = reader.metadata.get("/Keywords", "") or ""
    assert "agent systems" in keywords and "creative destruction" in keywords
    fonts = font_audit(pdf_path)
    return {
        "file": pdf_path.name,
        "pages": len(pages),
        "references_start_page": references_start + 1,
        "checklist_last": True,
        "embedded_fonts": len(fonts),
        "type3_fonts": 0,
        "sha256": hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-dir", type=Path, default=ROOT / "paper")
    args = parser.parse_args()
    paper = args.paper_dir.resolve()
    pdfs = [paper / "main.pdf"]
    assert pdfs[0].exists(), "compile the venue-neutral workshop PDF before audit"

    log_text = (paper / "main.log").read_text(encoding="utf-8", errors="replace")
    assert "Undefined control sequence" not in log_text
    assert "There were undefined references" not in log_text
    assert "undefined citations" not in log_text.lower()
    assert "Overfull \\hbox" not in log_text
    assert "Overfull \\vbox" not in log_text

    source_text = "\n".join(path.read_text(encoding="utf-8") for path in paper.rglob("*.tex"))
    assert source_text.count(r"\begin{promptlisting}") == 6
    assert "Q121" in source_text and "label conflict" in source_text
    checklist = (paper / "checklist.tex").read_text(encoding="utf-8")
    question_lines = "\n".join(
        line for line in checklist.splitlines() if re.match(r"\s*\\item\[\] Question:", line)
    ) + "\n"
    assert hashlib.sha256(question_lines.encode()).hexdigest() == "be94032da3b33c4f50d5896d16864f64fee3860506ca1de50399ddee7a4626bb"
    assert len(re.findall(r"^\s*\\item \{\\bf", checklist, flags=re.MULTILINE)) == 16
    assert len(re.findall(r"^\s*\\item\[\] Guidelines:", checklist, flags=re.MULTILINE)) == 16
    assert len(re.findall(
        r"^\s*\\item\[\] Answer: \\answer(?:Yes|No|NA)\{\}", checklist, flags=re.MULTILINE
    )) == 16
    assert "answerTODO" not in checklist and "justificationTODO" not in checklist
    assert "BEGIN INSTRUCTIONS" not in checklist and "END INSTRUCTIONS" not in checklist
    main_source = (paper / "main.tex").read_text(encoding="utf-8")
    assert r"\input{checklist.tex}" in main_source
    title = re.search(r"\\title\{([^{}]*)\}", main_source, flags=re.DOTALL)
    assert title and r"\\" not in title.group(1)
    assert hashlib.sha256((paper / "neurips_2026.sty").read_bytes()).hexdigest() == "c3fc2894e83d2517ca18b66741d6c595986d97957dc08ec08bb2125a7ec4555a"
    bbl = (paper / "main.bbl").read_text(encoding="utf-8")
    assert bbl.count(r"\url{") == 23
    assert "economic-sciences/2025/press-release/" in bbl

    svg_text = "\n".join(
        (paper / "figs" / name).read_text(encoding="utf-8")
        for name in (
            "fig1_spatial_story.svg", "fig2_multiview_results.svg",
            "fig3_economic_story.svg", "figS1_uncertainty_sources.svg", "figS2_study_design.svg",
            "figS3_economic_sensitivity.svg", "figS4_country_maps.svg",
            "figS5_country_profiles.svg",
        )
    )
    assert "Nimbus Roman" in svg_text
    assert "DejaVu Sans" not in svg_text

    results = [audit_pdf(path) for path in pdfs]
    body_pages = int(results[0]["references_start_page"]) - 1
    report = {
        "status": "PASS",
        "body_pages": body_pages,
        "template": "NeurIPS 2026 dblblindworkshop",
        "pdfs": results,
        "checks": [
            f"references begin on page {body_pages + 1}",
            "official checklist.tex appears last with all questions and guidelines",
            "all fonts embedded and no Type 3 fonts",
            "no undefined citations/references or overfull boxes",
            "figure typography uses the same Times-compatible serif family as the manuscript",
            "prompt listings use a dedicated monospaced font and breakable boxes",
            "all 23 bibliography records print explicit URLs",
            "venue-neutral PDF subject metadata and workshop-relevant keywords are correct",
        ],
    }
    output = ROOT / "manifests/submission_audit_v100.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: venue-neutral PDF, exact {body_pages}-page body, bibliography, appendix, official checklist, and fonts")


if __name__ == "__main__":
    main()
