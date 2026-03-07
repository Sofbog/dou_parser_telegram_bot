"""Tests for middleware.py — RateLimitMiddleware."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram import types
from aiogram.types import TelegramObject

from middleware import RateLimitMiddleware, _RATE_LIMIT_SECONDS


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_message(user_id: int = 1) -> MagicMock:
    msg = MagicMock(spec=types.Message)
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.answer = AsyncMock()
    return msg


def _make_non_message_event() -> MagicMock:
    return MagicMock(spec=TelegramObject)


# ---------------------------------------------------------------------------
# First request passes through
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_first_request_passes() -> None:
    mw = RateLimitMiddleware()
    handler = AsyncMock(return_value="ok")
    msg = _make_message(user_id=42)

    result = await mw(handler, msg, {})

    assert result == "ok"
    handler.assert_awaited_once_with(msg, {})
    msg.answer.assert_not_called()


# ---------------------------------------------------------------------------
# Second request within limit is blocked
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_second_request_blocked() -> None:
    mw = RateLimitMiddleware()
    handler = AsyncMock(return_value="ok")
    msg = _make_message(user_id=42)

    await mw(handler, msg, {})
    result = await mw(handler, msg, {})

    assert result is None
    msg.answer.assert_called_once()
    assert "Зачекайте" in msg.answer.call_args[0][0]


# ---------------------------------------------------------------------------
# Different users are independent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_different_users_independent() -> None:
    mw = RateLimitMiddleware()
    handler = AsyncMock(return_value="ok")

    msg1 = _make_message(user_id=1)
    msg2 = _make_message(user_id=2)

    await mw(handler, msg1, {})
    result = await mw(handler, msg2, {})

    assert result == "ok"
    assert handler.await_count == 2


# ---------------------------------------------------------------------------
# Request passes after cooldown expires
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_request_passes_after_cooldown() -> None:
    mw = RateLimitMiddleware()
    handler = AsyncMock(return_value="ok")
    msg = _make_message(user_id=42)

    await mw(handler, msg, {})

    # Simulate time passing beyond rate limit
    mw._last_request[42] = time.monotonic() - _RATE_LIMIT_SECONDS - 1

    result = await mw(handler, msg, {})
    assert result == "ok"
    assert handler.await_count == 2


# ---------------------------------------------------------------------------
# Non-Message events pass through without rate limiting
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_non_message_event_passes() -> None:
    mw = RateLimitMiddleware()
    handler = AsyncMock(return_value="ok")
    event = _make_non_message_event()

    result = await mw(handler, event, {})

    assert result == "ok"
    handler.assert_awaited_once_with(event, {})
