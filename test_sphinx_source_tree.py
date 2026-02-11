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
