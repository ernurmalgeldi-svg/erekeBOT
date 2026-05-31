import time
import asyncio
import logging
import openpyxl
from groq import AsyncGroq
import httpx
import os

logger = logging.getLogger(__name__)

groq_client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

QUESTIONS = [
    "Python дегеніміз не?",
    "Жасанды интеллект дегеніміз не?",
    "Machine Learning қалай жұмыс істейді?",
    "Telegram бот жасау үшін не керек?",
    "RAG дегеніміз не?",
    "SQLite және PostgreSQL айырмашылығы неде?",
    "API дегеніміз не?",
    "Docker контейнер дегеніміз не?",
    "Groq API не үшін қолданылады?",
    "Ollama дегеніміз не?",
    "LLM дегеніміз не?",
    "Нейрондық желі дегеніміз не?",
    "GitHub дегеніміз не?",
    "REST API дегеніміз не?",
    "JSON дегеніміз не?",
    "Асинхронды бағдарламалау дегеніміз не?",
    "Redis не үшін қолданылады?",
    "Aiogram кітапханасы не үшін керек?",
    "Токен дегеніміз не LLM контекстінде?",
    "KazNITU қандай университет?"
]

async def benchmark_groq(question: str) -> dict:
    start = time.time()
    try:
        response = await groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": question}],
            max_tokens=200
        )
        latency = time.time() - start
        answer = response.choices[0].message.content
        tokens = response.usage.completion_tokens
        return {
            "platform": "Groq",
            "question": question,
            "latency": round(latency, 2),
            "tokens": tokens,
            "tokens_per_sec": round(tokens / latency, 1) if latency > 0 else 0,
            "answer": answer[:100]
        }
    except Exception as e:
        return {
            "platform": "Groq",
            "question": question,
            "latency": -1,
            "tokens": 0,
            "tokens_per_sec": 0,
            "answer": f"Қате: {str(e)}"
        }

async def benchmark_ollama(question: str) -> dict:
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": "llama3.2:3b",
                    "messages": [{"role": "user", "content": question}],
                    "stream": False
                }
            )
            data = response.json()
            latency = time.time() - start
            answer = data["message"]["content"]
            tokens = len(answer.split())
            return {
                "platform": "Ollama",
                "question": question,
                "latency": round(latency, 2),
                "tokens": tokens,
                "tokens_per_sec": round(tokens / latency, 1) if latency > 0 else 0,
                "answer": answer[:100]
            }
    except Exception as e:
        return {
            "platform": "Ollama",
            "question": question,
            "latency": -1,
            "tokens": 0,
            "tokens_per_sec": 0,
            "answer": f"Қате: {str(e)}"
        }

async def run_benchmark() -> str:
    results = []
    for i, question in enumerate(QUESTIONS):
        groq_result = await benchmark_groq(question)
        ollama_result = await benchmark_ollama(question)
        results.append(groq_result)
        results.append(ollama_result)

    # Excel жасау
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Benchmark"

    headers = ["Платформа", "Сұрақ", "Латентность (сек)", "Токендер", "Токен/сек", "Жауап үзіндісі"]
    ws.append(headers)

    for r in results:
        ws.append([
            r["platform"],
            r["question"],
            r["latency"],
            r["tokens"],
            r["tokens_per_sec"],
            r["answer"]
        ])

    # Статистика
    groq_latencies = [r["latency"] for r in results if r["platform"] == "Groq" and r["latency"] > 0]
    ollama_latencies = [r["latency"] for r in results if r["platform"] == "Ollama" and r["latency"] > 0]

    ws2 = wb.create_sheet("Статистика")
    ws2.append(["Метрика", "Groq", "Ollama"])
    ws2.append(["p50 латентность", round(sorted(groq_latencies)[len(groq_latencies)//2], 2), round(sorted(ollama_latencies)[len(ollama_latencies)//2], 2)])
    ws2.append(["p95 латентность", round(sorted(groq_latencies)[int(len(groq_latencies)*0.95)], 2), round(sorted(ollama_latencies)[int(len(ollama_latencies)*0.95)], 2)])
    ws2.append(["Орташа латентность", round(sum(groq_latencies)/len(groq_latencies), 2), round(sum(ollama_latencies)/len(ollama_latencies), 2)])

    filename = "benchmark_results.xlsx"
    wb.save(filename)
    return filename