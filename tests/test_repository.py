"""Tests for repository.py — JobRepository, JSONJobRepository."""

import json

import pytest

from models import Job
from repository import JSONJobRepository, JobRepository, _DEFAULT_FILE


# ---------------------------------------------------------------------------
# JobRepository is abstract
# ---------------------------------------------------------------------------

def test_job_repository_is_abstract() -> None:
    with pytest.raises(TypeError):
        JobRepository()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# _DEFAULT_FILE is an absolute path
# ---------------------------------------------------------------------------

def test_default_file_is_absolute() -> None:
    import os
    assert os.path.isabs(_DEFAULT_FILE)
    assert _DEFAULT_FILE.endswith("work.json")


# ---------------------------------------------------------------------------
# JSONJobRepository.save_jobs — writes correct JSON
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_jobs_writes_json(tmp_path) -> None:
    path = str(tmp_path / "out.json")
    repo = JSONJobRepository()
    jobs = [
        Job(title="A", city="B", salary="C", info="D", link="E"),
        Job(title="F", city="G", salary="H", info="I", link="J"),
    ]
    await repo.save_jobs(jobs, file_path=path)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert len(data) == 2
    assert data[0]["title"] == "A"
    assert data[1]["link"] == "J"


# ---------------------------------------------------------------------------
# JSONJobRepository.save_jobs — empty list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_jobs_empty_list(tmp_path) -> None:
    path = str(tmp_path / "empty.json")
    repo = JSONJobRepository()
    await repo.save_jobs([], file_path=path)

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    assert data == []


# ---------------------------------------------------------------------------
# JSONJobRepository.save_jobs — default path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_jobs_default_path(monkeypatch, tmp_path) -> None:
    """When file_path is None, uses _DEFAULT_FILE."""
    fake_default = str(tmp_path / "work.json")
    import repository
    monkeypatch.setattr(repository, "_DEFAULT_FILE", fake_default)

    repo = JSONJobRepository()
    await repo.save_jobs([Job(title="T", city="C", salary="S", info="I", link="L")])

    with open(fake_default, encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1


# ---------------------------------------------------------------------------
# JSONJobRepository.save_jobs — unicode
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_save_jobs_unicode(tmp_path) -> None:
    path = str(tmp_path / "unicode.json")
    repo = JSONJobRepository()
    await repo.save_jobs(
        [Job(title="Розробник", city="Київ", salary="₴50000", info="Віддалено", link="https://x.ua")],
        file_path=path,
    )

    with open(path, encoding="utf-8") as f:
        content = f.read()

    # ensure_ascii=False means Cyrillic is written directly
    assert "Розробник" in content
    assert "Київ" in content
