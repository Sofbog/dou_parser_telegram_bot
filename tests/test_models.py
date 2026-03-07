"""Tests for models.py — Job dataclass."""

from dataclasses import asdict

from models import Job


def test_job_creation() -> None:
    job = Job(title="Dev", city="Kyiv", salary="3000", info="Remote", link="https://example.com")
    assert job.title == "Dev"
    assert job.city == "Kyiv"
    assert job.salary == "3000"
    assert job.info == "Remote"
    assert job.link == "https://example.com"


def test_job_equality() -> None:
    a = Job(title="A", city="B", salary="C", info="D", link="E")
    b = Job(title="A", city="B", salary="C", info="D", link="E")
    assert a == b


def test_job_asdict() -> None:
    job = Job(title="T", city="C", salary="S", info="I", link="L")
    d = asdict(job)
    assert d == {"title": "T", "city": "C", "salary": "S", "info": "I", "link": "L"}


def test_job_slots() -> None:
    """Job uses __slots__ so arbitrary attributes cannot be set."""
    job = Job(title="T", city="C", salary="S", info="I", link="L")
    with __import__("pytest").raises(AttributeError):
        job.nonexistent = "x"  # type: ignore[attr-defined]
