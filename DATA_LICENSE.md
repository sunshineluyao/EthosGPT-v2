# Data and redistribution audit

| Asset | Source | Redistribution decision |
|---|---|---|
| Official WVS7 questionnaire | World Values Survey Association | Cited and used to audit exact wording; users should follow official terms |
| Joint EVS/WVS v5.0 microdata | WVSA/GESIS, DOI 10.4232/1.14320 and 10.14281/18241.26 | Not accessed or bundled |
| Oxford WVS 2017–2022 SFT derivative | Pinned Hugging Face derivative | Raw respondent narratives excluded; only minimal aggregate country–item distributions included |
| WorldValuesBench outputs | Pinned upstream repository | Retained only as non-pooled historical context; full upstream files excluded |
| GPT-5.5/GPT-5.6 Sol outputs | Authors' paid API collection | Validated probability records, prompts, and provenance released without credentials |
| Natural Earth basemap | Natural Earth public-domain data | Country geometry used for the result map |
| Project code and original vector assets | This release | MIT License |

The public derivative's license label does not independently resolve rights in
all upstream survey content. The release therefore excludes raw narratives and
official microdata, and includes only the minimum aggregate evidence needed to
verify the paper. No API key or identifiable respondent data is present.
