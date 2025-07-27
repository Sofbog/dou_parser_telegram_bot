"""Repository abstractions for persisting job data.

This module defines an abstract base class that specifies the
interface for storing job listings. Concrete implementations can
persist data to different back ends, such as a local JSON file or a
database. Separating persistence logic from scraping and business
logic promotes adherence to the single‑responsibility principle and
facilitates testing and future extensions.
"""

import json
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import asdict

import aiofiles
from models import Job


class JobRepository(ABC):
    """Abstract base class describing how to persist job listings.

    Concrete subclasses must implement the :meth:`save_jobs` method
    according to their storage medium. This abstraction allows the
    application to depend on a stable interface rather than a
    particular storage technology, in line with the dependency
    inversion principle.
    """

    @abstractmethod
    async def save_jobs(self, jobs: Iterable[Job], file_path: str | None = None) -> None:
        """Persist a collection of jobs to the underlying storage.

        Args:
            jobs: An iterable of :class:`Job` instances to persist.
            file_path: Optional path hint for the storage destination.
                Concrete implementations may interpret this argument
                differently or ignore it altogether.
        """
        raise NotImplementedError


class JSONJobRepository(JobRepository):
    """Repository that writes job listings to a JSON file on disk.

    The jobs are serialised into a list of dictionaries using the
    dataclass fields. This implementation performs asynchronous
    file I/O using aiofiles, ensuring non-blocking behavior.
    """

    async def save_jobs(self, jobs: Iterable[Job], file_path: str | None = None) -> None:
        """Serialise the jobs to JSON and write them to ``file_path``.

        Args:
            jobs: An iterable of :class:`Job` objects to be saved.
            file_path: Destination filename; defaults to ``"work.json"``
                if omitted or ``None``.
        """
        path: str = file_path or "work.json"
        # Convert dataclass instances to dictionaries for JSON serialisation
        data: list[dict] = [asdict(job) for job in jobs]
        async with aiofiles.open(path, "w", encoding="utf-8") as file:
            await file.write(json.dumps(data, ensure_ascii=False, indent=2))