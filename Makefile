PYTHON ?= python3
PIP ?= $(PYTHON) -m pip

.PHONY: dev lint type test format pre-commit

dev:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements-dev.txt
	pre-commit install

lint:
	ruff check .

type:
	mypy --config-file mypy.ini app

test:
	pytest -q

format:
	ruff format .

pre-commit:
	pre-commit run --all-files
