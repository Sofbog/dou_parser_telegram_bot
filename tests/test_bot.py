"""Tests for bot.py — handlers, keyboard, registration."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# bot.py reads TELEGRAM_TOKEN at import time, so we must set it first.
os.environ.setdefault("TELEGRAM_TOKEN", "123456789:AABBCCDDEEFFGGHHIIJJKKLLMMNNOOPPqqr")

from aiogram.enums import ParseMode

from models import Job

import bot as bot_module
from bot import (
    SUPPORTED_LANGUAGES,
    _build_start_keyboard,
    _send_job_list,
    handle_start,
    main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_message() -> MagicMock:
    msg = MagicMock()
    msg.answer = AsyncMock()
    return msg


def _make_jobs(n: int = 2) -> list[Job]:
    return [Job(title=f"Job{i}", city="C", salary="S", info="I", link=f"https://x.ua/{i}") for i in range(n)]


# ---------------------------------------------------------------------------
# _build_start_keyboard
# ---------------------------------------------------------------------------

def test_build_keyboard_buttons_match_languages() -> None:
    """Keyboard buttons must exactly match SUPPORTED_LANGUAGES in order."""
    kb = _build_start_keyboard()
    texts = [row[0].text for row in kb.keyboard]
    assert texts == SUPPORTED_LANGUAGES


def test_build_keyboard_one_button_per_row() -> None:
    """Each language gets its own row for clear UI."""
    kb = _build_start_keyboard()
    for row in kb.keyboard:
        assert len(row) == 1


# ---------------------------------------------------------------------------
# handle_start
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_start_sends_keyboard() -> None:
    msg = _make_message()
    await handle_start(msg)

    msg.answer.assert_awaited_once()
    kwargs = msg.answer.call_args.kwargs
    assert "reply_markup" in kwargs
    # Verify the keyboard contains actual language buttons
    kb = kwargs["reply_markup"]
    texts = [row[0].text for row in kb.keyboard]
    assert texts == SUPPORTED_LANGUAGES


# ---------------------------------------------------------------------------
# _send_job_list — success with card formatting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_success() -> None:
    msg = _make_message()
    jobs = _make_jobs(3)

    with patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=jobs):
        await _send_job_list(msg, "python")

    # 1 "Очікуйте" + 3 job cards = 4 calls
    assert msg.answer.await_count == 4
    # Verify job card contains title link and city/salary labels
    first_card = msg.answer.call_args_list[1][0][0]
    assert "Job0" in first_card
    assert "Місто" in first_card
    assert "Зарплата" in first_card


# ---------------------------------------------------------------------------
# _send_job_list — empty result
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_empty() -> None:
    msg = _make_message()

    with patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=[]):
        await _send_job_list(msg, "python")

    assert msg.answer.await_count == 2  # "Очікуйте" + "Вакансій не знайдено"
    assert "не знайдено" in msg.answer.call_args_list[1][0][0]


# ---------------------------------------------------------------------------
# _send_job_list — exception handling
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_error() -> None:
    """On exception, user gets an error message and bot doesn't crash."""
    msg = _make_message()

    with patch.object(
        bot_module._job_service, "get_jobs", new_callable=AsyncMock, side_effect=RuntimeError("boom")
    ):
        await _send_job_list(msg, "python")

    assert msg.answer.await_count == 2  # "Очікуйте" + error message
    assert "помилка" in msg.answer.call_args_list[1][0][0]


# ---------------------------------------------------------------------------
# _send_job_list — Telegram rate limit sleep after 20 messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_rate_limit_sleep() -> None:
    """Bot should pause after every 20 messages to avoid Telegram rate limit."""
    msg = _make_message()
    jobs = _make_jobs(21)

    with (
        patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=jobs),
        patch("bot.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await _send_job_list(msg, "python")

    # Sleep happens at index 20 (after sending 20 cards)
    mock_sleep.assert_awaited_once_with(3)


# ---------------------------------------------------------------------------
# _send_job_list — language is lowercased
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_lowercases_language() -> None:
    """Language is passed as .lower() to the service."""
    msg = _make_message()

    with patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=[]) as mock_get:
        await _send_job_list(msg, "Python")

    mock_get.assert_awaited_once_with("python")


# ---------------------------------------------------------------------------
# _register_language_handlers — correct number of handlers
# ---------------------------------------------------------------------------

def test_language_handlers_registered() -> None:
    """Each supported language should have a registered handler + /start."""
    from bot import dp
    handler_count = len(dp.message.handlers)
    # /start + one per language
    assert handler_count >= len(SUPPORTED_LANGUAGES) + 1


# ---------------------------------------------------------------------------
# main — configures logging and starts polling
# ---------------------------------------------------------------------------

def test_main_calls_run_polling() -> None:
    with (
        patch.object(bot_module.dp, "run_polling") as mock_poll,
        patch("bot.logging.basicConfig") as mock_log_cfg,
    ):
        main()
        mock_poll.assert_called_once()
        mock_log_cfg.assert_called_once()


# ---------------------------------------------------------------------------
# Dynamic handler actually delegates to _send_job_list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dynamic_handler_delegates_to_send_job_list() -> None:
    """The closure-based handler for each language calls _send_job_list."""
    from bot import dp

    # Find any dynamic handler (name is "handler", not "handle_start")
    dynamic_handler = None
    for h in dp.message.handlers:
        if h.callback.__name__ == "handler":
            dynamic_handler = h.callback
            break
    assert dynamic_handler is not None

    msg = _make_message()
    with patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=[]):
        await dynamic_handler(msg)

    # "Очікуйте" + "Вакансій не знайдено"
    assert msg.answer.await_count == 2
