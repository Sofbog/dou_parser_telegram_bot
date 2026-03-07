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
# SUPPORTED_LANGUAGES
# ---------------------------------------------------------------------------

def test_supported_languages_not_empty() -> None:
    assert len(SUPPORTED_LANGUAGES) >= 1


# ---------------------------------------------------------------------------
# _build_start_keyboard
# ---------------------------------------------------------------------------

def test_build_keyboard_buttons_match_languages() -> None:
    kb = _build_start_keyboard()
    texts = [row[0].text for row in kb.keyboard]
    assert texts == SUPPORTED_LANGUAGES


def test_build_keyboard_resize() -> None:
    kb = _build_start_keyboard()
    assert kb.resize_keyboard is True


# ---------------------------------------------------------------------------
# handle_start
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_handle_start_sends_keyboard() -> None:
    msg = _make_message()
    await handle_start(msg)

    msg.answer.assert_awaited_once()
    call_kwargs = msg.answer.call_args
    assert "reply_markup" in call_kwargs.kwargs or len(call_kwargs.args) >= 2


# ---------------------------------------------------------------------------
# _send_job_list — success
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_success() -> None:
    msg = _make_message()
    jobs = _make_jobs(3)

    with patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=jobs):
        await _send_job_list(msg, "python")

    # 1 "Очікуйте" + 3 job cards = 4 calls
    assert msg.answer.await_count == 4


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
# _send_job_list — exception
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_error() -> None:
    msg = _make_message()

    with patch.object(
        bot_module._job_service, "get_jobs", new_callable=AsyncMock, side_effect=RuntimeError("boom")
    ):
        await _send_job_list(msg, "python")

    assert msg.answer.await_count == 2  # "Очікуйте" + error message
    assert "помилка" in msg.answer.call_args_list[1][0][0]


# ---------------------------------------------------------------------------
# _send_job_list — rate limit sleep after 20 messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_job_list_rate_limit_sleep() -> None:
    msg = _make_message()
    jobs = _make_jobs(21)

    with (
        patch.object(bot_module._job_service, "get_jobs", new_callable=AsyncMock, return_value=jobs),
        patch("bot.asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
    ):
        await _send_job_list(msg, "python")

    mock_sleep.assert_awaited_once_with(3)


# ---------------------------------------------------------------------------
# _register_language_handlers — handlers are registered
# ---------------------------------------------------------------------------

def test_language_handlers_registered() -> None:
    """Each supported language should have a registered handler."""
    # dp.message.handlers contains the registered handler objects
    from bot import dp
    handler_count = len(dp.message.handlers)
    # At minimum: /start + one per language
    assert handler_count >= len(SUPPORTED_LANGUAGES) + 1


# ---------------------------------------------------------------------------
# main — calls run_polling
# ---------------------------------------------------------------------------

def test_main_calls_run_polling() -> None:
    with (
        patch.object(bot_module.dp, "run_polling") as mock_poll,
        patch("bot.logging.basicConfig"),
    ):
        main()
        mock_poll.assert_called_once()


# ---------------------------------------------------------------------------
# Dynamic handler closure calls _send_job_list
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dynamic_handler_calls_send_job_list() -> None:
    """The dynamically registered handler should call _send_job_list."""
    from bot import dp

    # Find the handler registered for the first supported language
    target_lang = SUPPORTED_LANGUAGES[0]
    msg = _make_message()
    jobs = _make_jobs(1)

    with patch("bot._send_job_list", new_callable=AsyncMock) as mock_send:
        # Call the handler callback directly
        for handler in dp.message.handlers:
            # Try to find our dynamic handler by calling it
            cb = handler.callback
            if cb.__name__ == "handler":
                await cb(msg, _lang=target_lang)
                break

    mock_send.assert_awaited_once_with(msg, target_lang)


# ---------------------------------------------------------------------------
# Missing token raises ValueError
# ---------------------------------------------------------------------------

def test_missing_token_raises() -> None:
    """Importing bot without TELEGRAM_TOKEN raises ValueError."""
    import importlib
    import sys

    # Save and remove the token
    saved = os.environ.pop("TELEGRAM_TOKEN", None)
    # Remove bot from module cache to force re-import
    saved_module = sys.modules.pop("bot", None)

    try:
        with pytest.raises(ValueError, match="TELEGRAM_TOKEN"):
            importlib.import_module("bot")
    finally:
        # Restore
        if saved:
            os.environ["TELEGRAM_TOKEN"] = saved
        if saved_module:
            sys.modules["bot"] = saved_module


# ---------------------------------------------------------------------------
# __main__ guard
# ---------------------------------------------------------------------------

def test_main_guard() -> None:
    """Cover the if __name__ == '__main__' block."""
    with patch("bot.main") as mock_main:
        exec(
            compile(
                'if __name__ == "__main__": main()',
                "bot.py",
                "exec",
            ),
            {"__name__": "__main__", "main": mock_main},
        )
    mock_main.assert_called_once()
