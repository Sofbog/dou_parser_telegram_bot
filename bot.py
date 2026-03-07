"""Telegram bot for delivering DOU job postings to users.

This script uses the aiogram library to build an asynchronous Telegram
bot. Users can select a programming language from a predefined set
and receive a list of job vacancies scraped from DOU. The scraping
logic resides in the ``scraper.py`` module and persistence logic in
``repository.py``, while this file handles all messaging
interactions.

Environment:
    The bot token must be provided via a ``TELEGRAM_TOKEN`` environment
    variable (loaded from ``.env``). See README.md for setup details.
"""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold, hlink
from dotenv import load_dotenv

from models import Job
from repository import JSONJobRepository
from scraper import JobScraper
from service import JobService

logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Get token from environment variable
token = os.getenv("TELEGRAM_TOKEN")
if not token:
    raise ValueError("TELEGRAM_TOKEN environment variable is not set")

bot = Bot(token=token)
dp: Dispatcher = Dispatcher()

# Initialise service layer with its dependencies. Using local imports
# avoids circular references and permits dependency injection for testing.
_job_service: JobService = JobService(JobScraper(), JSONJobRepository())


def _build_start_keyboard() -> ReplyKeyboardMarkup:
    """Construct the reply keyboard for language selection.

    Returns:
        ReplyKeyboardMarkup: A keyboard markup with language options.
    """
    buttons: list[list[KeyboardButton]] = [
        [KeyboardButton(text="Java")],
        [KeyboardButton(text="Python")],
        [KeyboardButton(text="Ruby")],
        [KeyboardButton(text="SQL")],
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


@dp.message(Command("start"))
async def handle_start(message: types.Message) -> None:
    """Handle the ``/start`` command by displaying language options.

    Args:
        message: Incoming Telegram message object.
    """
    keyboard = _build_start_keyboard()
    await message.answer(
        "Вибери мову програмування яка тебе цікавить", reply_markup=keyboard
    )


async def _send_job_list(message: types.Message, language: str) -> None:
    """Fetch job postings and send them to the user.

    This helper function notifies the user that processing has begun,
    retrieves the list of vacancies via the :class:`JobService`,
    persists the data using the configured repository (defaulting to
    ``work.json``), and then iterates over the results to send each
    vacancy as a formatted message. To respect Telegram rate limits
    the function pauses briefly after sending every 20 messages.

    Args:
        message: Telegram message from the user requesting jobs.
        language: Programming language category to search on DOU.
    """
    await message.answer("Очікуйте...", parse_mode=ParseMode.HTML)

    try:
        jobs: list[Job] = await _job_service.get_jobs(language.lower())
    except Exception:
        logger.exception("Failed to fetch jobs for language=%s", language)
        await message.answer(
            "Виникла помилка при отриманні вакансій. Спробуйте пізніше.",
            parse_mode=ParseMode.HTML,
        )
        return

    if not jobs:
        await message.answer("Вакансій не знайдено.", parse_mode=ParseMode.HTML)
        return

    for index, job in enumerate(jobs):
        card: str = (
            f"{hlink(job.title, job.link)}\n"
            f"{hbold('Місто: ')}{job.city}\n"
            f"{hbold('Зарплата: ')}{job.salary}"
        )
        if index % 20 == 0 and index != 0:
            await asyncio.sleep(3)
        await message.answer(card, parse_mode=ParseMode.HTML)


@dp.message(F.text == "Python")
async def handle_python(message: types.Message) -> None:
    """Respond to the 'Python' button by sending Python vacancies."""
    await _send_job_list(message, "python")


@dp.message(F.text == "Java")
async def handle_java(message: types.Message) -> None:
    """Respond to the 'Java' button by sending Java vacancies."""
    await _send_job_list(message, "java")


@dp.message(F.text == "Ruby")
async def handle_ruby(message: types.Message) -> None:
    """Respond to the 'Ruby' button by sending Ruby vacancies."""
    await _send_job_list(message, "ruby")


@dp.message(F.text == "SQL")
async def handle_sql(message: types.Message) -> None:
    """Respond to the 'SQL' button by sending SQL vacancies."""
    await _send_job_list(message, "sql")


def main() -> None:
    """Entry point to start polling for Telegram updates."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger.info("Bot starting...")
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
