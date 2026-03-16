# AGENTS.md — sphinx-source-tree

**Package version**: See `pyproject.toml`
**Repository**: https://github.com/barseghyanartur/sphinx-source-tree
**Maintainer**: Artur Barseghyan <artur.barseghyan@gmail.com>

This file is for AI agents and developers using AI assistants to work on or
with sphinx-source-tree. It covers two distinct roles: **using** the package
in documentation pipelines, and **developing/extending** the package itself.

---

## 1. Project Mission (Never Deviate)

> Generate a reStructuredText file containing an ASCII project tree and
> `literalinclude` directives for every source file — specifically for
> `llms.txt`, providing full project context for LLMs.

- The tool is read-only with respect to the project it documents.
- Zero required dependencies for Python 3.11+; only `tomli` for 3.10.
- The three-layer config merge (`DEFAULTS` < `pyproject.toml` < CLI) is
  preserved for every option.
- Output is always a valid `.rst` document that Sphinx can build without
  modification.

---

## 2. Using sphinx-source-tree in Documentation Pipelines

### Quick start

```sh
# Install
uv pip install sphinx-source-tree

# Run in project root — writes docs/source_tree.rst
sphinx-source-tree

# Print to stdout instead
sphinx-source-tree --stdout
```

### Python API

```python
from pathlib import Path
from sphinx_source_tree import generate

rst = generate(
    project_root=Path("."),
    output=Path("docs/source_tree.rst"),
    depth=5,
    extensions=[".py", ".rst"],
    ignore=["__pycache__", "*.pyc"],
    title="My project source",
)
Path("docs/source_tree.rst").write_text(rst)
```

`generate()` returns the RST string and **never writes to disk**, so you can
post-process or redirect as needed.

### Lower-level helpers (importable directly)

| Symbol | Purpose |
|---|---|
| `build_tree()` | ASCII tree string |
| `collect_files()` | Sorted list of `Path` objects to include |
| `detect_language()` | Suffix → Sphinx highlight-language mapping |
| `load_config()` | Read `[tool.sphinx-source-tree]` from `pyproject.toml` |
| `resolve_config()` | Merge defaults / pyproject / CLI into one dict |

### Configuration via `pyproject.toml`

```toml
[tool.sphinx-source-tree]
depth = 4
output = "docs/source_tree.rst"
extensions = [".py", ".rst", ".toml"]
ignore = ["__pycache__", "*.pyc", ".git", "*.egg-info"]
whitelist = ["src", "docs"]
include-all = false
title = "Source listing"
linenos = true
order = ["README.rst", "pyproject.toml"]

[tool.sphinx-source-tree.file-options]
"src/app.py" = {"end-before" = "# *** Tests ***"}
```

Multiple output files are supported via `[[tool.sphinx-source-tree.files]]`
entries. Top-level keys act as shared defaults; each entry can override any
of them. See README for full reference.

---

## 3. Architecture

### Key files

| File | Purpose |
|---|---|
| `sphinx_source_tree.py` | Entire implementation — single-module package |
| `test_sphinx_source_tree.py` | Full test suite |
| `conftest.py` | `safe_test_path` fixture for documentation code blocks |
| `pyproject.toml` | Build, ruff, mypy, pytest, tool config |
| `docs/` | Sphinx documentation source |

### Public API surface (`__all__`)

```
build_parser   build_tree     collect_files   detect_language
generate       load_config    main            resolve_config
```

### Config resolution order

```
DEFAULTS  <  [tool.sphinx-source-tree]  <  [[…files]] entry  <  CLI args
```

`resolve_config()` implements this merge and returns a single flat dict (or
a dict with a `"files"` key for multi-file mode). `_generate_from_cfg()`
calls `generate()` using that dict. `main()` orchestrates the CLI.

### Per-file inclusion options

`VALID_FILE_OPTIONS` (a `frozenset`) lists the only option keys accepted in
`file_options` dicts: `lines`, `start-at`, `start-after`, `end-before`,
`end-at`. Unknown keys are warned and dropped. Key normalisation
(underscore ↔ hyphen) is handled by `_validate_file_options()`.

---

## 4. Coding Conventions

### Formatting

- Line length: **80 characters** (ruff).
- Import sorting: `isort`. Run `make pre-commit` to verify.
- Target: `py39` (ruff), `Python 3.10+` (runtime).

### Ruff rules in effect

`B`, `C4`, `E`, `F`, `G`, `I`, `ISC`, `INP`, `N`, `PERF`, `Q`, `SIM`, `TD`.

Explicitly ignored:

| Rule | Reason |
|---|---|
| `G004` | f-strings in logging calls are allowed |
| `ISC003` | explicitly concatenated strings allowed |
| `TD002` | TODO without author allowed |
| `TD003` | TODO without URL allowed |

### Style

- The module is intentionally a **single file** (`sphinx_source_tree.py`).
  Do not split it into a package without a very strong reason.
- Every public function must have a docstring with Sphinx-style type
  annotations.
- Module-level dunder metadata (`__title__`, `__version__`, `__author__`,
  `__copyright__`, `__license__`, `__all__`) must be kept up to date.
- Use `sys.stderr` for all warnings (`print(..., file=sys.stderr)`).
- `generate()` must never write to disk — return the RST string only.
  Callers that need to write call `_write_output()` or `Path.write_text()`.

### RST heading hierarchy (for documentation)

```
=====
title
=====

header
======

sub-header
----------

sub-sub-header
~~~~~~~~~~~~~~

sub-sub-sub-header
^^^^^^^^^^^^^^^^^^

sub-sub-sub-sub-header
++++++++++++++++++++++

sub-sub-sub-sub-sub-header
**************************
```

---

## 5. Agent Workflow: Adding Features or Fixing Bugs

When asked to add a feature or fix a bug, follow these steps in order:

1. **Identify the affected function(s)** — most changes belong in one of:
   `build_tree`, `collect_files`, `generate`, `resolve_config`,
   `_apply_order`, `_validate_file_options`, `_resolve_file_options_profile`,
   or `_is_ignored`.
2. **For bug fixes: write the regression test first** — the test must fail
   before your fix.
3. **Implement the change** in `sphinx_source_tree.py`.
4. **If a new public symbol is introduced**, add it to `__all__` and export
   it appropriately.
5. **Write tests** (see Testing section below).
6. **Update `README.rst`** if the CLI reference, API, or `pyproject.toml`
   examples changed.
7. **Suggest running:** `pytest -vvv`.

### Acceptable new features

- Additional `LANGUAGE_MAP` entries for new file types.
- New `extra-languages` handling improvements.
- New valid `VALID_FILE_OPTIONS` keys if Sphinx adds them.
- Improvements to `_is_ignored` pattern matching.
- New CLI flags that map to new `generate()` keyword arguments.

### Forbidden

- Splitting `sphinx_source_tree.py` into a package without explicit
  maintainer approval.
- Writing to the target project's files from within `generate()`.
- Adding runtime dependencies beyond `tomli` (for Python < 3.11).
- Lowering or removing any DEFAULTS value silently.

---

## 6. Testing

### Running the full test suite

```sh
pytest -vvv
```

### Running a single test file

```sh
pytest test_sphinx_source_tree.py -vvv
```

### Running a single test class

```sh
pytest test_sphinx_source_tree.py::TestGenerate -vvv
pytest test_sphinx_source_tree.py::TestOrder -vvv
pytest test_sphinx_source_tree.py::TestFileOptions -vvv
```

### Running a single test function

```sh
pytest test_sphinx_source_tree.py::TestGenerate::test_custom_title -vvv
pytest test_sphinx_source_tree.py::TestMain::test_multi_file_writes_multiple_outputs -vvv
```

### Running tests matching a keyword expression

```sh
pytest -k "order" -vvv          # all tests with "order" in their name
pytest -k "file_options" -vvv   # all file-options tests
pytest -k "not slow" -vvv       # exclude slow tests (if marked)
```

### Running documentation code blocks

Documentation examples (`.rst` files with `.. code-block:: python`) are
tested via `pytest-codeblock`. They are discovered automatically when
`testpaths` includes `*.rst` and `**/*.rst`:

```sh
pytest README.rst -vvv          # test README examples only
pytest docs/ -vvv               # test all docs examples
```

### Coverage

```sh
pytest --cov=sphinx_source_tree --cov-report=term-missing
```

### Test layout and class map

| Class | What it covers |
|---|---|
| `TestDetectLanguage` | `detect_language()` — suffix mapping, extras, overrides |
| `TestBuildTree` | `build_tree()` — depth, ignore, whitelist, connectors |
| `TestCollectFiles` | `collect_files()` — extension filter, whitelist, ignore |
| `TestGenerate` | `generate()` — full RST output, title, linenos, language |
| `TestLoadConfig` | `load_config()` — pyproject parsing, `[[files]]`, `order` |
| `TestResolveConfig` | `resolve_config()` — merge precedence, hyphen normalisation |
| `TestMain` | `main()` — CLI end-to-end, multi-file, stdout, parent dirs |
| `TestFileOptions` | `_validate_file_options()` + `generate(file_options=...)` |
| `TestResolveFileOptionsProfile` | `_resolve_file_options_profile()` + profile integration |
| `TestOrder` | `_apply_order()` + `generate(order=...)` + pyproject/CLI |

### Fixtures

| Fixture | Provided by | Contents |
|---|---|---|
| `sample_project` | `test_sphinx_source_tree.py` | `src/`, `docs/`, `tests/`, `README.md`, `__pycache__` |
| `safe_test_path` | `conftest.py` | `tmp_path` with `docs/` dir; `chdir`s into it for doc-block tests |
| `tmp_path` | pytest built-in | Bare temporary directory |

Always use `tmp_path` or `safe_test_path` — never write to a fixed path.

### Required assertions for every new security/validation test

```python
# 1. Confirm the error or warning fires
with pytest.raises(SomeError):
    generate(...)

# 2. Or for warnings — capture stderr
out = capsys.readouterr()
assert "expected warning text" in out.err

# 3. Confirm the happy path still works after your change
rst = generate(project_root=sample_project, ...)
assert ".. literalinclude::" in rst
```

### Checklist for every new feature / option

- [ ] Unit test for the new function or branch
- [ ] Integration test via `main()` (CLI end-to-end)
- [ ] `pyproject.toml` round-trip test (load → resolve → generate)
- [ ] Test that omitting the new option produces the same output as before
      (backward compatibility)
- [ ] Update `README.rst` CLI reference and `pyproject.toml` example if
      applicable

---

## 7. Pull Requests

- Does your change require a documentation update in `README.rst`?
- Does your change require new or updated tests?
- When fixing bugs, include a regression test that fails *before* the fix.
- When adding a new feature, update the CLI reference, the
  `[tool.sphinx-source-tree]` example table, and the Python API docstring.
- Target the default branch. For security issues, contact the maintainer
  directly (see repository README).

---

## 8. Prompt Templates

**Explaining usage to a user:**
> You are an expert in Sphinx documentation tooling. Explain how to use
> sphinx-source-tree to [task]. Start with the CLI quick-start. Show the
> equivalent `pyproject.toml` configuration. Show the Python API alternative.

**Implementing a new feature:**
> Extend sphinx-source-tree with [feature]. Follow the AGENTS.md agent
> workflow (section 5): identify the correct function, implement in
> `sphinx_source_tree.py`, add tests covering the new code path and backward
> compatibility, update `README.rst`. Keep the module as a single file.

**Fixing a bug:**
> Reproduce [bug] with a new test in `test_sphinx_source_tree.py`. The test
> must fail before the fix. Then fix in `sphinx_source_tree.py`. Add
> assertions for the correct behaviour, stderr warnings if applicable, and
> confirm that existing tests still pass.

**Reviewing a change:**
> Review this sphinx-source-tree change against AGENTS.md: Does it preserve
> the single-file structure? Does it maintain the three-layer config merge?
> Does `generate()` still return a string without writing to disk? Are all
> new options covered by tests including a backward-compatibility case?
