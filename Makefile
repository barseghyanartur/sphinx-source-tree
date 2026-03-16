# Update version ONLY here
VERSION := 0.2.5
SHELL := /bin/bash
# Makefile for project
VENV := .venv/bin/activate
UNAME_S := $(shell uname -s)

# Build documentation using Sphinx and zip it
build-docs:
	uv run sphinx-source-tree
	uv run sphinx-build -n -b text docs builddocs
	uv run sphinx-build -n -a -b html docs builddocs
	cd builddocs && zip -r ../builddocs.zip . -x ".*" && cd ..

rebuild-docs:
	uv run sphinx-apidoc . --full -o docs -H 'sphinx-llms-txt-link' -A 'Artur Barseghyan <artur.barseghyan@gmail.com>' -f -d 20
	cp docs/index.rst.distrib docs/index.rst
	cp docs/conf.py.distrib docs/conf.py

auto-build-docs:
	uv run sphinx-autobuild docs docs/_build/html --port 5001

source-tree:
	uv run sphinx-source-tree

pre-commit:
	pre-commit run --all-files

doc8:
	uv run doc8

# Run ruff on the codebase
ruff:
	uv run ruff check . --fix
	uv run ruff format .

# Serve the built docs on port 5001
serve-docs:
	uv run python -m http.server 5001 --directory builddocs/

create-venv:
	uv sync

# Install the project
install:
	uv sync --all-extras

test: clean
	uv run pytest -vrx -s

shell:
	uv run ipython

create-secrets:
	uv run detect-secrets scan > .secrets.baseline

detect-secrets:
	uv run detect-secrets scan --baseline .secrets.baseline

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
	uv run pip compile --all-extras -o docs/requirements.txt pyproject.toml

compile-requirements-upgrade:
	uv run pip compile --all-extras -o docs/requirements.txt pyproject.toml --upgrade

update-version:
	@if [ "$(UNAME_S)" = "Darwin" ]; then \
		gsed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		gsed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' sphinx_source_tree.py; \
	else \
		sed -i 's/version = "[0-9.]\+"/version = "$(VERSION)"/' pyproject.toml; \
		sed -i 's/__version__ = "[0-9.]\+"/__version__ = "$(VERSION)"/' sphinx_source_tree.py; \
	fi

build:
	uv run python -m build .

check-build:
	uv run twine check dist/*

release:
	uv run twine upload dist/* --verbose

test-release:
	uv run twine upload --repository testpypi dist/*

mypy:
	uv run mypy sphinx_source_tree.py

%:
	@:
