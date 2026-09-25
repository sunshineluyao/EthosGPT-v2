PYTHON ?= python
export PYTHONPATH := src
export SOURCE_DATE_EPOCH ?= 1788566400

.PHONY: setup analysis assets lint test negative-tests verify paper-workshop papers audit-paper audit-visual release-contract reproduce-offline

PAPER_DIR ?= paper
EXPERIMENT := experiments/gpt55_gpt56_64country

setup:
	$(PYTHON) -m pip install -r requirements.txt

analysis:
	$(PYTHON) $(EXPERIMENT)/score_wave1.py
	$(PYTHON) $(EXPERIMENT)/uncertainty_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/protocol_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/wording_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/six_region_sensitivity.py
	$(PYTHON) $(EXPERIMENT)/spatial_hac.py
	$(PYTHON) $(EXPERIMENT)/extended_analysis.py

assets:
	$(PYTHON) scripts/make_wave1_assets.py
	$(PYTHON) scripts/make_v070_assets.py
	$(PYTHON) scripts/make_visual_story_v100.py
	$(PYTHON) scripts/polish_submission_tables.py

lint:
	$(PYTHON) -m compileall -q src scripts experiments/gpt55_gpt56_64country tests

test:
	$(PYTHON) -m pytest -q tests

negative-tests:
	$(PYTHON) -m pytest -q tests/test_release_negative.py

verify:
	$(PYTHON) scripts/verify_results.py
	$(PYTHON) -m pytest -q tests

paper-workshop:
	cd $(PAPER_DIR) && latexmk -pdf -halt-on-error -interaction=nonstopmode main.tex

papers: paper-workshop

audit-paper:
	$(PYTHON) scripts/audit_submission.py --paper-dir $(PAPER_DIR)

audit-visual:
	$(PYTHON) scripts/audit_visual_assets.py

release-contract: lint verify papers audit-paper audit-visual negative-tests

reproduce-offline:
	$(PYTHON) scripts/reproduce_offline.py
