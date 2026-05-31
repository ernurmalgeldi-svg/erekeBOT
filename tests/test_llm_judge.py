import pytest
import json
import os
from unittest.mock import AsyncMock, MagicMock

# ============================================================================
# ЗАДАЧА 27: LLM-as-a-Judge — автоматическая оценка качества ответов
# ============================================================================

# Эталонный датасет (Golden Dataset) — 10 вопросов с эталонными ответами
GOLDEN_DATASET = [
    {
        "query": "Python-дағы list пен tuple айырмашылығы неде?",
        "expected": "List — өзгерітін (mutable), ал Tuple — өзгермейтін (immutable) деректер типі.",
    },
    {
        "query": "Docker контейнерді өшіру командасы қандай?",
        "expected": "Docker контейнерін тоқтату үшін 'docker stop <container_id>' командасы қолданылады.",
    },
    {
        "query": "RAG дегеніміз не?",
        "expected": "RAG — Retrieval-Augmented Generation, деректер базасынан контекст алып LLM-ге беру әдісі.",
    },
    {
        "query": "API дегеніміз не?",
        "expected": "API — Application Programming Interface, бағдарламалар арасындағы байланыс интерфейсі.",
    },
    {
        "query": "asyncio дегеніміз не Python контекстінде?",
        "expected": "asyncio — Python-дың асинхронды бағдарламалауға арналған кітапханасы.",
    },
]


async def _call_groq_mock(client, model: str, messages: list, response_format=None) -> str:
    """Groq API шақыруды жасайды (тесттерде мок арқылы)."""
    kwargs = {
        "model": model,
        "messages": messages,
    }
    if response_format:
        kwargs["response_format"] = response_format

    completion = await client.chat.completions.create(**kwargs)
    return completion.choices[0].message.content


async def get_bot_response_mockable(client, query: str) -> str:
    """Негізгі бот жауабын модельден алу (llama-3.1-8b-instant)."""
    return await _call_groq_mock(
        client,
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": query}]
    )


JUDGE_SYSTEM_PROMPT = """
Сен — ИИ ассистенттердің жауаптарын тексеретін қатал әрі әділ судьясың.
Саған пайдаланушының сұрағы, эталонды дұрыс жауап және бағаланушы боттың жауабы берілледі.
Сен боттың жауабын 1-ден 5-ке дейінгі шкаламен келесі критерийлер бойынша бағала:
1. Дәлдік (Accuracy)
2. Релеванттылық (Relevance)
3. Галлюцинацияның жоқтығы (No hallucinations)

Жауапты ТЕК қана келесі үлгідегі JSON форматында қайтар:
{"score": 4.5, "explanation": "Түсіндірме мұнда жазылады", "verdict": "passed"}
"""


@pytest.mark.asyncio
async def test_llm_judge_single_response():
    """
    Задача 27: Судья (Judge) жауапты дұрыс JSON форматта қайтарады.
    """
    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

    item = GOLDEN_DATASET[0]
    bot_reply = await get_bot_response_mockable(client, item["query"])

    judge_prompt = f"""
    Сұрақ: {item['query']}
    Эталонды жауап: {item['expected']}
    Боттың жауабы: {bot_reply}
    """

    judge_completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": judge_prompt}
        ]
    )

    raw = judge_completion.choices[0].message.content
    decision = json.loads(raw)

    assert "score" in decision, "JSON-да 'score' өрісі болуы керек"
    assert 1.0 <= float(decision["score"]) <= 5.0, "Балл 1-5 аралығында болуы керек"


@pytest.mark.asyncio
async def test_llm_judge_regression():
    """
    Задача 27: Регрессиялық тест — орташа баллдың 4.0-ден төмен түспеуін тексереді.
    CI-да бұл тест өзгерістерден кейін сапаның сақталуын қамтамасыз етеді.
    """
    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    scores = []

    for item in GOLDEN_DATASET:
        # 1. Тестіленетін боттан жауап алу
        actual_bot_reply = await get_bot_response_mockable(client, item["query"])

        # 2. Судья (70B модель) жауапты бағалайды
        judge_prompt = f"""
        Сұрақ: {item['query']}
        Эталонды жауап: {item['expected']}
        Боттың жауабы: {actual_bot_reply}
        """

        judge_completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": judge_prompt}
            ]
        )

        raw = judge_completion.choices[0].message.content
        decision = json.loads(raw)
        scores.append(float(decision["score"]))

    # 3. Орташа баллды есептеу
    average_score = sum(scores) / len(scores)
    print(f"\n[LLM-as-a-Judge] Орташа балл: {average_score:.2f} / 5.00")
    print(f"[LLM-as-a-Judge] Барлық баллдар: {scores}")

    # 4. Регрессиялық шек: орташа балл 4.0-ден төмен болмауы керек
    assert average_score >= 4.0, (
        f"Сапа деңгейі тым төмен: {average_score:.2f}. "
        f"Регрессия анықталды! Орташа балл 4.0-ден жоғары болуы керек."
    )


@pytest.mark.asyncio
async def test_llm_judge_score_format_validation():
    """
    Задача 27: Судья жауабының форматы дұрыс екенін тексеру.
    """
    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    item = GOLDEN_DATASET[1]

    bot_reply = await get_bot_response_mockable(client, item["query"])

    judge_completion = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
            {"role": "user", "content": f"Сұрақ: {item['query']}\nЭталон: {item['expected']}\nЖауап: {bot_reply}"}
        ]
    )

    raw = judge_completion.choices[0].message.content

    # JSON парсинг сәтсіз болмауы керек
    try:
        decision = json.loads(raw)
    except json.JSONDecodeError:
        pytest.fail(f"Судья дұрыс JSON қайтармады: {raw}")

    # Міндетті өрістер
    assert "score" in decision, "JSON-да 'score' өрісі жоқ"
    score = float(decision["score"])
    assert 1.0 <= score <= 5.0, f"Балл диапазоннан тыс: {score}"


@pytest.mark.asyncio
async def test_llm_judge_all_items_pass_minimum():
    """
    Задача 27: Әр жауап кемінде 3.0 балл алуы керек (минималды сапа шегі).
    """
    from groq import AsyncGroq

    client = AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))
    failed_items = []

    for item in GOLDEN_DATASET[:3]:  # Алғашқы 3 сұрақты тексеру
        bot_reply = await get_bot_response_mockable(client, item["query"])

        judge_completion = await client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": f"Сұрақ: {item['query']}\nЭталон: {item['expected']}\nЖауап: {bot_reply}"}
            ]
        )

        raw = judge_completion.choices[0].message.content
        decision = json.loads(raw)
        score = float(decision["score"])

        if score < 3.0:
            failed_items.append({"query": item["query"], "score": score})

    assert len(failed_items) == 0, (
        f"Келесі сұрақтарда сапа өте төмен: {failed_items}"
    )

