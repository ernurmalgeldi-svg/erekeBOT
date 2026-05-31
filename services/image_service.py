import os
import logging
import httpx
import base64
from groq import AsyncGroq

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
HF_TOKEN = os.getenv("HF_TOKEN")

# HuggingFace Stable Diffusion моделі
HF_API_URL = "https://image.pollinations.ai/prompt/"


async def generate_image(prompt: str) -> bytes | None:
    """Pollinations.ai арқылы сурет генерациялайды."""
    try:
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&nologo=true"

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                return response.content
            else:
                logger.error(f"Pollinations қатесі: {response.status_code}")
                return None

    except Exception as e:
        logger.error(f"Сурет генерация қатесі: {e}")
        return None
async def analyze_image(image_data: bytes, question: str = "Суретте не бар?") -> str:
    """Groq vision арқылы суретті анализдейді."""
    try:
        base64_image = base64.b64encode(image_data).decode("utf-8")

        response = await groq_client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        },
                        {
                            "type": "text",
                            "text": question
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        return response.choices[0].message.content

    except Exception as e:
        logger