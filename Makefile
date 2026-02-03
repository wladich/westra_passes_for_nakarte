define help
Available targets:
	help
	pylint
	black
	flake8
	mypy
	check - all static checks
  test_reference - create reference files for testing upgrades
  test - run pytest tests, perform testing against reference files
	venv - create or update venv for development
	clean - clean caches and run/test artifacts except reference files
	cleanall - like "clean" but also delete reference files
	run - create nakarte files from Westra API
	tree - request Westra API and store unprocessed data to file
	run_tree - create nakarte files from local file created with "tree"
endef
export help

TOOL_PREFIX=./.venv/bin/
ARTIFACTS=./test_artifacts
REFERENCE_ARTIFACTS=./test_artifacts_reference
VERIFICATION_ARTIFACTS=./test_artifacts_verification

ifneq (,$(wildcard ./.env))
    include .env
    export
endif

help:
	@echo "$$help"

pylint: venv
	$(TOOL_PREFIX)pylint . --recursive y

black: venv
	$(TOOL_PREFIX)black --diff --check -q .

flake8: venv
	$(TOOL_PREFIX)flake8 .

mypy: venv
	$(TOOL_PREFIX)mypy mountain_passes_for_nakarte

test_reference: venv
test_reference: ARTIFACTS_DIR=$(REFERENCE_ARTIFACTS)
test_reference: reference


test: ARTIFACTS_DIR=$(VERIFICATION_ARTIFACTS)
test: venv reference
	$(TOOL_PREFIX)pytest
	diff --recursive --brief $(REFERENCE_ARTIFACTS) $(VERIFICATION_ARTIFACTS)

check: mypy pylint flake8 black  # test
	@echo All checks passed.

.PHONY: venv
venv:
	uv sync

clean:
	rm -rf ./mypy_cache ./*.egg-info ./.mypy_cache ./__pycache__ ./.pytest_cache ./.venv ./build ./test_artifacts $(ARTIFACTS) $(VERIFICATION_ARTIFACTS)

cleanall: clean
	rm -rf $(REFERENCE_ARTIFACTS)

run: venv
	@if [ -z "$(API_KEY)" ]; then echo API_KEY is not set.; exit 1; fi
	mkdir -p "$(ARTIFACTS)"
	$(TOOL_PREFIX)westra_to_nakarte_json --api-key "$(API_KEY)" $(ARTIFACTS)/passes.json $(ARTIFACTS)/coverage.json $(ARTIFACTS)/regions.txt

tree: venv
	mkdir -p "$(ARTIFACTS)"
	$(TOOL_PREFIX)westra_tree_to_file_for_debugging --api-key "$(API_KEY)" $(ARTIFACTS)/tree.json

run_tree: venv
	$(TOOL_PREFIX)westra_to_nakarte_json --load-tree $(ARTIFACTS)/tree.json $(ARTIFACTS)/passes.json $(ARTIFACTS)/coverage.json $(ARTIFACTS)/regions.txt

reference:
	@if [ -z "$(API_KEY)" ]; then echo API_KEY is not set.; exit 1; fi
	@if [ -z "$(ARTIFACTS_DIR)" ]; then echo ARTIFACTS_DIR is not set.; exit 1; fi
	rm -rf "$(ARTIFACTS_DIR)"
	mkdir "$(ARTIFACTS_DIR)"
# Fetch tree
	$(TOOL_PREFIX)westra_tree_to_file_for_debugging --api-key "$(API_KEY)" $(ARTIFACTS_DIR)/tree.json
# Create files from local tree
	$(TOOL_PREFIX)westra_to_nakarte_json --load-tree $(ARTIFACTS_DIR)/tree.json $(ARTIFACTS_DIR)/passes_from_local.json $(ARTIFACTS_DIR)/coverage_from_local.json $(ARTIFACTS_DIR)/regions_from_local.txt
# Create files from remote tree
	$(TOOL_PREFIX)westra_to_nakarte_json --api-key "$(API_KEY)" $(ARTIFACTS_DIR)/passes_from_remote.json $(ARTIFACTS_DIR)/coverage_from_remote.json $(ARTIFACTS_DIR)/regions_from_remote.txt

	diff --brief $(ARTIFACTS_DIR)/passes_from_local.json $(ARTIFACTS_DIR)/passes_from_remote.json
	diff --brief $(ARTIFACTS_DIR)/coverage_from_local.json $(ARTIFACTS_DIR)/coverage_from_remote.json
	diff --brief $(ARTIFACTS_DIR)/regions_from_local.txt $(ARTIFACTS_DIR)/regions_from_remote.txt
# Create region labels
	$(TOOL_PREFIX)gpx_regions_to_geojson data/westra/westra_region_labels_1.gpx $(ARTIFACTS_DIR)/westra_labels_1.json
	$(TOOL_PREFIX)gpx_regions_to_geojson data/westra/westra_region_labels_2.gpx $(ARTIFACTS_DIR)/westra_labels_2.json
