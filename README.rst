===================
sphinx-source-tree
===================
Ship entire project source code and directory tree with your Sphinx
documentation.

.. External references

.. _Sphinx: https://www.sphinx-doc.org/
.. _reStructuredText: https://docutils.sourceforge.io/rst.html

.. Internal references

.. _Read the Docs: http://sphinx-source-tree.readthedocs.io/
.. _GitHub: https://github.com/barseghyanartur/sphinx-source-tree

.. image:: https://img.shields.io/pypi/v/sphinx-source-tree.svg
   :target: https://pypi.python.org/pypi/sphinx-source-tree
   :alt: PyPI Version

.. image:: https://img.shields.io/pypi/pyversions/sphinx-source-tree.svg
    :target: https://pypi.python.org/pypi/sphinx-source-tree/
    :alt: Supported Python versions

.. image:: https://github.com/barseghyanartur/sphinx-source-tree/actions/workflows/test.yml/badge.svg?branch=main
   :target: https://github.com/barseghyanartur/sphinx-source-tree/actions
   :alt: Build Status

.. image:: https://readthedocs.org/projects/sphinx-source-tree/badge/?version=latest
    :target: http://sphinx-source-tree.readthedocs.io
    :alt: Documentation Status

.. image:: https://img.shields.io/badge/docs-llms.txt-blue
    :target: https://sphinx-source-tree.readthedocs.io/en/latest/llms.txt
    :alt: llms.txt - documentation for LLMs

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/barseghyanartur/sphinx-source-tree/#License
   :alt: MIT

.. image:: https://coveralls.io/repos/github/barseghyanartur/sphinx-source-tree/badge.svg?branch=main&service=github
    :target: https://coveralls.io/github/barseghyanartur/sphinx-source-tree?branch=main
    :alt: Coverage

Generate a reStructuredText (``.rst``) file that contains:

1. An ASCII directory tree of your project.
2. A ``literalinclude`` directive for every source file you select.

The result is a single ``.rst`` document ready to be included in a `Sphinx`_
documentation build, specifically for the ``llms.txt``, providing full
project context for LLMs.

Prerequisites
=============
Python 3.10+

Installation
============

.. code-block:: sh

   uv pip install sphinx-source-tree

Usage
=====
Quick start
-----------

Run in your project root:

.. code-block:: sh

   sphinx-source-tree

This writes ``docs/source_tree.rst`` with the full tree and
``literalinclude`` blocks for ``.py``, ``.md``, ``.js`` and ``.rst``
files.

Print to stdout instead:

.. code-block:: sh

   sphinx-source-tree --stdout

CLI reference
-------------

.. code-block:: sh

   sphinx-source-tree [OPTIONS]

``-p, --project-root PATH``
    Project directory.  Default: current directory.

``-d, --depth N``
    Maximum tree depth.  Default: ``10``.

``-o, --output PATH``
    Output ``.rst`` file.  Default: ``docs/source_tree.rst``.

``-e, --extensions EXT [EXT ...]``
    File suffixes to include via ``literalinclude``.
    Default: ``.py .md .js .rst``.

``-i, --ignore PAT [PAT ...]``
    Glob patterns to ignore (matched against both the relative path
    and the bare file name).

``-w, --whitelist DIR [DIR ...]``
    Restrict output to these directories.  Ignored when
    ``--include-all`` is active.

``--include-all / --no-include-all``
    Include everything regardless of whitelist.  Default: on.

``-t, --title TEXT``
    RST section title.  Default: ``Project source-tree``.

``--linenos / --no-linenos``
    Attach ``:linenos:`` to ``literalinclude`` directives.
    Default: off.

``--stdout``
    Write to stdout instead of the output file.

``-V, --version``
    Show version and exit.

Configuration via pyproject.toml
---------------------------------

All CLI options (except ``--stdout`` and ``--version``) can be set under
``[tool.sphinx-source-tree]`` in your project's ``pyproject.toml``.
CLI arguments always take precedence.

Example:

.. code-block:: toml

   [tool.sphinx-source-tree]
   depth = 4
   output = "docs/source_tree.rst"
   extensions = [".py", ".rst", ".toml"]
   ignore = ["__pycache__", "*.pyc", ".git", "*.egg-info"]
   whitelist = ["src", "docs"]
   include-all = false
   title = "Source listing"
   linenos = true
   extra-languages = {".vue" = "vue", ".svelte" = "svelte"}

Key names use hyphens (``include-all``) to follow TOML/PEP 621
convention; they are normalised internally.

Python API
----------

You can also call the generator from Python:

.. pytestfixture: safe_test_path
.. code-block:: python
    :name: test_python_api

    from pathlib import Path
    from sphinx_source_tree import generate

    rst = generate(
        project_root=Path("."),
        output=Path("docs/source_tree1.rst"),
        depth=5,
        extensions=[".py", ".rst"],
        ignore=["__pycache__", "*.pyc"],
        title="My project source",
    )
    Path("docs/source_tree.rst").write_text(rst)

``generate()`` returns the RST content as a string and never writes to
disk, so you can post-process or redirect as needed.

Lower-level helpers are also importable:

- ``build_tree()`` -- ASCII tree string.
- ``collect_files()`` -- list of ``Path`` objects to include.
- ``detect_language()`` -- suffix-to-Sphinx-language mapping.
- ``load_config()`` -- read ``[tool.sphinx-source-tree]`` from
  ``pyproject.toml``.

Documentation
=============
- Documentation is available on `Read the Docs`_.

Tests
=====

Run the tests:

.. code-block:: sh

   pytest -vvv

Writing documentation
=====================

Keep the following hierarchy.

.. code-block:: text

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

License
=======

MIT

Support
=======
For security issues contact me at the e-mail given in the `Author`_ section.

For overall issues, go to `GitHub`_.

Author
======

Artur Barseghyan <artur.barseghyan@gmail.com>
