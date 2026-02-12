from __future__ import annotations

from typing import TYPE_CHECKING, Generator

import pytest

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture
def safe_test_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[Path, None, None]:
    """Change to tmp_path for safe execution of documentation tests.

    :param tmp_path: Temporary directory fixture from pytest
    :param monkeypatch: Monkeypatch fixture from pytest
    :yields: Path
    :ytype: Path
    """
    monkeypatch.chdir(tmp_path)
    (tmp_path / "docs").mkdir()
    yield tmp_path
