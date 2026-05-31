import logging
import asyncio
from groq import AsyncGroq
from config.settings import config

try:
    # Groq кілтін үлкен әріппен қауіпсіз оқу
    api_key = str(config.GROQ_API_KEY)
    groq_client = AsyncGroq(api_key=api_key)
except Exception as e:
    logging.error(f"Groq клиентін қосуда қате: {e}")
    groq_client = None

async def get_groq_stream_response(messages: list, bot, chat_id: int, processing_msg_id: int) -> str:
    """Задача 4 & 5: Стриминг және Модельдер Fallback роутері"""
    models_to_try = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile"]
    
    if not groq_client:
        return "⚠️ Groq API кілті кодқа дұрыс берілмеген!"

    for model in models_to_try:
        try:
            stream = await groq_client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            full_response = ""
            last_ui_update = asyncio.get_event_loop().time()
            
            async for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                
                # Тапсырма 4: Дебаунс (1.5 секундта 1 рет қана эдит)
                current_time = asyncio.get_event_loop().time()
                if current_time - last_ui_update > 1.5 and full_response.strip():
                    try:
                        await bot.edit_message_text(
                            text=full_response + " ▌",
                            chat_id=chat_id,
                            message_id=processing_msg_id
                        )
                        last_ui_update = current_time
                    except Exception:
                        pass
            
            # Соңғы нұсқасын таза шығару
            if full_response.strip():
                try:
                    await bot.edit_message_text(
                        text=full_response,
                        chat_id=chat_id,
                        message_id=processing_msg_id
                    )
                except Exception:
                    pass
                return full_response
                
        except Exception as e:
            logging.warning(f"Модель {model} қате берді: {e}. Келесі модельге ауысу...")
            continue
            
    raise Exception("Барлық Groq модельдері қате берді немесе API Key жарамсыз!")