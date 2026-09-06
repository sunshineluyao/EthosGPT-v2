# Release gate — v1.0.0

## Status

Pass.

- End-to-end offline reconstruction from 3,840 versioned outputs: pass.
- Input hashes: GPT-5.5 `cb35dea8…ce729`; GPT-5.6 Sol `3c94ddeb…d6a28`: pass.
- Prompt-set hash and complete 64-country pairing: pass.
- Unit suite: 16 passed.
- Negative release tests: 3 passed.
- Static Overleaf source audit: pass.
- Source-mapped visual audit: seven vector figures and two parseable Draw.io masters: pass.
- Semantic figure-manifest audit: pass.
- SVG structure: accessible titles, live text, unique IDs, no embedded raster, and no explicit type below 7 pt: pass.
- Standalone PDF text geometry: zero text-to-text overlaps across all seven figures: pass.
- LaTeX build: 32 pages; no undefined references/citations and no overfull boxes: pass.
- Page gate: exact four-page body; references begin on page 5: pass.
- Font audit: all 36 detected font records embedded; no Type 3 fonts: pass.
- Official 16-question checklist preserved and last: pass.
- Final PDF SHA-256: `931496967b0a9bbf90cfa3dbe727e2ae770e588348b9e4e66608cf24197afdb5`.

The LaTeX log contains non-failing underfull-box notices in sparse appendix and
checklist areas. Full-page and stand-alone renders were inspected; they produce
no clipping, overflow, or hidden content. The spatial stack also emits its known
bounded-optimizer and near-constant-input diagnostics; all numerical assertions
and robustness contracts pass.
