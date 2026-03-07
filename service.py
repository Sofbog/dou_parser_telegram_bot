"""Service layer orchestrating scraping and persistence operations.

The :class:`JobService` coordinates between a :class:`JobScraper`
and a :class:`JobRepository` to fetch and save job listings. By
delegating responsibilities to these collaborators, this service
adheres to the single‑responsibility principle and enables easy
substitution of alternate implementations for scraping or storage.
"""

import asyncio
import logging
import time

from models import Job
from repository import JobRepository
from scraper import JobScraper

logger = logging.getLogger(__name__)

_CACHE_TTL_SECONDS: int = 30 * 60  # 30 minutes
_MAX_CONCURRENT_REQUESTS: int = 3


class JobService:
    """Coordinate scraping and persistence of job listings.

    This class encapsulates the workflow of obtaining job data from
    a scraper and storing it via a repository. It provides a single
    entry point for consumers (such as a bot interface) to retrieve
    fresh listings and persist them. Results are cached in memory
    for ``_CACHE_TTL_SECONDS`` to avoid redundant scraping. A
    semaphore limits concurrent requests to DOU.
    """

    def __init__(self, scraper: JobScraper, repository: JobRepository) -> None:
        """Create a new service with its dependencies injected.

        Args:
            scraper: An instance capable of fetching job listings.
            repository: An instance capable of saving job listings.
        """
        self._scraper: JobScraper = scraper
        self._repository: JobRepository = repository
        self._cache: dict[str, tuple[float, list[Job]]] = {}
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(_MAX_CONCURRENT_REQUESTS)

    async def get_jobs(self, language: str, file_path: str | None = None) -> list[Job]:
        """Fetch jobs for a language and persist them using the repository.

        Returns cached results if available and not expired. Otherwise
        fetches fresh data (limited by semaphore) and updates the cache.

        Args:
            language: Lower‑case language slug (e.g. ``"python"``).
            file_path: Optional destination for persisted data. If
                omitted, a default chosen by the repository is used.

        Returns:
            A list of :class:`Job` instances representing the
            job listings for the requested language.
        """
        cached = self._cache.get(language)
        if cached:
            cached_at, jobs = cached
            if time.monotonic() - cached_at < _CACHE_TTL_SECONDS:
                logger.info("Cache hit for language=%s (%d jobs)", language, len(jobs))
                return jobs

        logger.info("Fetching fresh jobs for language=%s", language)
        async with self._semaphore:
            jobs = await self._scraper.fetch_jobs(language)

        await self._repository.save_jobs(jobs, file_path)
        self._cache[language] = (time.monotonic(), jobs)
        return jobs
