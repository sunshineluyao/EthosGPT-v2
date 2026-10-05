PYTHON ?= python
export PYTHONPATH := src
export SOURCE_DATE_EPOCH ?= 1788566400

.PHONY: setup analysis assets signed-directions creative-destruction featured-figures release-smoke lint test negative-tests verify audit-visual release-contract reproduce-offline mechanisms reproduce-dynamics dynamic-figures

EXPERIMENT := experiments/gpt55_gpt56_64country

setup:
	$(PYTHON) -m pip install -r requirements.txt

analysis:
	$(PYTHON) $(EXPERIMENT)/score_wave1.py
	$(PYTHON) $(EXPERIMENT)/uncertainty_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/protocol_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/wording_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/eight_region_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/spatial_hac.py
	$(PYTHON) $(EXPERIMENT)/extended_analysis.py

assets:
	$(PYTHON) scripts/make_wave1_assets.py
	$(PYTHON) scripts/make_v070_assets.py
	$(PYTHON) scripts/make_visual_story_v100.py
	$(PYTHON) $(EXPERIMENT)/plot_eight_regions.py
	$(MAKE) signed-directions
	$(MAKE) creative-destruction
	$(MAKE) featured-figures

signed-directions:
	$(PYTHON) $(EXPERIMENT)/signed_directions.py --scores $(EXPERIMENT)/results/country_question_scores.csv --region-metrics $(EXPERIMENT)/results/eight_region_sensitivity.csv --output-dir results/signed_directions

creative-destruction:
	$(PYTHON) $(EXPERIMENT)/simulate_creative_destruction.py --scores $(EXPERIMENT)/results/country_question_scores.csv --output-dir results/creative_destruction

featured-figures:
	$(PYTHON) assets/figure_sources/make_fig1_ethos_gallery.py
	$(PYTHON) assets/figure_sources/make_fig2_value_bridge.py

release-smoke:
	$(PYTHON) scripts/release_smoke.py
	$(PYTHON) scripts/reproduce_dynamics.py --check

lint:
	$(PYTHON) -m compileall -q src scripts experiments/gpt55_gpt56_64country experiments/dynamic_growth experiments/ah_growth tests

test:
	$(PYTHON) -m pytest -q tests

negative-tests:
	$(PYTHON) -m pytest -q tests/test_release_negative.py

verify:
	$(PYTHON) scripts/verify_results.py
	$(PYTHON) -m pytest -q tests

audit-visual:
	$(PYTHON) scripts/audit_visual_assets.py

release-contract: lint release-smoke verify audit-visual negative-tests mechanisms structural-check

reproduce-offline:
	$(PYTHON) scripts/reproduce_offline.py

mechanisms:
	cd experiments/dynamic_growth && $(PYTHON) -m unittest test_dynamics -v

reproduce-dynamics:
	$(PYTHON) scripts/reproduce_dynamics.py

dynamic-figures:
	$(PYTHON) scripts/reproduce_dynamics.py --figures-only

.PHONY: structural-check reproduce-structural structural-figures
structural-check:
	$(PYTHON) experiments/ah_growth/verify_results.py
reproduce-structural:
	$(PYTHON) experiments/ah_growth/reproduce.py --refresh-metrics
structural-figures:
	$(PYTHON) experiments/ah_growth/publication_figures.py
	$(PYTHON) scripts/make_structural_hero.py

.PHONY: structural-full
structural-full:
	python experiments/ah_growth/reproduce_structural.py --full --output .build/full-structural
