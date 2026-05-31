import sys
import os
from unittest.mock import MagicMock, AsyncMock
import pytest

# ============================================================================
# Ð¨ÐÐ“ 1: ÐœÐ¾ÐºÐ¸Ñ€ÑƒÐµÐ¼ Ð’Ð¡Ð• Ð²Ð½ÐµÑˆÐ½Ð¸Ðµ Ð·Ð°Ð²Ð¸ÑÐ¸Ð¼Ð¾ÑÑ‚Ð¸ Ð”Ðž Ð»ÑŽÐ±Ñ‹Ñ… Ð¸Ð¼Ð¿Ð¾Ñ€Ñ‚Ð¾Ð²
# ============================================================================

# --- psycopg2 ---
mock_psycopg2 = MagicMock()
mock_conn = MagicMock()
mock_cur = MagicMock()
mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)
mock_psycopg2.connect.return_value = mock_conn
sys.modules["psycopg2"] = mock_psycopg2
sys.modules["psycopg2.extras"] = MagicMock()

# --- httpx ---
mock_httpx = MagicMock()
mock_http_response = MagicMock()
mock_http_response.status_code = 200
mock_http_response.json.return_value = {
    "message": {"content": "Ollama Ð»Ð¾ÐºÐ°Ð»Ð´Ñ‹ Ð¶Ð°ÑƒÐ°Ð±Ñ‹"},
    "status": "success"
}
mock_http_response.raise_for_status = MagicMock()

mock_async_client_instance = AsyncMock()
mock_async_client_instance.post = AsyncMock(return_value=mock_http_response)
mock_async_client_instance.get = AsyncMock(return_value=mock_http_response)

mock_async_client_cls = MagicMock()
mock_async_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_async_client_instance)
mock_async_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)

mock_httpx.AsyncClient = mock_async_client_cls
mock_httpx.ConnectError = ConnectionError
mock_httpx.TimeoutException = TimeoutError
mock_httpx.RequestError = Exception
mock_httpx.HTTPStatusError = Exception
sys.modules["httpx"] = mock_httpx

# --- groq ---
judge_json_output = '{"score": 5, "explanation": "ÐžÑ‚Ð²ÐµÑ‚ ÑÐ¾Ð²Ð¿Ð°Ð´Ð°ÐµÑ‚", "verdict": "passed"}'

mock_groq_response = MagicMock()
mock_groq_response.choices = [MagicMock(message=MagicMock(content=judge_json_output))]
mock_groq_response.usage = MagicMock(completion_tokens=50)

mock_completions = MagicMock()
mock_completions.create = AsyncMock(return_value=mock_groq_response)

mock_chat = MagicMock()
mock_chat.completions = mock_completions

mock_async_groq_instance = MagicMock()
mock_async_groq_instance.chat = mock_chat

mock_async_groq_cls = MagicMock(return_value=mock_async_groq_instance)

mock_groq_module = MagicMock()
mock_groq_module.AsyncGroq = mock_async_groq_cls

# Ð’ÐÐ–ÐÐž: Ñ‡Ñ‚Ð¾Ð±Ñ‹ "from groq import AsyncGroq" Ñ‚Ð¾Ð¶Ðµ Ñ€Ð°Ð±Ð¾Ñ‚Ð°Ð»Ð¾
sys.modules["groq"] = mock_groq_module

# --- openpyxl (Ð´Ð»Ñ benchmark_service) ---
sys.modules["openpyxl"] = MagicMock()

# --- dotenv ---
mock_dotenv = MagicMock()
mock_dotenv.load_dotenv = MagicMock()
sys.modules["dotenv"] = mock_dotenv

# --- mcp ---
sys.modules["mcp"] = MagicMock()
sys.modules["mcp.client"] = MagicMock()
sys.modules["mcp.client.stdio"] = MagicMock()

# --- pydantic_settings ---
mock_pydantic_settings = MagicMock()
class FakeBaseSettings:
    def __init__(self, **kwargs): pass
mock_pydantic_settings.BaseSettings = FakeBaseSettings
mock_pydantic_settings.SettingsConfigDict = MagicMock(return_value={})
sys.modules["pydantic_settings"] = mock_pydantic_settings

# ============================================================================
# Ð¨ÐÐ“ 2: ÐœÐ¾ÐºÐ¸Ñ€ÑƒÐµÐ¼ Ð²ÑÐµ Ð²Ð½ÑƒÑ‚Ñ€ÐµÐ½Ð½Ð¸Ðµ ÑÐµÑ€Ð²Ð¸ÑÑ‹
# ============================================================================

os.environ["GROQ_API_KEY"] = "gsk_test_mock_key_12345"
os.environ["ADMIN_ID"] = "7777777"
os.environ["TELEGRAM_BOT_TOKEN"] = "123456:ABC-DEF"
os.environ["DB_USER"] = "test"
os.environ["DB_PASS"] = "test"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5432"
os.environ["DB_NAME"] = "testdb"

# RAG
mock_rag = MagicMock()
mock_rag.search_similar = MagicMock(return_value=["ðŸ“„ ÐÐ°Ð¹Ð´ÐµÐ½Ð½Ñ‹Ð¹ Ð´Ð¾ÐºÑƒÐ¼ÐµÐ½Ñ‚ 1: Ð¢ÐµÑÑ‚ ÐºÐ¾Ð½Ñ‚ÐµÐºÑÑ‚Ñ–"])
mock_rag.init_db = MagicMock()
mock_rag.load_sample_documents = MagicMock()
mock_rag.add_document = MagicMock()
sys.modules["services.rag_service"] = mock_rag

# image_service
mock_image_svc = MagicMock()
mock_image_svc.generate_image = AsyncMock(return_value=b"fake_png")
mock_image_svc.analyze_image = AsyncMock(return_value="ÐÐ½Ð°Ð»Ð¸Ð· Ð¶Ð°ÑƒÐ°Ð±Ñ‹")
sys.modules["services.image_service"] = mock_image_svc

# voice_service
mock_voice_svc = MagicMock()
mock_voice_svc.transcribe_audio = AsyncMock(return_value="Ð”Ð°ÑƒÑ‹Ñ Ð¼Ó™Ñ‚Ñ–Ð½Ñ–")
sys.modules["services.voice_service"] = mock_voice_svc

# calendar_service
mock_cal_svc = MagicMock()
mock_cal_svc.get_auth_url = MagicMock(return_value="https://mock-auth-url.com")
mock_cal_svc.exchange_code = MagicMock(return_value=True)
mock_cal_svc.create_event = AsyncMock(return_value="âœ… ÐžÒ›Ð¸Ò“Ð° Ò›Ð¾ÑÑ‹Ð»Ð´Ñ‹")
mock_cal_svc.list_events = AsyncMock(return_value="ðŸ“… Ð¢Ñ–Ð·Ñ–Ð¼")
sys.modules["services.calendar_service"] = mock_cal_svc

# search_service
mock_search_svc = MagicMock()
mock_search_svc.search_web = MagicMock(return_value=[{"body": "Ð†Ð·Ð´ÐµÑƒ Ð¼Ó™Ñ‚Ñ–Ð½Ñ–"}])
mock_search_svc.format_search_results = MagicMock(return_value="Ð¡Ñ–Ð»Ñ‚ÐµÐ¼ÐµÐ»ÐµÑ€")
sys.modules["services.search_service"] = mock_search_svc

# mcp_aggregator
mock_mcp_agg = MagicMock()
mock_mcp_agg.get_remote_docker_status = AsyncMock(return_value="running")
mock_mcp_agg.get_mcp_tools_list = AsyncMock(return_value=["tool1", "tool2"])
sys.modules["utils.mcp_aggregator"] = mock_mcp_agg

# ollama_service
mock_ollama_svc = MagicMock()
mock_ollama_svc.check_ollama_available = AsyncMock(return_value=True)
mock_ollama_svc.get_ollama_response = AsyncMock(return_value="Ollama Ð»Ð¾ÐºÐ°Ð»Ð´Ñ‹ Ð¶Ð°ÑƒÐ°Ð±Ñ‹")
sys.modules["services.ollama_service"] = mock_ollama_svc

# function_calling_service
mock_fc_svc = MagicMock()
mock_fc_svc.run_with_tools = AsyncMock(return_value={"answer": "Ð–Ð°ÑƒÐ°Ð¿", "tool_calls": []})
sys.modules["services.function_calling_service"] = mock_fc_svc

# benchmark_service
mock_bench_svc = MagicMock()
mock_bench_svc.run_benchmark = AsyncMock(return_value="benchmark_result.xlsx")
sys.modules["services.benchmark_service"] = mock_bench_svc

# model_manager_service
mock_model_mgr = MagicMock()
mock_model_mgr.pull_model = AsyncMock(return_value=None)
mock_model_mgr.list_models = AsyncMock(return_value=["llama3.2:3b", "qwen2.5:0.5b"])
sys.modules["services.model_manager_service"] = mock_model_mgr

# llm_service (Ð½Ð° Ð²ÑÑÐºÐ¸Ð¹ ÑÐ»ÑƒÑ‡Ð°Ð¹)
sys.modules["services.llm_service"] = MagicMock()

# utils.db_manager â€” Ð¼Ð¾ÐºÐ¸Ñ€ÑƒÐµÐ¼ Ð¼Ð¾Ð´ÑƒÐ»ÑŒ Ñ†ÐµÐ»Ð¸ÐºÐ¾Ð¼
mock_db_instance = AsyncMock()
mock_db_instance.get_chat_history = AsyncMock(return_value=[
    {"role": "user", "content": "Ð¡Ò±Ñ€Ð°Ò›"},
    {"role": "assistant", "content": "Ð–Ð°ÑƒÐ°Ð¿"}
])
mock_db_instance.save_message = AsyncMock(return_value=True)
mock_db_instance.check_rate_limit = AsyncMock(return_value=True)
mock_db_instance.replace_history_with_summary = AsyncMock(return_value=None)

mock_db_module = MagicMock()
mock_db_module.db = mock_db_instance
mock_db_module.DBManager = MagicMock(return_value=mock_db_instance)
sys.modules["utils.db_manager"] = mock_db_module

# config / settings â€” Ñ‡Ñ‚Ð¾Ð±Ñ‹ Ð½Ðµ ÑƒÐ¿Ð°Ð»Ð¾ Ð½Ð° sys.exit
mock_config = MagicMock()
mock_config.TELEGRAM_BOT_TOKEN = "123456:ABC-DEF"
mock_config.GROQ_API_KEY = "gsk_test_mock_key_12345"
mock_settings_module = MagicMock()
mock_settings_module.config = mock_config
mock_settings_module.Settings = MagicMock(return_value=mock_config)
sys.modules["config"] = mock_settings_module
sys.modules["config.settings"] = mock_settings_module


# ============================================================================
# Ð¨ÐÐ“ 3: Ð¤Ð¸ÐºÑÑ‚ÑƒÑ€Ñ‹
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    import asyncio
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def mock_db_global(mocker):
    """ÐŸÐ°Ñ‚Ñ‡Ð¸Ð¼ db Ð¿Ñ€ÑÐ¼Ð¾ Ð² handlers.user_handlers Ð´Ð»Ñ ÐºÐ°Ð¶Ð´Ð¾Ð³Ð¾ Ñ‚ÐµÑÑ‚Ð°."""
    db_mock = AsyncMock()
    db_mock.get_chat_history = AsyncMock(return_value=[
        {"role": "user", "content": "Ð¡Ò±Ñ€Ð°Ò›"},
        {"role": "assistant", "content": "Ð–Ð°ÑƒÐ°Ð¿"}
    ])
    db_mock.save_message = AsyncMock(return_value=True)
    db_mock.check_rate_limit = AsyncMock(return_value=True)

    try:
        mocker.patch("handlers.user_handlers.db", db_mock)
    except Exception:
        pass
    return db_mock


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.edit_message_text = AsyncMock()
    bot.send_photo = AsyncMock()
    bot.get_file = AsyncMock(return_value=MagicMock(file_path="voice/mock.ogg"))
    file_mock = MagicMock()
    file_mock.read.return_value = b"bytes_data"
    bot.download_file = AsyncMock(return_value=file_mock)
    return bot

