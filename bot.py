"""Telegram bot for delivering DOU job postings to users.

This script uses the aiogram library to build an asynchronous Telegram
bot. Users can select a programming language from a predefined set
and receive a list of job vacancies scraped from DOU. The scraping
logic resides in the ``scraper.py`` module and persistence logic in
``repository.py``, while this file handles all messaging
interactions.

Environment:
    The bot token must be provided via a ``config.py`` module that
    exposes a ``token`` attribute. See README.md for setup details.
"""

import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.markdown import hbold, hlink

from config import token  # type: ignore  # token defined externally

from models import Job
from repository import JSONJobRepository
from scraper import JobScraper
from service import JobService


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
    # Fetch fresh jobs and persist them via the service layer
    jobs: list[Job] = await _job_service.get_jobs(language.lower())

    for index, job in enumerate(jobs):
        card: str = (
            f"{hlink(job.title, job.link)}\n"
            f"{hbold('Місто: ')}{job.city}\n"
            f"{hbold('Зарплата: ')}{job.salary}"
        )
        if index % 20 == 0 and index != 0:
            # Respect Telegram rate limits by pausing between batches
            await asyncio.sleep(3)
        await message.answer(card, parse_mode=ParseMode.HTML)


@dp.message(lambda m: m.text == "Python")
async def handle_python(message: types.Message) -> None:
    """Respond to the 'Python' button by sending Python vacancies."""
    await _send_job_list(message, "python")


@dp.message(lambda m: m.text == "Java")
async def handle_java(message: types.Message) -> None:
    """Respond to the 'Java' button by sending Java vacancies."""
    await _send_job_list(message, "java")


@dp.message(lambda m: m.text == "Ruby")
async def handle_ruby(message: types.Message) -> None:
    """Respond to the 'Ruby' button by sending Ruby vacancies."""
    await _send_job_list(message, "ruby")


@dp.message(lambda m: m.text == "SQL")
async def handle_sql(message: types.Message) -> None:
    """Respond to the 'SQL' button by sending SQL vacancies."""
    await _send_job_list(message, "sql")


def main() -> None:
    """Entry point to start polling for Telegram updates."""
    dp.run_polling(bot)


if __name__ == "__main__":
    main()
