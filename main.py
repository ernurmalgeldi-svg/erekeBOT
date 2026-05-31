"""
Задача 28: main.py с structlog-логированием и OpenTelemetry трассировкой.
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from logging_setup import setup_logging, setup_tracing, get_logger
from handlers.user_handlers import router
from middlewares.tracing_middleware import TracingMiddleware
from aiogram import Bot, Dispatcher

setup_logging()
logger = get_logger(__name__)


async def main():
    # Инициализируем трассировку (экспорт → Jaeger)
    setup_tracing(service_name="mcp-telegram-bot")

    bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("BOT_TOKEN")
    if not bot_token:
        logger.error("bot_token_missing", env_var="TELEGRAM_BOT_TOKEN")
        return

    bot = Bot(token=bot_token)
    dp = Dispatcher()

    # Подключаем middleware трассировки — первым в цепочке
    dp.update.middleware(TracingMiddleware())
    dp.include_router(router)

    logger.info("bot_started", token_prefix=bot_token[:10])
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("bot_stopped")
