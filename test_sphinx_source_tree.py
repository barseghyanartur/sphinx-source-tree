from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from sphinx_source_tree import (
    DEFAULTS,
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

    # ── _validate_file_options ────────────────────────────────────────

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

    # ── generate() with file_options ─────────────────────────────────

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

    # ── pyproject.toml integration ────────────────────────────────────

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
