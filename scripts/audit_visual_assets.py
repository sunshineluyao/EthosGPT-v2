#!/usr/bin/env python3
"""Fail closed on stale, rasterized, undersized, or unmapped released figures."""

from __future__ import annotations

import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
FIGS = ROOT / "results/figures"
MANIFEST = ROOT / "assets/figure_sources/semantic_graphics_manifest.json"


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def audit_svg(path: Path) -> None:
    root = ET.parse(path).getroot()
    assert local(root.tag) == "svg"
    assert root.get("viewBox") and root.get("width") and root.get("height")
    ids: set[str] = set()
    titles = sum(1 for child in root if local(child.tag) == "title")
    live_text = 0
    for element in root.iter():
        kind = local(element.tag)
        if kind in {"text", "textPath"}:
            live_text += 1
        assert kind != "image", f"embedded or linked raster in {path.name}"
        assert "clip-path" not in element.attrib and "mask" not in element.attrib
        element_id = element.get("id")
        if element_id:
            assert element_id not in ids, f"duplicate SVG id {element_id} in {path.name}"
            ids.add(element_id)
        for value in element.attrib.values():
            if not isinstance(value, str):
                continue
            for size in re.findall(r"font-size\s*:\s*([0-9.]+)px", value):
                assert float(size) >= 7.0, f"{size}px text in {path.name}"
    assert titles == 1, f"expected one accessible title in {path.name}"
    assert live_text > 0, f"no live text in {path.name}"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert manifest["version"] == "1.0.0"
    records = manifest["figures"]
    stems = [record["stem"] for record in records]
    assert len(stems) == len(set(stems)) == 8
    assert manifest["format_contract"]["embedded_raster_images"] is False

    expected = {f"{stem}{suffix}" for stem in stems for suffix in (".pdf", ".svg")}
    actual_core = {path.name for path in FIGS.iterdir() if path.suffix in {".pdf", ".svg"}}
    assert actual_core == expected, f"stale or missing figure assets: {sorted(actual_core ^ expected)}"
    for stem in stems:
        assert (FIGS / f"{stem}.pdf").stat().st_size > 0
        audit_svg(FIGS / f"{stem}.svg")

    assert not (ROOT / "paper").exists(), "manuscript sources belong in the paper repository"
    assert (FIGS / "figS2_study_design.drawio").stat().st_size > 0
    assert (FIGS / "fig1_spatial_story.drawio").stat().st_size > 0
    ET.parse(FIGS / "fig1_spatial_story.drawio")
    print("PASS: eight manifest-mapped vector figures, two editable draw.io masters, live text >=7 px, no embedded raster or stale assets")


if __name__ == "__main__":
    main()
