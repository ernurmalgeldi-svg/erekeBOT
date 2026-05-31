import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> list:
    """DuckDuckGo арқылы интернеттен іздейді."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return results
    except Exception as e:
        logger.error(f"Іздеу қатесі: {e}")
        return []


def format_search_results(results: list) -> str:
    """Іздеу нәтижелерін форматтайды."""
    if not results:
        return "Нәтиже табылмады."

    formatted = ""
    for i, r in enumerate(results, 1):
        title = r.get("title", "Тақырып жоқ")
        body = r.get("body", "")[:200]
        href = r.get("href", "")
        formatted += f"{i}. <b>{title}</b>\n{body}...\n<a href='{href}'>🔗 Сілтеме</a>\n\n"

    return formatted