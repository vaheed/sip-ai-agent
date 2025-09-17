PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
ENV_FILE ?= .env
ENV_EXAMPLE ?= env.example

.PHONY: dev lint type test format pre-commit env-validate env-sample

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

env-validate:
	$(PYTHON) -m app.config validate --path $(ENV_FILE)

env-sample:
	$(PYTHON) -m app.config sample --write --path $(ENV_EXAMPLE)
