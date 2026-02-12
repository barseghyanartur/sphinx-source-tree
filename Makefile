# Update version ONLY here
VERSION := 0.1.2
SHELL := /bin/bash
# Makefile for project
VENV := .venv/bin/activate
UNAME_S := $(shell uname -s)

# Build documentation using Sphinx and zip it
build-docs:
	source $(VENV) && python scripts/generate_project_source_tree.py
	source $(VENV) && sphinx-build -n -b text docs builddocs
	source $(VENV) && sphinx-build -n -a -b html docs builddocs
	cd builddocs && zip -r ../builddocs.zip . -x ".*" && cd ..

rebuild-docs:
	source $(VENV) && sphinx-apidoc . --full -o docs -H 'sphinx-llms-txt-link' -A 'Artur Barseghyan <artur.barseghyan@gmail.com>' -f -d 20
	cp docs/index.rst.distrib docs/index.rst
	cp docs/conf.py.distrib docs/conf.py

pre-commit:
	pre-commit run --all-files

doc8:
	source $(VENV) && doc8

# Run ruff on the codebase
ruff:
	source $(VENV) && ruff check . --fix
	source $(VENV) && ruff format .

# Serve the built docs on port 5001
serve-docs:
	source $(VENV) && python -m http.server 5001 --directory builddocs/

venv:
	uv sync

# Install the project
install:
	source $(VENV) && uv pip install -e .'[all]'

test: clean
	source $(VENV) && pytest -vrx -s

shell:
	source $(VENV) && ipython

create-secrets:
	source $(VENV) && detect-secrets scan > .secrets.baseline

detect-secrets:
	source $(VENV) && detect-secrets scan --baseline .secrets.baseline

# Clean up generated files
clean:
	find . -type f -name "*.pyc" -exec rm -f {} \;
	find . -type f -name "builddocs.zip" -exec rm -f {} \;
	find . -type f -name "*.py,cover" -exec rm -f {} \;
	find . -type f -name "*.orig" -exec rm -f {} \;
	find . -type d -name "__pycache__" -exec rm -rf {} \; -prune
	rm -rf sphinx_llms_txt_link.egg-info/
	rm -rf build/
	rm -rf dist/
	rm -rf .cache/
	rm -rf htmlcov/
	rm -rf builddocs/
	rm -rf testdocs/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/

compile-requirements:
	source $(VENV) && uv pip compile --all-extras -o docs/requirements.txt pyproject.toml

compile-requirements-upgrade:
	source $(VENV) && uv pip compile --all-extras -o docs/requirements.txt pyproject.toml --upgrade

update-version:
	@if [ "$(UNAME_S)" = "Darwin" ]; then \
		gsed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		gsed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' sphinx_source_tree.py; \
	else \
		sed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		sed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' sphinx_source_tree.py; \
	fi

build:
	source $(VENV) && python -m build .

check-build:
	source $(VENV) && twine check dist/*

release:
	source $(VENV) && twine upload dist/* --verbose

test-release:
	source $(VENV) && twine upload --repository testpypi dist/*

mypy:
	source $(VENV) && mypy sphinx_source_tree.py

%:
	@:
