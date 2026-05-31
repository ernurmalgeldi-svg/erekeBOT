import httpx
import json
import logging

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434/api/chat"
OLLAMA_MODEL = "llama3.2:3b"

# Құралдар анықтамасы
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Қаланың ауа райын қайтарады",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "Қала атауы"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Математикалық есептеу жасайды",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Математикалық өрнек, мысалы: 2+2"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Қазіргі уақытты қайтарады",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> str:
    """Құралды іске қосады және нәтиже қайтарады."""
    if tool_name == "get_weather":
        city = arguments.get("city", "Алматы")
        return f"{city} қаласында ауа райы: +22°C, күн ашық ☀️"

    elif tool_name == "calculate":
        expression = arguments.get("expression", "0")
        try:
            result = eval(expression)
            return f"{expression} = {result}"
        except Exception:
            return f"Қате: {expression} есептеу мүмкін емес"

    elif tool_name == "get_current_time":
        from datetime import datetime
        now = datetime.now().strftime("%H:%M:%S, %d.%m.%Y")
        return f"Қазіргі уақыт: {now}"

    return f"Белгісіз құрал: {tool_name}"


async def run_with_tools(user_message: str) -> dict:
    """Ollama-да function calling іске қосады."""
    messages = [
        {
            "role": "system",
            "content": "Сен көмекші ассистентсің. Қажет болса құралдарды қолдан."
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "tools": TOOLS,
                "stream": False
            }
        )
        data = response.json()

    message = data.get("message", {})
    tool_calls = message.get("tool_calls", [])

    tool_results = []
    if tool_calls:
        for tool_call in tool_calls:
            tool_name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            result = execute_tool(tool_name, arguments)
            tool_results.append({
                "tool": tool_name,
                "arguments": arguments,
                "result": result
            })

        # Құрал нәтижесімен қайта сұрау
        messages.append({"role": "assistant", "content": "", "tool_calls": tool_calls})
        for tr in tool_results:
            messages.append({
                "role": "tool",
                "content": tr["result"]
            })

        async with httpx.AsyncClient(timeout=60.0) as client:
            response2 = await client.post(
                OLLAMA_URL,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False
                }
            )
            data2 = response2.json()
            final_answer = data2.get("message", {}).get("content", "Жауап жоқ")
    else:
        final_answer = message.get("content", "Жауап жоқ")

    return {
        "answer": final_answer,
        "tool_calls": tool_results
    }