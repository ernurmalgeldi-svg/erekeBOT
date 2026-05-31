import logging
import httpx

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"

async def get_ollama_response(messages: list) -> str:
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            payload = {
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            }
            response = await client.post(OLLAMA_URL, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["message"]["content"]
    except httpx.ConnectError:
        logger.error("Ollama serverine kosinuqa bolmady.")
        return "Ollama iske qosylmagan. Terminalda: ollama serve"
    except httpx.TimeoutException:
        logger.error("Ollama timeout.")
        return "Ollama uaqyt asty, qayta korinez."
    except Exception as e:
        logger.error(f"Ollama qatesi: {e}")
        return f"Ollama qatesi: {str(e)}"

async def check_ollama_available() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            return resp.status_code == 200
    except Exception:
        return False