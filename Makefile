PYTHON ?= python3
PIP ?= $(PYTHON) -m pip
ENV_FILE ?= .env
ENV_EXAMPLE ?= env.example

.PHONY: install dev lint type test format pre-commit env-validate env-sample

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PYTHON) scripts/install_pjsua2.py

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
