"""Domain models for the DOU parser bot.

This module defines simple data structures used throughout the
application. The primary model is :class:`Job`, which represents
information about a single job vacancy scraped from the DOU website.
"""

from dataclasses import dataclass


@dataclass(slots=True)
class Job:
    """A data container representing a single job listing.

    Args:
        title: The job title as displayed on the DOU listing.
        city: The city or location of the job.
        salary: The salary range or indication, if provided.
        info: Additional information or description snippet.
        link: A URL linking to the full job description on DOU.
    """

    title: str
    city: str
    salary: str
    info: str
    link: str
