PYTHON ?= python
export PYTHONPATH := src
export SOURCE_DATE_EPOCH ?= 1788566400

.PHONY: setup analysis assets lint test negative-tests verify audit-visual release-contract reproduce-offline

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

lint:
	$(PYTHON) -m compileall -q src scripts experiments/gpt55_gpt56_64country tests

test:
	$(PYTHON) -m pytest -q tests

negative-tests:
	$(PYTHON) -m pytest -q tests/test_release_negative.py

verify:
	$(PYTHON) scripts/verify_results.py
	$(PYTHON) -m pytest -q tests

audit-visual:
	$(PYTHON) scripts/audit_visual_assets.py

release-contract: lint verify audit-visual negative-tests

reproduce-offline:
	$(PYTHON) scripts/reproduce_offline.py
