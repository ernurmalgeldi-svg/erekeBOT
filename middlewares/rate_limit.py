from aiogram import BaseMiddleware
from aiogram.types import Message
from utils.db_manager import db

class RateLimitMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        user_id = event.from_user.id
        chat_id = event.chat.id

        # 1. Per-user лимиті (минутына 10 сұраныс = секундына 0.166 токен қосылады)
        user_allowed = await db.check_rate_limit(f"user:{user_id}", capacity=10, refill_rate=0.166)
        if not user_allowed:
            await event.answer("⚠️ Сіз лимиттен асып кеттіңіз (минутына 10 сұраныс). Біраз күте тұрыңыз.")
            return

        # 2. Per-chat лимиті (минутына 50 сұраныс = секундына 0.833 токен)
        chat_allowed = await db.check_rate_limit(f"chat:{chat_id}", capacity=50, refill_rate=0.833)
        if not chat_allowed:
            await event.answer("⚠️ Бұл чатта сұраныс тым көп (минутына 50).")
            return

        return await handler(event, data)