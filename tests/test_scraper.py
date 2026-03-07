"""Tests for scraper.py — BaseJobScraper, JobScraper, ALLOWED_LANGUAGES."""

import pytest
import httpx

from models import Job
from scraper import ALLOWED_LANGUAGES, BaseJobScraper, JobScraper

# ---------------------------------------------------------------------------
# Sample HTML fixtures
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>
<ul>
  <li class="l-vacancy">
    <a class="vt" href="https://dou.ua/job/1">Senior\xa0Python Dev</a>
    <span class="cities">Kyiv</span>
    <span class="salary">$3\xa0000</span>
    <div class="sh-info">Some\xa0info\nhere</div>
  </li>
  <li class="l-vacancy">
    <a class="vt" href="https://dou.ua/job/2">Junior Dev</a>
  </li>
</ul>
</body></html>
"""

EMPTY_HTML = "<html><body><ul></ul></body></html>"


# ---------------------------------------------------------------------------
# ALLOWED_LANGUAGES
# ---------------------------------------------------------------------------

def test_allowed_languages_contains_basics() -> None:
    for lang in ("python", "java", "ruby", "sql"):
        assert lang in ALLOWED_LANGUAGES


# ---------------------------------------------------------------------------
# BaseJobScraper is abstract
# ---------------------------------------------------------------------------

def test_base_scraper_is_abstract() -> None:
    with pytest.raises(TypeError):
        BaseJobScraper()  # type: ignore[abstract]


# ---------------------------------------------------------------------------
# JobScraper — custom base_url
# ---------------------------------------------------------------------------

def test_custom_base_url() -> None:
    scraper = JobScraper(base_url="https://custom.example.com/")
    assert scraper.base_url == "https://custom.example.com/"


def test_default_base_url() -> None:
    scraper = JobScraper()
    assert "jobs.dou.ua" in scraper.base_url


# ---------------------------------------------------------------------------
# JobScraper.fetch_jobs — validation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_jobs_unsupported_language() -> None:
    scraper = JobScraper()
    with pytest.raises(ValueError, match="Unsupported language"):
        await scraper.fetch_jobs("brainfuck")


# ---------------------------------------------------------------------------
# JobScraper.fetch_jobs — successful parse
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_jobs_parses_html(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify parsing of a full vacancy and one with missing optional fields."""

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, text=SAMPLE_HTML, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    scraper = JobScraper()
    jobs = await scraper.fetch_jobs("python")

    assert len(jobs) == 2

    # First vacancy — all fields present, \xa0 replaced
    assert jobs[0].title == "Senior Python Dev"
    assert jobs[0].city == "Kyiv"
    assert jobs[0].salary == "$3 000"
    assert "Some info" in jobs[0].info
    assert "\n" not in jobs[0].info
    assert jobs[0].link == "https://dou.ua/job/1"

    # Second vacancy — missing city, salary, info
    assert jobs[1].title == "Junior Dev"
    assert jobs[1].city == "Місто не вказано"
    assert jobs[1].salary == "Зарплата не вказана"
    assert jobs[1].info == "Інформація не вказана"


# ---------------------------------------------------------------------------
# JobScraper.fetch_jobs — empty page
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_jobs_empty_page(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, text=EMPTY_HTML, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    scraper = JobScraper()
    jobs = await scraper.fetch_jobs("python")
    assert jobs == []


# ---------------------------------------------------------------------------
# JobScraper.fetch_jobs — non-200 status
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_jobs_non_200_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(self, url, **kwargs):
        return httpx.Response(403, text="Forbidden", request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    scraper = JobScraper()
    with pytest.raises(ValueError, match="status 403"):
        await scraper.fetch_jobs("python")


# ---------------------------------------------------------------------------
# JobScraper.fetch_jobs — missing title element
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fetch_jobs_missing_title(monkeypatch: pytest.MonkeyPatch) -> None:
    html = '<html><body><li class="l-vacancy"></li></body></html>'

    async def fake_get(self, url, **kwargs):
        return httpx.Response(200, text=html, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    scraper = JobScraper()
    jobs = await scraper.fetch_jobs("python")
    assert len(jobs) == 1
    assert jobs[0].title == "Без назви"
    assert jobs[0].link == ""
