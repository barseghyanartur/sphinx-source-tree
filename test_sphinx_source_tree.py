from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from sphinx_source_tree import (
    DEFAULTS,
    SYSTEM_EXTENSIONS,
    SYSTEM_IGNORE,
    build_parser,
    build_tree,
    collect_files,
    detect_language,
    generate,
    load_config,
    main,
    resolve_config,
)

__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2026 Artur Barseghyan"
__license__ = "MIT"
__all__ = (
    "TestBuildTree",
    "TestCollectFiles",
    "TestDetectLanguage",
    "TestFileOptions",
    "TestGenerate",
    "TestLoadConfig",
    "TestLoadConfig",
    "TestLoadConfig",
    "TestMain",
    "TestOrder",
    "TestResolveConfig",
)


# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------


@pytest.fixture
def sample_project(tmp_path):
    """Minimal project tree used by most tests."""
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app.py").write_text(
        "print('hello')\n", encoding="utf-8"
    )
    (tmp_path / "src" / "utils.py").write_text(
        "def helper(): pass\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.rst").write_text(
        "Title\n=====\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_app.py").write_text(
        "def test_one(): pass\n", encoding="utf-8"
    )
    (tmp_path / "README.md").write_text("# Readme\n", encoding="utf-8")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "app.cpython-312.pyc").write_bytes(b"\x00")
    return tmp_path


# ----------------------------------------------------------------------------
# Detect_language
# ----------------------------------------------------------------------------


class TestDetectLanguage:
    def test_known_suffix(self):
        assert detect_language(Path("foo.py")) == "python"
        assert detect_language(Path("bar.js")) == "javascript"
        assert detect_language(Path("baz.rst")) == "rst"

    def test_unknown_suffix(self):
        assert detect_language(Path("data.xyz")) == ""

    def test_extra_mapping_extends(self):
        assert detect_language(Path("x.vue"), extra={".vue": "vue"}) == "vue"

    def test_extra_mapping_overrides(self):
        assert (
            detect_language(Path("x.py"), extra={".py": "python3"}) == "python3"
        )


# ----------------------------------------------------------------------------
# build_tree
# ----------------------------------------------------------------------------


class TestBuildTree:
    def test_basic(self, sample_project):
        tree = build_tree(
            sample_project,
            max_depth=2,
            ignore=["__pycache__"],
            whitelist=[],
            include_all=True,
            root=sample_project,
        )
        assert "src" in tree
        assert "docs" in tree
        assert "tests" in tree
        assert "README.md" in tree
        assert "__pycache__" not in tree

    def test_last_entry_uses_corner_connector(self, sample_project):
        tree = build_tree(
            sample_project,
            max_depth=1,
            ignore=["__pycache__"],
            whitelist=[],
            include_all=True,
            root=sample_project,
        )
        lines = [_l for _l in tree.splitlines() if _l.strip()]
        last = lines[-1]
        assert "\u2514\u2500\u2500 " in last

    def test_depth_zero(self, sample_project):
        tree = build_tree(
            sample_project,
            max_depth=0,
            ignore=[],
            whitelist=[],
            include_all=True,
            root=sample_project,
        )
        # depth=0 lists immediate children only (no recursion into dirs)
        assert "src" in tree
        assert "app.py" not in tree

    def test_negative_depth(self, sample_project):
        tree = build_tree(
            sample_project,
            max_depth=-1,
            ignore=[],
            whitelist=[],
            include_all=True,
            root=sample_project,
        )
        assert tree == ""

    def test_whitelist(self, sample_project):
        tree = build_tree(
            sample_project,
            max_depth=3,
            ignore=["__pycache__"],
            whitelist=["src"],
            include_all=False,
            root=sample_project,
        )
        assert "src" in tree
        assert "app.py" in tree
        assert "docs" not in tree
        assert "README.md" not in tree

    def test_ignore_by_name(self, sample_project):
        """Patterns should match against file *name*, not just full path."""
        tree = build_tree(
            sample_project,
            max_depth=3,
            ignore=["*.pyc", "__pycache__"],
            whitelist=[],
            include_all=True,
            root=sample_project,
        )
        assert "__pycache__" not in tree


# ----------------------------------------------------------------------------
# collect_files
# ----------------------------------------------------------------------------


class TestCollectFiles:
    def test_basic(self, sample_project):
        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        names = [f.name for f in files]
        assert "app.py" in names
        assert "test_app.py" in names
        assert "app.cpython-312.pyc" not in names

    def test_whitelist_restricts(self, sample_project):
        files = collect_files(
            sample_project,
            extensions=[".py", ".rst"],
            ignore=["__pycache__"],
            whitelist=["docs"],
            include_all=False,
        )
        rels = [f.relative_to(sample_project).as_posix() for f in files]
        assert "docs/index.rst" in rels
        assert all(r.startswith("docs/") for r in rels)

    def test_extension_filter(self, sample_project):
        files = collect_files(
            sample_project,
            extensions=[".rst"],
            ignore=[],
            whitelist=[],
            include_all=True,
        )
        assert all(f.suffix == ".rst" for f in files)


# ----------------------------------------------------------------------------
# generate
# ----------------------------------------------------------------------------


class TestGenerate:
    def test_basic_output(self, sample_project):
        out_file = sample_project / "docs" / "tree.rst"
        rst = generate(
            project_root=sample_project,
            output=out_file,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        assert "Project source-tree" in rst
        assert ".. code-block:: text" in rst
        assert ".. literalinclude::" in rst
        assert "app.py" in rst

    def test_custom_title(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "out.rst",
            title="My Custom Title",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        assert "My Custom Title" in rst
        assert "=" * len("My Custom Title") in rst

    def test_linenos(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            linenos=True,
        )
        assert ":linenos:" in rst

    def test_no_linenos_by_default(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        assert ":linenos:" not in rst

    def test_language_annotation(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        assert ":language: python" in rst

    def test_extra_languages(self, sample_project):
        (sample_project / "src" / "style.vue").write_text(
            "<template></template>", encoding="utf-8"
        )
        rst = generate(
            project_root=sample_project,
            output=sample_project / "out.rst",
            extensions=[".vue"],
            ignore=["__pycache__"],
            extra_languages={".vue": "vue"},
        )
        assert ":language: vue" in rst


# ----------------------------------------------------------------------------
# load_config
# ----------------------------------------------------------------------------


class TestLoadConfig:
    def test_missing_file(self, tmp_path):
        assert load_config(tmp_path) == {}

    def test_no_section(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[project]\nname = "foo"\n', encoding="utf-8"
        )
        assert load_config(tmp_path) == {}

    def test_reads_section(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                depth = 5
                title = "Source"
                extensions = [".py", ".rs"]
                linenos = true
            """),
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        assert cfg["depth"] == 5
        assert cfg["title"] == "Source"
        assert cfg["extensions"] == [".py", ".rs"]
        assert cfg["linenos"] is True

    def test_reads_files_entries(self, tmp_path):
        """``files`` key is returned as-is for resolve_config to process."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                depth = 4

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_a.rst"
                title = "Tree A"

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_b.rst"
                title = "Tree B"
                extensions = [".py"]
            """),
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        assert cfg["depth"] == 4
        assert len(cfg["files"]) == 2
        assert cfg["files"][0]["title"] == "Tree A"
        assert cfg["files"][1]["extensions"] == [".py"]

    def test_reads_order_from_top_level(self, tmp_path):
        """``order`` key at top level is loaded correctly."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                order = ["README.rst", "src/app.py"]
            """),
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        assert cfg["order"] == ["README.rst", "src/app.py"]

    def test_reads_order_from_files_entry(self, tmp_path):
        """``order`` key inside a [[files]] entry is loaded correctly."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree.rst"
                order = ["src/core.py", "src/utils.py"]
            """),
            encoding="utf-8",
        )
        cfg = load_config(tmp_path)
        assert cfg["files"][0]["order"] == ["src/core.py", "src/utils.py"]


# ----------------------------------------------------------------------------
# resolve_config
# ----------------------------------------------------------------------------


class TestResolveConfig:
    def test_defaults_used(self, tmp_path):
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["depth"] == DEFAULTS["depth"]
        assert cfg["title"] == DEFAULTS["title"]

    def test_pyproject_overrides_defaults(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            '[tool.sphinx-source-tree]\ndepth = 3\ntitle = "Tree"\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["depth"] == 3
        assert cfg["title"] == "Tree"

    def test_cli_overrides_pyproject(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[tool.sphinx-source-tree]\ndepth = 3\n", encoding="utf-8"
        )
        parser = build_parser()
        args = parser.parse_args(
            [
                "--project-root",
                str(tmp_path),
                "--depth",
                "7",
            ]
        )
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["depth"] == 7

    def test_hyphenated_keys_normalised(self, tmp_path):
        (tmp_path / "pyproject.toml").write_text(
            "[tool.sphinx-source-tree]\ninclude-all = true\n"
            'extra-languages = {".vue" = "vue"}\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["include_all"] is True
        assert cfg["extra_languages"] == {".vue": "vue"}

    def test_no_files_key_when_none_configured(self, tmp_path):
        """When no [[files]] entries exist, 'files' should not be in cfg."""
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert "files" not in cfg

    def test_files_inherit_top_level_defaults(self, tmp_path):
        """Per-file entries should inherit top-level pyproject settings."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                depth = 4
                linenos = true

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_a.rst"
                title = "Tree A"

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_b.rst"
                title = "Tree B"
                depth = 2
            """),
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)

        assert len(cfg["files"]) == 2

        # Tree A inherits depth=4 and linenos=true from top-level
        assert cfg["files"][0]["depth"] == 4
        assert cfg["files"][0]["linenos"] is True
        assert cfg["files"][0]["title"] == "Tree A"

        # Tree B overrides depth but still inherits linenos
        assert cfg["files"][1]["depth"] == 2
        assert cfg["files"][1]["linenos"] is True
        assert cfg["files"][1]["title"] == "Tree B"

    def test_cli_overrides_all_file_entries(self, tmp_path):
        """A CLI flag should override every per-file entry."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_a.rst"
                depth = 3

                [[tool.sphinx-source-tree.files]]
                output = "docs/tree_b.rst"
                depth = 5
            """),
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(
            ["--project-root", str(tmp_path), "--depth", "9"]
        )
        delattr(args, "stdout")
        cfg = resolve_config(args)

        for file_cfg in cfg["files"]:
            assert file_cfg["depth"] == 9


# ----------------------------------------------------------------------------
# main (integration)
# ----------------------------------------------------------------------------


class TestMain:
    def test_writes_output_file(self, sample_project):
        out = sample_project / "output.rst"
        main(
            [
                "--project-root",
                str(sample_project),
                "--output",
                str(out),
                "--include-all",
                "--ignore",
                "__pycache__",
                "*.pyc",
            ]
        )
        assert out.exists()
        content = out.read_text(encoding="utf-8")
        assert "Project source-tree" in content
        assert "app.py" in content

    def test_stdout_mode(self, sample_project, capsys):
        main(
            [
                "--project-root",
                str(sample_project),
                "--stdout",
                "--include-all",
                "--ignore",
                "__pycache__",
                "*.pyc",
            ]
        )
        captured = capsys.readouterr()
        assert "Project source-tree" in captured.out
        assert ".. literalinclude::" in captured.out

    def test_creates_parent_dirs(self, sample_project):
        out = sample_project / "deep" / "nested" / "tree.rst"
        main(
            [
                "--project-root",
                str(sample_project),
                "--output",
                str(out),
                "--include-all",
                "--ignore",
                "__pycache__",
                "*.pyc",
            ]
        )
        assert out.exists()

    def test_multi_file_writes_multiple_outputs(self, sample_project):
        """[[files]] entries each produce their own output file."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_py.rst"
                title = "Python Files"
                extensions = [".py"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_rst.rst"
                title = "RST Files"
                extensions = [".rst"]
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])

        py_out = sample_project / "docs" / "tree_py.rst"
        rst_out = sample_project / "docs" / "tree_rst.rst"

        assert py_out.exists()
        assert rst_out.exists()

        py_content = py_out.read_text(encoding="utf-8")
        rst_content = rst_out.read_text(encoding="utf-8")

        assert "Python Files" in py_content
        assert ":language: python" in py_content
        # .rst files should not appear in the py-only tree's literalincludes
        assert ":language: rst" not in py_content

        assert "RST Files" in rst_content
        assert ":language: rst" in rst_content

    def test_multi_file_stdout_mode(self, sample_project, capsys):
        """--stdout with [[files]] concatenates all outputs."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_a.rst"
                title = "Alpha"
                extensions = [".py"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_b.rst"
                title = "Beta"
                extensions = [".md"]
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project), "--stdout"])
        captured = capsys.readouterr()
        assert "Alpha" in captured.out
        assert "Beta" in captured.out

    def test_multi_file_cli_depth_overrides_all(self, sample_project):
        """A CLI --depth flag overrides depth in every [[files]] entry."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_a.rst"
                extensions = [".py"]
                depth = 3

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/tree_b.rst"
                extensions = [".md"]
                depth = 5
            """),
            encoding="utf-8",
        )
        # CLI depth=1 should win for both files; trees will be shallow
        main(
            [
                "--project-root",
                str(sample_project),
                "--depth",
                "1",
            ]
        )
        for out in ("tree_a.rst", "tree_b.rst"):
            content = (sample_project / "docs" / out).read_text(
                encoding="utf-8"
            )
            assert "to 1 levels" in content


# ----------------------------------------------------------------------------
# file_options
# ----------------------------------------------------------------------------


class TestFileOptions:
    """Tests for per-file literalinclude inclusion-range options."""

    # -- _validate_file_options ----------------------------------------------

    def test_validate_accepts_all_valid_options(self):
        from sphinx_source_tree import _validate_file_options

        opts = _validate_file_options(
            {
                "lines": "1-10",
                "start-at": "def foo",
                "start-after": "# begin",
                "end-before": "# end",
                "end-at": "return",
            }
        )
        assert opts == {
            "lines": "1-10",
            "start-at": "def foo",
            "start-after": "# begin",
            "end-before": "# end",
            "end-at": "return",
        }

    def test_validate_normalises_underscores_to_hyphens(self):
        from sphinx_source_tree import _validate_file_options

        opts = _validate_file_options(
            {
                "end_before": "# Tests",
                "start_after": "# begin",
                "start_at": "class Foo",
                "end_at": "pass",
            }
        )
        assert "end-before" in opts
        assert "start-after" in opts
        assert "start-at" in opts
        assert "end-at" in opts
        assert "end_before" not in opts

    def test_validate_drops_unknown_keys_with_warning(self, capsys):
        from sphinx_source_tree import _validate_file_options

        opts = _validate_file_options(
            {"end-before": "# stop", "bad-option": "x", "another-bad": "y"},
            source="src/foo.py",
        )
        assert "end-before" in opts
        assert "bad-option" not in opts
        assert "another-bad" not in opts

        err = capsys.readouterr().err
        assert "bad-option" in err
        assert "another-bad" in err
        assert "src/foo.py" in err

    def test_validate_coerces_values_to_strings(self):
        from sphinx_source_tree import _validate_file_options

        # ``lines`` might come from TOML as an integer or a string
        opts = _validate_file_options({"lines": 42})
        assert opts["lines"] == "42"

    def test_validate_empty_input_returns_empty(self):
        from sphinx_source_tree import _validate_file_options

        assert _validate_file_options({}) == {}

    # -- generate() with file_options ----------------------------------------

    def test_end_before_emitted_for_matched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"end-before": "# *** Tests ***"}},
        )
        assert ":end-before: # *** Tests ***" in rst

    def test_start_after_emitted_for_matched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"start-after": "# public API"}},
        )
        assert ":start-after: # public API" in rst

    def test_start_at_emitted_for_matched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"start-at": "def main"}},
        )
        assert ":start-at: def main" in rst

    def test_end_at_emitted_for_matched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"end-at": "return result"}},
        )
        assert ":end-at: return result" in rst

    def test_lines_emitted_for_matched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"lines": "1-20"}},
        )
        assert ":lines: 1-20" in rst

    def test_multiple_options_all_emitted(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={
                "src/app.py": {
                    "start-after": "# begin",
                    "end-before": "# end",
                }
            },
        )
        assert ":start-after: # begin" in rst
        assert ":end-before: # end" in rst

    def test_options_not_emitted_for_unmatched_file(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"end-before": "# stop"}},
        )
        # Locate the utils.py literalinclude block and check it has no options
        lines = rst.splitlines()
        utils_idx = next(
            i
            for i, ln in enumerate(lines)
            if "literalinclude" in ln and "utils.py" in ln
        )
        block = lines[utils_idx : utils_idx + 10]
        assert not any(":end-before:" in ln for ln in block)

    def test_options_placed_after_caption_and_linenos(self, sample_project):
        """Inclusion-range options must come after :caption: / :linenos:."""
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            linenos=True,
            file_options={"src/app.py": {"end-before": "# stop"}},
        )
        lines = rst.splitlines()
        # Find the src/app.py block specifically, then check ordering within it
        caption_idx = next(
            i for i, ln in enumerate(lines) if ":caption: src/app.py" in ln
        )
        # :linenos: and :end-before: must both appear after the caption line
        block = lines[caption_idx:]
        linenos_pos = next(i for i, ln in enumerate(block) if ":linenos:" in ln)
        end_before_pos = next(
            i for i, ln in enumerate(block) if ":end-before:" in ln
        )
        assert linenos_pos < end_before_pos

    def test_absolute_path_key_resolved(self, sample_project):
        """An absolute path key should be matched to the correct file."""
        abs_path = str(sample_project / "src" / "app.py")
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={abs_path: {"end-before": "# Tests"}},
        )
        assert ":end-before: # Tests" in rst

    def test_underscore_option_key_works(self, sample_project):
        """Keys written with underscores (TOML style) should be normalised."""
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={"src/app.py": {"end_before": "# Tests"}},
        )
        assert ":end-before: # Tests" in rst

    def test_no_file_options_produces_clean_output(self, sample_project):
        """When file_options is omitted the output should be unchanged."""
        rst_without = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        rst_with_empty = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            file_options={},
        )
        assert rst_without == rst_with_empty
        assert ":end-before:" not in rst_without
        assert ":start-after:" not in rst_without

    # -- pyproject.toml integration ------------------------------------------

    def test_file_options_loaded_from_pyproject(self, sample_project):
        """file-options table in pyproject.toml should drive the output."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options]
                "src/app.py" = {"end-before" = "# *** Tests ***"}
            """),
            encoding="utf-8",
        )
        out = sample_project / "docs" / "out.rst"
        main(["--project-root", str(sample_project), "--output", str(out)])
        content = out.read_text(encoding="utf-8")
        assert ":end-before: # *** Tests ***" in content

    def test_file_options_multiple_files_in_pyproject(self, sample_project):
        """Multiple entries under file-options should each be applied."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options]
                "src/app.py" = {"end-before" = "# stop app"}
                "src/utils.py" = {"start-after" = "# public"}
            """),
            encoding="utf-8",
        )
        out = sample_project / "docs" / "out.rst"
        main(["--project-root", str(sample_project), "--output", str(out)])
        content = out.read_text(encoding="utf-8")
        assert ":end-before: # stop app" in content
        assert ":start-after: # public" in content


# ----------------------------------------------------------------------------
# _resolve_file_options_profile
# ----------------------------------------------------------------------------


class TestResolveFileOptionsProfile:
    """Tests for the profile-selection helper."""

    def test_no_profile_returns_file_options(self):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options": {"src/app.py": {"end-before": "# stop"}},
            "file_options_profiles": {},
            "file_options_profile": None,
        }
        assert _resolve_file_options_profile(cfg) == {
            "src/app.py": {"end-before": "# stop"}
        }

    def test_named_profile_returned_when_found(self):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options": {"src/app.py": {"end-before": "# top-level"}},
            "file_options_profiles": {
                "compact": {"src/app.py": {"end-before": "# compact"}},
                "full": {},
            },
            "file_options_profile": "compact",
        }
        assert _resolve_file_options_profile(cfg) == {
            "src/app.py": {"end-before": "# compact"}
        }

    def test_full_profile_returns_empty_mapping(self):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options": {"src/app.py": {"end-before": "# stop"}},
            "file_options_profiles": {
                "compact": {"src/app.py": {"end-before": "# stop"}},
                "full": {},
            },
            "file_options_profile": "full",
        }
        assert _resolve_file_options_profile(cfg) == {}

    def test_missing_profile_warns_and_falls_back(self, capsys):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options": {"src/app.py": {"end-before": "# stop"}},
            "file_options_profiles": {"compact": {}},
            "file_options_profile": "nonexistent",
        }
        result = _resolve_file_options_profile(cfg)
        assert result == {"src/app.py": {"end-before": "# stop"}}
        err = capsys.readouterr().err
        assert "nonexistent" in err
        assert "compact" in err

    def test_missing_profile_warning_lists_available_profiles(self, capsys):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options": {},
            "file_options_profiles": {"alpha": {}, "beta": {}, "gamma": {}},
            "file_options_profile": "delta",
        }
        _resolve_file_options_profile(cfg)
        err = capsys.readouterr().err
        assert "alpha" in err
        assert "beta" in err
        assert "gamma" in err

    def test_no_profiles_key_falls_back_to_file_options(self):
        from sphinx_source_tree import _resolve_file_options_profile

        # cfg coming from old config that never had profiles
        cfg = {
            "file_options": {"src/app.py": {"lines": "1-10"}},
            "file_options_profile": None,
        }
        assert _resolve_file_options_profile(cfg) == {
            "src/app.py": {"lines": "1-10"}
        }

    def test_profile_none_with_no_file_options_returns_empty(self):
        from sphinx_source_tree import _resolve_file_options_profile

        cfg = {
            "file_options_profiles": {},
            "file_options_profile": None,
        }
        assert _resolve_file_options_profile(cfg) == {}

    # -- integration via [[files]] + pyproject.toml ---------------------------

    def test_each_file_entry_can_select_different_profile(self, sample_project):
        """Two [[files]] entries selecting different profiles produce
        different output."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options-profiles.compact]
                "src/app.py" = {{"end-before" = "# stop"}}

                [tool.sphinx-source-tree.file-options-profiles.full]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/full.rst"
                title = "Full"
                extensions = [".py"]
                file-options-profile = "full"

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/compact.rst"
                title = "Compact"
                extensions = [".py"]
                file-options-profile = "compact"
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])

        full = (sample_project / "docs" / "full.rst").read_text(
            encoding="utf-8"
        )
        compact = (sample_project / "docs" / "compact.rst").read_text(
            encoding="utf-8"
        )

        assert ":end-before:" not in full
        assert ":end-before: # stop" in compact

    def test_top_level_file_options_used_when_no_profile_set(
        self, sample_project
    ):
        """When no file-options-profile is set the flat file-options table
        applies, even in multi-file mode."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options]
                "src/app.py" = {{"end-before" = "# stop"}}

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/out.rst"
                title = "All files"
                extensions = [".py"]
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])
        content = (sample_project / "docs" / "out.rst").read_text(
            encoding="utf-8"
        )
        assert ":end-before: # stop" in content

    def test_missing_profile_in_files_entry_warns_and_uses_fallback(
        self, sample_project, capsys
    ):
        """A [[files]] entry referencing an undefined profile should warn
        and fall back to the top-level file-options."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options]
                "src/app.py" = {{"end-before" = "# fallback stop"}}

                [tool.sphinx-source-tree.file-options-profiles.compact]
                "src/app.py" = {{"end-before" = "# compact stop"}}

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/out.rst"
                title = "Oops"
                extensions = [".py"]
                file-options-profile = "typo-profile"
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])
        err = capsys.readouterr().err
        assert "typo-profile" in err
        content = (sample_project / "docs" / "out.rst").read_text(
            encoding="utf-8"
        )
        assert ":end-before: # fallback stop" in content

    def test_profile_overrides_top_level_file_options(self, sample_project):
        """When a profile is active it completely replaces file_options —
        the top-level flat mapping is NOT merged in."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [tool.sphinx-source-tree.file-options]
                "src/app.py" = {{"end-before" = "# top-level stop"}}

                [tool.sphinx-source-tree.file-options-profiles.compact]
                "src/app.py" = {{"end-before" = "# compact stop"}}

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/out.rst"
                title = "Compact"
                extensions = [".py"]
                file-options-profile = "compact"
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])
        content = (sample_project / "docs" / "out.rst").read_text(
            encoding="utf-8"
        )
        assert ":end-before: # compact stop" in content
        assert ":end-before: # top-level stop" not in content


# ----------------------------------------------------------------------------
# order
# ----------------------------------------------------------------------------


def _literalinclude_order(rst: str) -> list[str]:
    """
    Return the list of :caption: values that follow a literalinclude directive.
    """
    result = []
    in_literalinclude = False
    for line in rst.splitlines():
        stripped = line.strip()
        if stripped.startswith(".. literalinclude::"):
            in_literalinclude = True
        elif in_literalinclude and stripped.startswith(":caption:"):
            result.append(stripped[len(":caption:") :].strip())
            in_literalinclude = False
        elif in_literalinclude and stripped and not stripped.startswith(":"):
            in_literalinclude = False
    return result


def _extract_tree_section(rst: str) -> str:
    """
    Return just the code-block tree from the RST (stops before file listings).
    """
    lines = rst.splitlines()
    start = next(i for i, ln in enumerate(lines) if "code-block:: text" in ln)
    # The tree ends at the first blank line after we've left the indented block
    # More robustly: find the first section header (underline of "---" or "===")
    # that follows after the code-block.  The first file listing section starts
    # right after the blank line separating the tree from it.
    in_block = False
    for i, ln in enumerate(lines[start:], start=start):
        if ln.startswith("   ") or ln == "":
            in_block = True
        elif in_block and ln and not ln.startswith(" "):
            # First non-blank, non-indented line after the tree block — this is
            # the start of the first file section.
            return "\n".join(lines[start:i])
    return "\n".join(lines[start:])


class TestOrder:
    """Tests for the ``order`` option."""

    # -- _apply_order unit tests ---------------------------------------------

    def test_apply_order_empty_returns_unchanged(self, sample_project):
        from sphinx_source_tree import _apply_order

        files = sorted(sample_project.rglob("*.py"))

        assert _apply_order(files, [], sample_project) == files

    def test_apply_order_pinned_files_come_first(self, sample_project):
        from sphinx_source_tree import _apply_order, collect_files

        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        ordered = _apply_order(
            files,
            ["src/utils.py", "src/app.py"],
            sample_project,
        )
        rels = [f.relative_to(sample_project).as_posix() for f in ordered]
        assert rels[0] == "src/utils.py"
        assert rels[1] == "src/app.py"

    def test_apply_order_unmentioned_files_follow_in_original_order(
        self, sample_project
    ):
        from sphinx_source_tree import _apply_order, collect_files

        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        ordered = _apply_order(
            files,
            ["tests/test_app.py"],
            sample_project,
        )
        rels = [f.relative_to(sample_project).as_posix() for f in ordered]
        assert rels[0] == "tests/test_app.py"
        # The rest should be in the same relative order as the original list
        original_rels = [
            f.relative_to(sample_project).as_posix() for f in files
        ]
        rest_original = [r for r in original_rels if r != "tests/test_app.py"]
        rest_ordered = rels[1:]
        assert rest_ordered == rest_original

    def test_apply_order_nonexistent_entry_warns(self, sample_project, capsys):
        from sphinx_source_tree import _apply_order, collect_files

        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        _apply_order(files, ["does/not/exist.py"], sample_project)
        err = capsys.readouterr().err
        assert "does/not/exist.py" in err

    def test_apply_order_absolute_path_accepted(self, sample_project):
        from sphinx_source_tree import _apply_order, collect_files

        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        abs_path = str(sample_project / "src" / "utils.py")
        ordered = _apply_order(files, [abs_path], sample_project)
        assert (
            ordered[0].relative_to(sample_project).as_posix() == "src/utils.py"
        )

    def test_apply_order_no_duplicates(self, sample_project):
        from sphinx_source_tree import _apply_order, collect_files

        files = collect_files(
            sample_project,
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            whitelist=[],
            include_all=True,
        )
        ordered = _apply_order(
            files,
            ["src/app.py", "src/utils.py"],
            sample_project,
        )
        rels = [f.relative_to(sample_project).as_posix() for f in ordered]
        assert len(rels) == len(set(rels)), "Duplicate files in output"

    # -- generate() with order -----------------------------------------------

    def test_generate_order_places_files_first(self, sample_project):
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            order=["src/utils.py", "src/app.py"],
        )
        captions = _literalinclude_order(rst)
        assert captions.index("src/utils.py") < captions.index("src/app.py")
        assert captions[0] == "src/utils.py"
        assert captions[1] == "src/app.py"

    def test_generate_order_does_not_affect_tree(self, sample_project):
        """The ASCII directory tree must be identical regardless of order."""
        rst_default = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        rst_ordered = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            order=["src/utils.py", "src/app.py"],
        )
        assert _extract_tree_section(rst_default) == _extract_tree_section(
            rst_ordered
        )

    def test_generate_order_none_is_default_sorted(self, sample_project):
        """Passing order=None (default) preserves the existing sorted order."""
        rst_no_order = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        rst_explicit_none = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            order=None,
        )
        assert rst_no_order == rst_explicit_none

    def test_generate_order_empty_list_is_noop(self, sample_project):
        rst_no_order = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        rst_empty_order = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            order=[],
        )
        assert rst_no_order == rst_empty_order

    def test_generate_order_partial_list_rest_in_default_order(
        self, sample_project
    ):
        """
        Only pin one file; the rest should follow in default sorted order.
        """
        rst_default = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
        )
        rst_ordered = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=["__pycache__", "*.pyc"],
            order=["tests/test_app.py"],
        )
        default_captions = _literalinclude_order(rst_default)
        ordered_captions = _literalinclude_order(rst_ordered)

        assert ordered_captions[0] == "tests/test_app.py"
        rest = ordered_captions[1:]
        expected_rest = [
            c for c in default_captions if c != "tests/test_app.py"
        ]
        assert rest == expected_rest

    # -- pyproject.toml integration ------------------------------------------

    def test_order_loaded_from_top_level_pyproject(self, sample_project):
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]
                order = ["src/utils.py", "src/app.py"]
            """),
            encoding="utf-8",
        )
        out = sample_project / "docs" / "out.rst"
        main(
            [
                "--project-root",
                str(sample_project),
                "--output",
                str(out),
                "--extensions",
                ".py",
            ]
        )
        content = out.read_text(encoding="utf-8")
        captions = _literalinclude_order(content)
        assert captions[0] == "src/utils.py"
        assert captions[1] == "src/app.py"

    def test_order_per_files_entry_in_pyproject(self, sample_project):
        """order set inside [[files]] applies only to that output."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/ordered.rst"
                title = "Ordered"
                extensions = [".py"]
                order = ["src/utils.py", "src/app.py"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/default.rst"
                title = "Default"
                extensions = [".py"]
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])

        ordered_content = (sample_project / "docs" / "ordered.rst").read_text(
            encoding="utf-8"
        )
        default_content = (sample_project / "docs" / "default.rst").read_text(
            encoding="utf-8"
        )

        ordered_captions = _literalinclude_order(ordered_content)
        default_captions = _literalinclude_order(default_content)

        # The [[files]] with order has utils before app
        assert ordered_captions[0] == "src/utils.py"
        assert ordered_captions[1] == "src/app.py"

        # The [[files]] without order uses default sorted order
        assert default_captions.index("src/app.py") < default_captions.index(
            "src/utils.py"
        )

    def test_cli_order_overrides_pyproject(self, sample_project):
        """--order CLI flag wins over pyproject order."""
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]
                order = ["src/app.py", "src/utils.py"]
            """),
            encoding="utf-8",
        )
        out = sample_project / "docs" / "out.rst"
        main(
            [
                "--project-root",
                str(sample_project),
                "--output",
                str(out),
                "--extensions",
                ".py",
                "--order",
                "src/utils.py",
                "src/app.py",
            ]
        )
        content = out.read_text(encoding="utf-8")
        captions = _literalinclude_order(content)
        assert captions[0] == "src/utils.py"
        assert captions[1] == "src/app.py"

    def test_top_level_order_inherited_by_files_entries(self, sample_project):
        """
        A top-level order is inherited by [[files]] that don't set their own.
        """
        (sample_project / "pyproject.toml").write_text(
            textwrap.dedent(f"""\
                [tool.sphinx-source-tree]
                ignore = ["__pycache__", "*.pyc"]
                order = ["src/utils.py"]

                [[tool.sphinx-source-tree.files]]
                output = "{sample_project}/docs/out.rst"
                extensions = [".py"]
            """),
            encoding="utf-8",
        )
        main(["--project-root", str(sample_project)])
        content = (sample_project / "docs" / "out.rst").read_text(
            encoding="utf-8"
        )
        captions = _literalinclude_order(content)
        assert captions[0] == "src/utils.py"


# ---------------------------------------------------------------------------
# system_ignore / user_ignore / system_extensions / user_extensions
# ---------------------------------------------------------------------------


class TestIgnoreExtensionsMerge:
    """Tests for the system/user split of ignore and extensions."""

    # -- _merge_ignore -------------------------------------------------------

    def test_merge_ignore_uses_system_plus_user(self):
        from sphinx_source_tree import _merge_ignore

        cfg = {
            "system_ignore": ["*.pyc", "__pycache__"],
            "user_ignore": ["my_secret/", "local_*"],
            "ignore": None,
        }
        result = _merge_ignore(cfg)
        assert result == ["*.pyc", "__pycache__", "my_secret/", "local_*"]

    def test_merge_ignore_explicit_ignore_overrides_all(self):
        from sphinx_source_tree import _merge_ignore

        cfg = {
            "system_ignore": ["*.pyc"],
            "user_ignore": ["foo"],
            "ignore": ["only_this"],
        }
        assert _merge_ignore(cfg) == ["only_this"]

    def test_merge_ignore_deduplicates(self):
        from sphinx_source_tree import _merge_ignore

        cfg = {
            "system_ignore": ["*.pyc", "__pycache__"],
            "user_ignore": ["*.pyc", "extra"],
            "ignore": None,
        }
        result = _merge_ignore(cfg)
        assert result.count("*.pyc") == 1
        assert "extra" in result

    def test_merge_ignore_empty_user(self):
        from sphinx_source_tree import _merge_ignore

        cfg = {
            "system_ignore": ["*.pyc"],
            "user_ignore": [],
            "ignore": None,
        }
        assert _merge_ignore(cfg) == ["*.pyc"]

    def test_merge_ignore_empty_system(self):
        from sphinx_source_tree import _merge_ignore

        cfg = {
            "system_ignore": [],
            "user_ignore": ["my_dir"],
            "ignore": None,
        }
        assert _merge_ignore(cfg) == ["my_dir"]

    # -- _merge_extensions ---------------------------------------------------

    def test_merge_extensions_uses_system_plus_user(self):
        from sphinx_source_tree import _merge_extensions

        cfg = {
            "system_extensions": [".py", ".rst"],
            "user_extensions": [".vue", ".svelte"],
            "extensions": None,
        }
        result = _merge_extensions(cfg)
        assert result == [".py", ".rst", ".vue", ".svelte"]

    def test_merge_extensions_explicit_overrides_all(self):
        from sphinx_source_tree import _merge_extensions

        cfg = {
            "system_extensions": [".py"],
            "user_extensions": [".vue"],
            "extensions": [".ts"],
        }
        assert _merge_extensions(cfg) == [".ts"]

    def test_merge_extensions_deduplicates(self):
        from sphinx_source_tree import _merge_extensions

        cfg = {
            "system_extensions": [".py", ".rst"],
            "user_extensions": [".py", ".vue"],
            "extensions": None,
        }
        result = _merge_extensions(cfg)
        assert result.count(".py") == 1
        assert ".vue" in result

    # -- resolve_config integration ------------------------------------------

    def test_user_ignore_added_to_system_defaults(self, tmp_path):
        """user-ignore in pyproject is merged with system defaults."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.sphinx-source-tree]\nuser-ignore = ["my_dir", "local_*"]\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        # System patterns must still be present
        assert "*.pyc" in cfg["ignore"]
        assert "__pycache__" in cfg["ignore"]
        # User patterns are appended
        assert "my_dir" in cfg["ignore"]
        assert "local_*" in cfg["ignore"]

    def test_user_extensions_added_to_system_defaults(self, tmp_path):
        """user-extensions in pyproject is merged with system defaults."""
        (tmp_path / "pyproject.toml").write_text(
            "[tool.sphinx-source-tree]\nuser-extensions = "
            '[".vue", ".svelte"]\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        # System extensions must still be present
        assert ".py" in cfg["extensions"]
        assert ".rst" in cfg["extensions"]
        # User extensions are appended
        assert ".vue" in cfg["extensions"]
        assert ".svelte" in cfg["extensions"]

    def test_explicit_ignore_replaces_everything(self, tmp_path):
        """Setting ignore= directly replaces the system+user union."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.sphinx-source-tree]\nignore = ["only_this"]\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["ignore"] == ["only_this"]

    def test_explicit_extensions_replaces_everything(self, tmp_path):
        """Setting extensions= directly replaces the system+user union."""
        (tmp_path / "pyproject.toml").write_text(
            '[tool.sphinx-source-tree]\nextensions = [".rs"]\n',
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert cfg["extensions"] == [".rs"]

    def test_cli_user_ignore_flag(self, tmp_path):
        """--user-ignore CLI flag appends to system defaults."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "--project-root",
                str(tmp_path),
                "--user-ignore",
                "secret/",
                "tmp_*",
            ]
        )
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert "*.pyc" in cfg["ignore"]
        assert "secret/" in cfg["ignore"]
        assert "tmp_*" in cfg["ignore"]

    def test_cli_user_extensions_flag(self, tmp_path):
        """--user-extensions CLI flag appends to system defaults."""
        parser = build_parser()
        args = parser.parse_args(
            [
                "--project-root",
                str(tmp_path),
                "--user-extensions",
                ".vue",
                ".svelte",
            ]
        )
        delattr(args, "stdout")
        cfg = resolve_config(args)
        assert ".py" in cfg["extensions"]
        assert ".vue" in cfg["extensions"]
        assert ".svelte" in cfg["extensions"]

    def test_per_file_user_ignore_merged_independently(self, tmp_path):
        """user-ignore inside [[files]] is resolved per-file."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]

                [[tool.sphinx-source-tree.files]]
                output = "docs/out.rst"
                user-ignore = ["extra_dir"]
            """),
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        file_ignore = cfg["files"][0]["ignore"]
        assert "*.pyc" in file_ignore
        assert "extra_dir" in file_ignore

    def test_per_file_user_extensions_merged_independently(self, tmp_path):
        """user-extensions inside [[files]] is resolved per-file."""
        (tmp_path / "pyproject.toml").write_text(
            textwrap.dedent("""\
                [tool.sphinx-source-tree]

                [[tool.sphinx-source-tree.files]]
                output = "docs/out.rst"
                user-extensions = [".vue"]
            """),
            encoding="utf-8",
        )
        parser = build_parser()
        args = parser.parse_args(["--project-root", str(tmp_path)])
        delattr(args, "stdout")
        cfg = resolve_config(args)
        file_exts = cfg["files"][0]["extensions"]
        assert ".py" in file_exts
        assert ".vue" in file_exts

    def test_generate_respects_user_extensions(self, sample_project):
        """user_extensions are actually used when collecting files."""
        (sample_project / "src" / "style.vue").write_text(
            "<template></template>", encoding="utf-8"
        )
        from sphinx_source_tree import _merge_extensions

        merged = _merge_extensions(
            {
                "system_extensions": list(SYSTEM_EXTENSIONS),
                "user_extensions": [".vue"],
                "extensions": None,
            }
        )
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=merged,
            ignore=["__pycache__", "*.pyc"],
            extra_languages={".vue": "vue"},
        )
        assert "style.vue" in rst

    def test_generate_respects_user_ignore(self, sample_project):
        """user_ignore patterns are actually excluded from output."""
        from sphinx_source_tree import _merge_ignore

        merged = _merge_ignore(
            {
                "system_ignore": list(SYSTEM_IGNORE),
                "user_ignore": ["src"],
                "ignore": None,
            }
        )
        rst = generate(
            project_root=sample_project,
            output=sample_project / "docs" / "out.rst",
            extensions=[".py"],
            ignore=merged,
        )
        assert "app.py" not in rst
