"""
sphinx-source-tree
==================
Generate a reStructuredText file containing an ASCII project tree
and ``literalinclude`` directives for every source file.

Reads defaults from ``[tool.sphinx-source-tree]`` in ``pyproject.toml``.
CLI arguments always take precedence.
"""

from __future__ import annotations

import argparse
import fnmatch
import os
import sys
from pathlib import Path
from typing import Any

__title__ = "sphinx-source-tree"
__version__ = "0.1"
__author__ = "Artur Barseghyan <artur.barseghyan@gmail.com>"
__copyright__ = "2026 Artur Barseghyan"
__license__ = "MIT"
__all__ = (
    "build_parser",
    "build_tree",
    "collect_files",
    "detect_language",
    "generate",
    "load_config",
    "main",
    "resolve_config",
)

DEFAULTS: dict[str, Any] = {
    "project_root": ".",
    "depth": 10,
    "output": "docs/source_tree.rst",
    "extensions": [
        ".js",
        ".json",
        ".md",
        ".py",
        ".rst",
        ".toml",
        ".yaml",
        ".yml",
    ],
    "ignore": [
        "__pycache__",
        "*.pyc",
        "*.pyo",
        "*.py,cover",
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".nox",
        ".venv",
        "venv",
        "env",
        "*.egg-info",
        "dist",
        "build",
        "node_modules",
        ".mypy_cache",
        ".pytest_cache",
        ".coverage",
        "htmlcov",
        ".idea",
        ".vscode",
        ".DS_Store",
        "Thumbs.db",
        ".ruff_cache",
        ".coverage.*",
        ".secrets.baseline",
    ],
    "whitelist": [],
    "include_all": True,
    "title": "Project source-tree",
    "linenos": False,
    "extra_languages": {},
}

LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".pyi": "python",
    ".pyx": "cython",
    ".js": "javascript",
    ".mjs": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "jsx",
    ".java": "java",
    ".kt": "kotlin",
    ".md": "markdown",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".rst": "rst",
    ".toml": "toml",
    ".cfg": "ini",
    ".ini": "ini",
    ".html": "html",
    ".jinja": "jinja",
    ".jinja2": "jinja",
    ".css": "css",
    ".scss": "scss",
    ".sass": "sass",
    ".less": "less",
    ".sql": "sql",
    ".rb": "ruby",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c",
    ".hpp": "cpp",
    ".xml": "xml",
    ".r": "r",
    ".R": "r",
    ".lua": "lua",
    ".php": "php",
    ".swift": "swift",
    ".dockerfile": "dockerfile",
    ".tf": "hcl",
    ".graphql": "graphql",
    ".proto": "protobuf",
    ".makefile": "makefile",
}


# ── config ───────────────────────────────────────────────────────────


def load_config(project_root: Path) -> dict[str, Any]:
    """Load ``[tool.sphinx-source-tree]`` from *pyproject.toml*."""
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return {}
    try:
        if sys.version_info >= (3, 11):
            import tomllib
        else:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(pyproject_path, "rb") as fh:
            data = tomllib.load(fh)
        return data.get("tool", {}).get("sphinx-source-tree", {})
    except Exception:
        return {}


def resolve_config(
    cli_ns: argparse.Namespace,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Merge *defaults* < *pyproject.toml* < *CLI arguments*.

    Only CLI values that were explicitly provided (not ``None``) override.
    """
    cfg = dict(defaults or DEFAULTS)

    # Determine project root first (needed to locate pyproject.toml)
    project_root = Path(
        cli_ns.project_root
        if cli_ns.project_root is not None
        else cfg.get("project_root", ".")
    ).resolve()

    # Layer 2: pyproject.toml
    file_cfg = load_config(project_root)
    for key, val in file_cfg.items():
        norm = key.replace("-", "_")
        if norm != "project_root":
            cfg[norm] = val

    # Layer 3: explicit CLI args
    cfg.update(
        {
            k: v
            for k, v in vars(cli_ns).items()
            if v is not None and k != "project_root"
        }
    )

    cfg["project_root"] = str(project_root)
    return cfg


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------


def _is_ignored(rel_path: str, name: str, patterns: list[str]) -> bool:
    """Match against both the full relative path and the bare name.

    For each pattern:
      - If it contains '/', match only against the full path (with wildcards
        allowed)
      - Otherwise, match against any path component (e.g., dir/file → matches
        name, or full path)
    """
    # Normalize path separators to '/'
    rel_path = rel_path.replace(os.sep, "/")
    name_parts = rel_path.split("/")

    for pat in patterns:
        # Normalize pattern separators (e.g. "dir/*.pyc" → "dir/*.pyc")
        pat = pat.replace(os.sep, "/")

        # If pattern contains '/', treat as glob against *entire path*
        if "/" in pat:
            if fnmatch.fnmatch(rel_path, pat):
                return True
        else:
            # Otherwise, match against any path component (dir/file.py →
            # matches "file.py")
            # or match against the *relative path* (e.g., "__pycache__/foo"
            # matches "*__pycache__*")
            if any(fnmatch.fnmatch(part, pat) for part in name_parts):
                return True
            # Also try full path with glob: e.g. pat="*.pyc" should
            # match "foo.pyc" anywhere
            if fnmatch.fnmatch(rel_path, f"*{pat}*") or fnmatch.fnmatch(
                rel_path, f"*{pat}"
            ):
                return True

    return False


def _matches_whitelist(rel_path: str, whitelist: list[str]) -> bool:
    for w in whitelist:
        w = w.strip("/")
        if rel_path == w or rel_path.startswith(w + "/"):
            return True
    return False


def _should_show_dir(rel_path: str, whitelist: list[str]) -> bool:
    """True when the directory is whitelisted *or* is an ancestor of one."""
    if _matches_whitelist(rel_path, whitelist):
        return True
    return any(w.strip("/").startswith(rel_path + "/") for w in whitelist)


# ----------------------------------------------------------------------------
# Core API
# ----------------------------------------------------------------------------


def detect_language(
    path: Path,
    extra: dict[str, str] | None = None,
) -> str:
    """Map a file suffix to its Sphinx highlight language string."""
    merged = {**LANGUAGE_MAP, **(extra or {})}
    return merged.get(path.suffix, "")


def build_tree(
    path: Path,
    *,
    max_depth: int,
    ignore: list[str],
    whitelist: list[str],
    include_all: bool,
    root: Path,
    prefix: str = "",
) -> str:
    """Return an ASCII directory tree for *path* (recursive).

    Entries are filtered *before* connectors are assigned so that the
    last visible entry always receives ``└──``.
    """
    if max_depth < 0:
        return ""

    entries = sorted(
        path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
    )

    visible: list[Path] = []
    for entry in entries:
        rel = entry.relative_to(root).as_posix()
        if _is_ignored(rel, entry.name, ignore):
            continue
        if not include_all and whitelist:
            if entry.is_dir():
                if not _should_show_dir(rel, whitelist):
                    continue
            elif not _matches_whitelist(rel, whitelist):
                continue
        visible.append(entry)

    lines: list[str] = []
    for idx, entry in enumerate(visible):
        is_last = idx == len(visible) - 1
        connector = "\u2514\u2500\u2500 " if is_last else "\u251c\u2500\u2500 "
        lines.append(f"{prefix}{connector}{entry.name}")
        if entry.is_dir():
            extension = "    " if is_last else "\u2502   "
            sub = build_tree(
                entry,
                max_depth=max_depth - 1,
                ignore=ignore,
                whitelist=whitelist,
                include_all=include_all,
                root=root,
                prefix=prefix + extension,
            )
            if sub:
                lines.extend(sub.splitlines())

    return "\n".join(lines)


def collect_files(
    root: Path,
    *,
    extensions: list[str],
    ignore: list[str],
    whitelist: list[str],
    include_all: bool,
) -> list[Path]:
    """Return a sorted list of files eligible for ``literalinclude``."""
    result: list[Path] = []
    for fp in sorted(root.rglob("*")):
        if not fp.is_file() or fp.suffix not in extensions:
            continue
        rel = fp.relative_to(root).as_posix()
        if _is_ignored(rel, fp.name, ignore):
            continue
        if (
            not include_all
            and whitelist
            and not _matches_whitelist(rel, whitelist)
        ):
            continue
        result.append(fp)
    return result


def generate(
    project_root: Path | str = ".",
    output: Path | str = "docs/source_tree.rst",
    *,
    depth: int = 10,
    extensions: list[str] | None = None,
    ignore: list[str] | None = None,
    whitelist: list[str] | None = None,
    include_all: bool = True,
    title: str = "Project source-tree",
    linenos: bool = False,
    extra_languages: dict[str, str] | None = None,
) -> str:
    """Build the full ``.rst`` document and return it as a string.

    Parameters
    ----------
    project_root:
        Path to the project directory.
    output:
        Destination ``.rst`` path (used to compute relative
        ``literalinclude`` paths, **not** written by this function).
    depth:
        Maximum tree depth.
    extensions:
        File suffixes to include via ``literalinclude``.
    ignore:
        Glob patterns to skip (matched against both relative path and
        file name).
    whitelist:
        Directories to restrict to (ignored when *include_all* is true).
    include_all:
        Bypass the whitelist.
    title:
        RST section title.
    linenos:
        Add ``:linenos:`` to every ``literalinclude``.
    extra_languages:
        Additional ``{suffix: language}`` mappings merged on top of the
        built-in ``LANGUAGE_MAP``.
    """
    root = Path(project_root).resolve()
    output_dir = Path(output).resolve().parent
    _extensions = (
        extensions if extensions is not None else list(DEFAULTS["extensions"])
    )
    _ignore = ignore if ignore is not None else list(DEFAULTS["ignore"])
    _whitelist = (
        whitelist if whitelist is not None else list(DEFAULTS["whitelist"])
    )

    underline = "=" * len(title)
    header = (
        f"{title}\n"
        f"{underline}\n"
        f"\n"
        f"Below is the layout of the project (to {depth} levels), "
        f"followed by\nthe contents of each key file.\n"
        f"\n"
        f".. code-block:: text\n"
        f"   :caption: Project directory layout\n"
        f"\n"
        f"   {root.name}/"
    )

    tree = build_tree(
        root,
        max_depth=depth,
        ignore=_ignore,
        whitelist=_whitelist,
        include_all=include_all,
        root=root,
        prefix="   ",
    )

    parts: list[str] = [header, tree, ""]

    files = collect_files(
        root,
        extensions=_extensions,
        ignore=_ignore,
        whitelist=_whitelist,
        include_all=include_all,
    )
    for fp in files:
        rel = fp.relative_to(root).as_posix()
        include_path = os.path.relpath(fp, output_dir).replace(os.sep, "/")
        lang = detect_language(fp, extra_languages)
        section_underline = "-" * len(rel)
        block: list[str] = [
            rel,
            section_underline,
            "",
            f".. literalinclude:: {include_path}",
        ]
        if lang:
            block.append(f"   :language: {lang}")
        block.append(f"   :caption: {rel}")
        if linenos:
            block.append("   :linenos:")
        block.append("")
        parts.extend(block)

    return "\n".join(parts)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Create the argument parser (exposed for documentation / testing)."""
    p = argparse.ArgumentParser(
        prog="sphinx-source-tree",
        description=(
            "Generate a .rst file with an ASCII project tree "
            "and literalinclude blocks for every source file."
        ),
    )
    p.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    p.add_argument(
        "-p",
        "--project-root",
        type=Path,
        default=None,
        help="Project directory (default: .)",
    )
    p.add_argument(
        "-d",
        "--depth",
        type=int,
        default=None,
        help="Max tree depth (default: 10)",
    )
    p.add_argument(
        "-o",
        "--output",
        default=None,
        help="Output .rst path (default: docs/source_tree.rst)",
    )
    p.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        default=None,
        metavar="EXT",
        help="File extensions to include (default: .py .md .js .rst)",
    )
    p.add_argument(
        "-i",
        "--ignore",
        nargs="+",
        default=None,
        metavar="PAT",
        help="Glob patterns to ignore",
    )
    p.add_argument(
        "-w",
        "--whitelist",
        nargs="+",
        default=None,
        metavar="DIR",
        help="Only include these directories (ignored when --include-all)",
    )
    p.add_argument(
        "--include-all",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Include everything regardless of whitelist",
    )
    p.add_argument(
        "-t",
        "--title",
        default=None,
        help='RST section title (default: "Project source-tree")',
    )
    p.add_argument(
        "--linenos",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Add :linenos: to literalinclude directives",
    )
    p.add_argument(
        "--stdout",
        action="store_true",
        default=None,
        help="Print to stdout instead of writing to a file",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``sphinx-source-tree`` command."""
    parser = build_parser()
    args = parser.parse_args(argv)

    stdout = args.stdout
    delattr(args, "stdout")

    cfg = resolve_config(args)

    content = generate(
        project_root=cfg["project_root"],
        output=cfg.get("output", DEFAULTS["output"]),
        depth=cfg.get("depth", DEFAULTS["depth"]),
        extensions=cfg.get("extensions"),
        ignore=cfg.get("ignore"),
        whitelist=cfg.get("whitelist"),
        include_all=cfg.get("include_all", DEFAULTS["include_all"]),
        title=cfg.get("title", DEFAULTS["title"]),
        linenos=cfg.get("linenos", DEFAULTS["linenos"]),
        extra_languages=cfg.get("extra_languages"),
    )

    if stdout:
        sys.stdout.write(content)
    else:
        out_path = Path(cfg.get("output", DEFAULTS["output"]))
        if not out_path.is_absolute():
            out_path = Path.cwd() / out_path
        out_path = out_path.resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
