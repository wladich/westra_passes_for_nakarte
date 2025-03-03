define help
Available targets:
	help
	pylint
	black
	flake8
	mypy
#	test
	check
	venv [path=PATH_TO_VENV]
		create venv for development
		default path=./venv
	clean

	common arguments:
		python=PYTHON3_EXECUTABLE, defaults to python3
endef
export help

path?=./venv
python?=python3

help:
	@echo "$$help"

pylint:
	pylint . --recursive y

black:
	black --diff --check -q .

flake8:
	flake8 .

mypy:
	mypy mountain_passes_for_nakarte

#test:
#	pytest

check: mypy pylint flake8 black  # test
	@echo All checks passed.

.PHONY: venv
venv:
	@echo Will install at $(path)
	$(python) -m venv $(path)
	SETUPTOOLS_ENABLE_FEATURES="legacy-editable" $(path)/bin/pip install -e ".[test]"

clean:
	rm -rf ./mypy_cache ./*.egg-info ./.mypy_cache ./__pycache__ ./.pytest_cache ./venv ./build