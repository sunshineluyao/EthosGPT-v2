# Structural figure revision

The revised figures use the original empirical palette: navy `#18324A`,
teal `#007F86`, blue `#4057D6`, rose `#B93678`, and muted gray `#728091`.
Serif text, redundant line styles, numeric keys, open start markers, and star
endpoints keep the views legible without relying on color alone.

Run `make structural-figures` from the repository root. This redraws twelve
structural views and the integrated hero from the frozen data. CairoSVG and
the system font requirements are documented in REPRODUCIBILITY.md.

| View | Source | Reader conclusion |
|---|---|---|
| Integrated hero, panels A-D | `assets/figure_sources/retained/fig1_ethos_gallery.svg` | Retained observed coverage, regional contrasts, signed gaps, and measurement-weight sensitivity. |
| Hero E and patent-valuation sheet | `country_revision_results/systems/market-valuation-sheet.csv` | Initial needs modestly shift normalized patent value; the 0.81% range and truncated vertical axis are disclosed. |
| Hero F, action fields, and system summary | `country_revision_results/systems/planner-phase-field.csv`; `country-paths.csv` | Research and assistance depend on needs; stationary needs can accompany continuing quality growth. |
| Adviser difference and retained absolute paths | `country_revision_results/country-paths.csv` | Close levels have small but explicit signed differences relative to the human-rule reference. |
| Initial states and phase/growth view | `country_revision_results/country-paths.csv` | Six tested starts approach the same tested endpoint within each policy; this does not prove global uniqueness. |
| Research and assistance controls | `country_revision_results/country-paths.csv` | A state-dependent planner and fixed-advice markets implement different decision rules. |
| Welfare weight and innovation size | `country_revision_results/matched-sensitivity.csv` | Reoptimized outcomes depend on the declared normative penalty and economic quality jump. |
| Refinement | `country_revision_results/country-refinement.csv` | Discrete value consistency does not certify every path statistic, particularly Egypt's small gain. |
| Upgrade contrasts | `country_revision_results/three-country-upgrade-comparison.csv` | Outcome direction and distance from human advice are distinct. |

Structural source paths in this table are relative to `experiments/ah_growth/`.
The SVGs retain live text and the PDFs remain vectors. No profile, economic
parameter, value array, scenario coordinate, or statistical estimate changes
in this visual revision. Country labels describe conditional resource inputs;
the outputs are not observed national effects or forecasts.
