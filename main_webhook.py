import asyncio
import os
import logging
from dotenv import load_dotenv
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from handlers.user_handlers import router

logging.basicConfig(level=logging.INFO)

WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = "/webhook"
HOST = "0.0.0.0"
PORT = 8080


async def on_startup(bot: Bot):
    await bot.set_webhook(f"{WEBHOOK_URL}{WEBHOOK_PATH}")
    print(f"🚀 Webhook установлен: {WEBHOOK_URL}{WEBHOOK_PATH}")


async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("🛑 Webhook удалён.")


def main():
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    bot = Bot(token=bot_token)
    dp = Dispatcher()
    dp.include_router(router)

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    print(f"🌐 Сервер запускается на порту {PORT}")
    web.run_app(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()