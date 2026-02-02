define help
Available targets:
	help
	pylint
	black
	flake8
	mypy
#	test
	check
	venv
		create or update venv for development
	clean

	common arguments:
    path: virtualenv path, default ./venv
endef
export help

path?="./.venv"
TOOL_PREFIX=$(path)/bin/

help:
	@echo "$$help"

pylint:
	$(TOOL_PREFIX)pylint . --recursive y

black:
	$(TOOL_PREFIX)black --diff --check -q .

flake8:
	$(TOOL_PREFIX)flake8 .

mypy:
	$(TOOL_PREFIX)mypy mountain_passes_for_nakarte

#test:
#	pytest

check: mypy pylint flake8 black  # test
	@echo All checks passed.

.PHONY: venv
venv:
	UV_PROJECT_ENVIRONMENT="$(path)" uv sync

clean:
	rm -rf ./mypy_cache ./*.egg-info ./.mypy_cache ./__pycache__ ./.pytest_cache ./.venv ./build