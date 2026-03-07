"""Tests for service.py — JobService with caching and semaphore."""

import asyncio
import time
from collections.abc import Iterable
from unittest.mock import AsyncMock

import pytest

from models import Job
from repository import JobRepository
from scraper import BaseJobScraper
from service import JobService, _CACHE_TTL_SECONDS, _MAX_CONCURRENT_REQUESTS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_jobs(n: int = 2) -> list[Job]:
    return [Job(title=f"Job{i}", city="C", salary="S", info="I", link="L") for i in range(n)]


class FakeScraper(BaseJobScraper):
    def __init__(self, jobs: list[Job] | None = None) -> None:
        self.jobs = _make_jobs() if jobs is None else jobs
        self.call_count = 0

    async def fetch_jobs(self, language: str) -> list[Job]:
        self.call_count += 1
        return self.jobs


class FakeRepository(JobRepository):
    def __init__(self) -> None:
        self.saved: list[tuple[list[Job], str | None]] = []

    async def save_jobs(self, jobs: Iterable[Job], file_path: str | None = None) -> None:
        self.saved.append((list(jobs), file_path))


# ---------------------------------------------------------------------------
# Basic fetch & persist
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_jobs_fetches_and_saves() -> None:
    scraper = FakeScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    jobs = await service.get_jobs("python")

    assert len(jobs) == 2
    assert scraper.call_count == 1
    assert len(repo.saved) == 1
    assert repo.saved[0][1] is None  # default file_path


@pytest.mark.asyncio
async def test_get_jobs_custom_file_path() -> None:
    scraper = FakeScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    await service.get_jobs("python", file_path="/tmp/custom.json")
    assert repo.saved[0][1] == "/tmp/custom.json"


# ---------------------------------------------------------------------------
# Caching
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_cache_hit_avoids_scraping() -> None:
    scraper = FakeScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    await service.get_jobs("python")
    await service.get_jobs("python")

    assert scraper.call_count == 1  # second call served from cache
    assert len(repo.saved) == 1    # no second save


@pytest.mark.asyncio
async def test_cache_is_per_language() -> None:
    scraper = FakeScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    await service.get_jobs("python")
    await service.get_jobs("java")

    assert scraper.call_count == 2


@pytest.mark.asyncio
async def test_cache_expires(monkeypatch: pytest.MonkeyPatch) -> None:
    scraper = FakeScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    await service.get_jobs("python")
    assert scraper.call_count == 1

    # Simulate time passing beyond TTL
    cached_at = service._cache["python"][0]
    service._cache["python"] = (cached_at - _CACHE_TTL_SECONDS - 1, service._cache["python"][1])

    await service.get_jobs("python")
    assert scraper.call_count == 2


# ---------------------------------------------------------------------------
# Semaphore limits concurrency
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_semaphore_limits_concurrency() -> None:
    max_concurrent = 0
    current_concurrent = 0

    class SlowScraper(BaseJobScraper):
        async def fetch_jobs(self, language: str) -> list[Job]:
            nonlocal max_concurrent, current_concurrent
            current_concurrent += 1
            if current_concurrent > max_concurrent:
                max_concurrent = current_concurrent
            await asyncio.sleep(0.05)
            current_concurrent -= 1
            return _make_jobs(1)

    scraper = SlowScraper()
    repo = FakeRepository()
    service = JobService(scraper, repo)

    # Launch more tasks than the semaphore allows.
    # Each needs a unique language to bypass cache.
    languages = [f"lang{i}" for i in range(_MAX_CONCURRENT_REQUESTS + 3)]
    await asyncio.gather(*(service.get_jobs(lang) for lang in languages))

    assert max_concurrent <= _MAX_CONCURRENT_REQUESTS


# ---------------------------------------------------------------------------
# Empty result is cached too
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_result_is_cached() -> None:
    scraper = FakeScraper(jobs=[])
    repo = FakeRepository()
    service = JobService(scraper, repo)

    result1 = await service.get_jobs("python")
    result2 = await service.get_jobs("python")

    assert result1 == []
    assert result2 == []
    assert scraper.call_count == 1
