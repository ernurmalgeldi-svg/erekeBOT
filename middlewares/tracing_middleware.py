"""
Задача 28: Middleware — добавляет request_id и span к каждому апдейту Telegram.
Цепочка: Telegram → бот → MCP → Ollama → ответ — всё под одним trace_id.
"""
import uuid
from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from opentelemetry import trace

logger = structlog.get_logger(__name__)


class TracingMiddleware(BaseMiddleware):
    """
    Для каждого входящего апдейта:
    1. Генерирует уникальный request_id
    2. Кладёт его в structlog contextvars (все дальнейшие логи будут иметь это поле)
    3. Открывает OpenTelemetry span — внутри него работают все сервисы
    """

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        request_id = str(uuid.uuid4())

        # Привязываем request_id ко всем structlog-логам в этом контексте
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)

        tracer = trace.get_tracer("mcp-telegram-bot")

        with tracer.start_as_current_span("handle_telegram_update") as span:
            span.set_attribute("request_id", request_id)

            # Пробрасываем request_id в data — хендлеры могут его использовать
            data["request_id"] = request_id

            log = logger.bind(request_id=request_id)
            log.info("telegram_update_received", event_type=type(event).__name__)

            try:
                result = await handler(event, data)
                log.info("telegram_update_handled", status="ok")
                return result
            except Exception as exc:
                span.record_exception(exc)
                log.error("telegram_update_failed", error=str(exc))
                raise
