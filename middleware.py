"""Aiogram middleware for the DOU parser bot."""

import time
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, types
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject

_RATE_LIMIT_SECONDS: float = 30.0


class RateLimitMiddleware(BaseMiddleware):
    """Middleware that limits users to one request per ``_RATE_LIMIT_SECONDS``."""

    def __init__(self) -> None:
        self._last_request: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, types.Message):
            return await handler(event, data)

        user_id = event.from_user.id
        now = time.monotonic()
        last = self._last_request.get(user_id, 0.0)
        remaining = _RATE_LIMIT_SECONDS - (now - last)

        if remaining > 0:
            await event.answer(
                f"Зачекайте {remaining:.0f} сек. перед наступним запитом.",
                parse_mode=ParseMode.HTML,
            )
            return None

        self._last_request[user_id] = now
        return await handler(event, data)
