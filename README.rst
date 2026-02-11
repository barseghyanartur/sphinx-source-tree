sphinx-source-tree
==================

Generate a reStructuredText (``.rst``) file that contains:

1. An ASCII directory tree of your project.
2. A ``literalinclude`` directive for every source file you select.

The result is a single ``.rst`` document ready to be included in a Sphinx
documentation build so readers can browse every file without leaving the
docs.


Installation
------------

From PyPI::

    pip install sphinx-source-tree

From source::

    git clone https://github.com/yourname/sphinx-source-tree.git
    cd sphinx-source-tree
    pip install .


Quick start
-----------

Run in your project root::

    sphinx-source-tree

This writes ``docs/source_tree.rst`` with the full tree and
``literalinclude`` blocks for ``.py``, ``.md``, ``.js`` and ``.rst``
files.

Print to stdout instead::

    sphinx-source-tree --stdout


CLI reference
-------------

::

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

Example::

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

You can also call the generator from Python::

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

``generate()`` returns the RST content as a string and never writes to
disk, so you can post-process or redirect as needed.

Lower-level helpers are also importable:

- ``build_tree()`` -- ASCII tree string.
- ``collect_files()`` -- list of ``Path`` objects to include.
- ``detect_language()`` -- suffix-to-Sphinx-language mapping.
- ``load_config()`` -- read ``[tool.sphinx-source-tree]`` from
  ``pyproject.toml``.


Running the tests
-----------------

::

    pip install -e ".[test]"
    pytest tests.py -v


License
-------

MIT.  See the ``LICENSE`` file for the full text.
