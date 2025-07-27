"""Service layer orchestrating scraping and persistence operations.

The :class:`JobService` coordinates between a :class:`JobScraper`
and a :class:`JobRepository` to fetch and save job listings. By
delegating responsibilities to these collaborators, this service
adheres to the single‑responsibility principle and enables easy
substitution of alternate implementations for scraping or storage.
"""

from models import Job
from repository import JobRepository
from scraper import JobScraper


class JobService:
    """Coordinate scraping and persistence of job listings.

    This class encapsulates the workflow of obtaining job data from
    a scraper and storing it via a repository. It provides a single
    entry point for consumers (such as a bot interface) to retrieve
    fresh listings and persist them. Dependency inversion is
    achieved by accepting any objects implementing the required
    interfaces for scraping and persistence.
    """

    def __init__(self, scraper: JobScraper, repository: JobRepository) -> None:
        """Create a new service with its dependencies injected.

        Args:
            scraper: An instance capable of fetching job listings.
            repository: An instance capable of saving job listings.
        """
        self._scraper: JobScraper = scraper
        self._repository: JobRepository = repository

    async def get_jobs(self, language: str, file_path: str | None = None) -> list[Job]:
        """Fetch jobs for a language and persist them using the repository.

        The jobs are returned to the caller after they have been saved
        via the repository. The destination file path may be provided
        to influence where the repository writes its data.

        Args:
            language: Lower‑case language slug (e.g. ``"python"``).
            file_path: Optional destination for persisted data. If
                omitted, a default chosen by the repository is used.

        Returns:
            A list of :class:`Job` instances representing the fresh
            job listings for the requested language.
        """
        jobs: list[Job] = await self._scraper.fetch_jobs(language)
        await self._repository.save_jobs(jobs, file_path)
        return jobs
