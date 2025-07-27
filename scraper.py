"""Web scraper utilities for retrieving job vacancies from DOU.

This module defines the :class:`JobScraper`, which encapsulates
the logic for downloading and parsing job listings from the DOU
website. By wrapping the scraping functionality in a class, we
adhere to the single‑responsibility principle and make it easier
to substitute alternative scraping implementations if the data
source changes.

The scraper uses the `httpx` library to perform asynchronous
HTTP requests and `BeautifulSoup` for HTML parsing. Each vacancy
is converted into an instance of :class:`Job` defined in
``models.py``.
"""

import httpx
from bs4 import BeautifulSoup

from models import Job


class JobScraper:
    """Scraper for extracting job listings from the DOU website.

    Instances of this class can fetch job vacancies for a given
    programming language category. The base URL can be customised
    via the constructor to facilitate testing or alternate data
    sources. Parsing is performed using BeautifulSoup to extract
    title, city, salary, additional info and a link for each
    vacancy. A new HTTP client is created for each request to
    simplify resource management.
    """

    _BASE_URL: str = "https://jobs.dou.ua/vacancies/?category="
    _HEADERS: dict[str, str] = {
        "Accept": "*/*",
        # A realistic User‑Agent header helps avoid being blocked by the server.
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/95.0.4638.69 Safari/537.36"
        ),
    }

    def __init__(self, base_url: str | None = None) -> None:
        """Initialise a new :class:`JobScraper` instance.

        Args:
            base_url: Optional override for the DOU vacancy listings URL.
                If omitted, a default base URL targeting DOU is used.
        """
        self.base_url: str = base_url or self._BASE_URL

    async def fetch_jobs(self, language: str) -> list[Job]:
        """Fetch and parse job vacancies for the specified language.

        This method builds the request URL by appending the given
        ``language`` to the base URL, performs an asynchronous GET
        request, and then parses the HTML response. Each vacancy is
        converted into a :class:`Job` object. If the remote server
        returns a non‑200 status code, a :class:`ValueError` is
        raised.

        Args:
            language: Lower‑case programming language slug (e.g.
                ``"python"``, ``"java"``) used to filter vacancies.

        Returns:
            A list of :class:`Job` instances representing the
            retrieved vacancies.

        Raises:
            ValueError: If the HTTP request fails or returns an
                unexpected status code.
        """
        url: str = f"{self.base_url}{language}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=self._HEADERS)
        if response.status_code != 200:
            raise ValueError(f"Failed to retrieve data: status {response.status_code}")
        html: str = response.text

        soup = BeautifulSoup(html, "lxml")
        jobs: list[Job] = []
        for item in soup.find_all("li", class_="l-vacancy"):
            title_elem = item.find("a", class_="vt")
            title: str = (
                title_elem.get_text(strip=True).replace("\xa0", " ") if title_elem else "Без назви"
            )
            link: str = title_elem.get("href") if title_elem else ""

            city_elem = item.find("span", class_="cities")
            city: str = city_elem.get_text(strip=True) if city_elem else "Місто не вказано"

            salary_elem = item.find("span", class_="salary")
            salary: str = (
                salary_elem.get_text(strip=True).replace("\xa0", " ")
                if salary_elem
                else "Зарплата не вказана"
            )

            info_elem = item.find("div", class_="sh-info")
            info: str = (
                info_elem.get_text(strip=True).replace("\xa0", " ").replace("\n", "")
                if info_elem
                else "Інформація не вказана"
            )

            jobs.append(Job(title=title, city=city, salary=salary, info=info, link=link))
        return jobs
