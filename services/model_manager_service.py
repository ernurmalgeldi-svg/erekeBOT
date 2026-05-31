import httpx
import asyncio
import logging
import json

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"


async def pull_model(model_name: str, bot, chat_id: int, msg_id: int):
    """Ollama арқылы модель жүктейді, прогресті жаңартып отырады."""
    try:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream(
                "POST",
                f"{OLLAMA_BASE_URL}/api/pull",
                json={"name": model_name}
            ) as response:

                if response.status_code != 200:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=f"❌ Қате: модель жүктеу басталмады ({response.status_code})"
                    )
                    return False

                last_update = asyncio.get_event_loop().time()
                last_status = ""

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        status = data.get("status", "")
                        completed = data.get("completed", 0)
                        total = data.get("total", 0)

                        if status != last_status or asyncio.get_event_loop().time() - last_update > 5:
                            if total > 0:
                                percent = round(completed / total * 100, 1)
                                progress_bar = "█" * int(percent // 10) + "░" * (10 - int(percent // 10))
                                text = (
                                    f"⬇️ <b>{model_name}</b> жүктелуде...\n\n"
                                    f"[{progress_bar}] {percent}%\n"
                                    f"📦 {round(completed/1024/1024, 1)} / {round(total/1024/1024, 1)} MB\n"
                                    f"🔄 {status}"
                                )
                            else:
                                text = (
                                    f"⬇️ <b>{model_name}</b> жүктелуде...\n\n"
                                    f"🔄 {status}"
                                )

                            try:
                                await bot.edit_message_text(
                                    chat_id=chat_id,
                                    message_id=msg_id,
                                    text=text,
                                    parse_mode="HTML"
                                )
                            except Exception:
                                pass

                            last_update = asyncio.get_event_loop().time()
                            last_status = status

                        if status == "success":
                            await bot.edit_message_text(
                                chat_id=chat_id,
                                message_id=msg_id,
                                text=f"✅ <b>{model_name}</b> сәтті жүктелді!",
                                parse_mode="HTML"
                            )
                            return True

                    except json.JSONDecodeError:
                        continue

        return True

    except httpx.ConnectError:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text="❌ Ollama сервері іске қосылмаған!"
        )
        return False
    except Exception as e:
        logger.error(f"Модель жүктеу қатесі: {e}")
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=msg_id,
            text=f"❌ Қате: {str(e)}"
        )
        return False


async def list_models() -> list:
    """Ollama-дағы жүктелген модельдер тізімі."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []