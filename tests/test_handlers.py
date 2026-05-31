import pytest
from unittest.mock import AsyncMock, MagicMock, patch


# ============================================================================
# Вспомогательная функция создания Message-объекта через моки
# ============================================================================

def create_tg_message(text: str = "", user_id: int = 11111, voice=None, photo=None, caption=None):
    """
    Создаёт мок Message для aiogram 3.x.
    Не используем конструктор aiogram напрямую — он требует Bot в контексте.
    """
    from_user = MagicMock()
    from_user.id = user_id
    from_user.is_bot = False
    from_user.first_name = "Тестер"
    from_user.username = "tester"

    chat = MagicMock()
    chat.id = user_id
    chat.type = "private"

    message = MagicMock()
    message.message_id = 999
    message.from_user = from_user
    message.chat = chat
    message.text = text
    message.voice = voice
    message.photo = photo
    message.caption = caption

    # Все методы отправки — AsyncMock
    message.answer = AsyncMock(return_value=MagicMock(message_id=1000, edit_text=AsyncMock(), delete=AsyncMock()))
    message.answer_document = AsyncMock()
    message.reply = AsyncMock()

    return message


# ============================================================================
# ТЕСТЫ ХЕНДЛЕРОВ
# ============================================================================

@pytest.mark.asyncio
async def test_handler_start_welcome(mocker):
    """Задача 23: /start хендлер возвращает приветствие с MCP ботом."""
    from handlers.user_handlers import cmd_start

    message = create_tg_message("/start")
    await cmd_start(message)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "МСР" in call_text or "MCP" in call_text or "бот" in call_text.lower() or "Мен" in call_text


@pytest.mark.asyncio
async def test_handler_admin_access_denied(mocker):
    """Задача 23: Обычный пользователь не может войти в /admin."""
    from handlers.user_handlers import cmd_admin

    message = create_tg_message("/admin", user_id=11111)
    await cmd_admin(message)

    message.answer.assert_called_once()
    assert "РҰҚСАТ ЖОҚ" in message.answer.call_args[0][0] or "рұқсат" in message.answer.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_handler_admin_access_granted(mocker):
    """Задача 23: Администратор (ID=7777777) получает доступ к /admin."""
    from handlers.user_handlers import cmd_admin

    message = create_tg_message("/admin", user_id=7777777)
    await cmd_admin(message)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "АДМИНИСТРАТОР" in call_text or "ADMIN" in call_text or "КОШ КЕЛДІҢІЗ" in call_text


@pytest.mark.asyncio
async def test_handler_myrole_user(mocker):
    """Задача 23: Обычный пользователь видит роль User."""
    from handlers.user_handlers import cmd_myrole

    message = create_tg_message("/myrole", user_id=11111)
    await cmd_myrole(message)

    message.answer.assert_called_once()
    assert "User" in message.answer.call_args[0][0] or "Пайдаланушы" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handler_myrole_admin(mocker):
    """Задача 23: Администратор видит роль Admin."""
    from handlers.user_handlers import cmd_myrole

    message = create_tg_message("/myrole", user_id=7777777)
    await cmd_myrole(message)

    message.answer.assert_called_once()
    assert "Admin" in message.answer.call_args[0][0] or "Администратор" in message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_handler_private_mode_enable(mocker):
    """Задача 23: /private включает приватный режим (Ollama)."""
    from handlers.user_handlers import cmd_private, private_mode_users

    private_mode_users.discard(555)  # сбросить состояние
    message = create_tg_message("/private", user_id=555)
    await cmd_private(message)

    message.answer.assert_called()
    call_text = message.answer.call_args[0][0]
    assert "ҚОСЫЛДЫ" in call_text or "Жергілікті режим" in call_text or "PRIVATE" in call_text


@pytest.mark.asyncio
async def test_handler_private_mode_toggle_off(mocker):
    """Задача 23: Повторный /private выключает приватный режим."""
    from handlers.user_handlers import cmd_private, private_mode_users

    private_mode_users.add(556)  # уже включён
    message = create_tg_message("/private", user_id=556)
    await cmd_private(message)

    message.answer.assert_called()
    call_text = message.answer.call_args[0][0]
    assert "Қалыпты режим" in call_text or "Groq" in call_text or "жабылды" in call_text.lower()


@pytest.mark.asyncio
async def test_handler_history_view(mock_db_global, mocker):
    """Задача 23: /history возвращает историю из БД."""
    from handlers.user_handlers import show_history

    message = create_tg_message("/history", user_id=11111)
    await show_history(message)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "тарих" in call_text.lower() or "history" in call_text.lower() or "хабарламалар" in call_text.lower()


@pytest.mark.asyncio
async def test_handler_ask_no_query(mocker):
    """Задача 23: /ask без аргумента — возвращает подсказку."""
    from handlers.user_handlers import cmd_ask

    message = create_tg_message("/ask")
    await cmd_ask(message)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "/ask" in call_text or "Мысалы" in call_text or "мысал" in call_text.lower()


@pytest.mark.asyncio
async def test_handler_ask_rag_integration(mocker):
    """Задача 23: /ask с запросом использует RAG и возвращает ответ."""
    from handlers.user_handlers import cmd_ask

    message = create_tg_message("/ask Не такое Docker?")
    await cmd_ask(message)

    assert message.answer.call_count >= 2  # "Іздеуде..." + ответ
    last_call = message.answer.call_args_list[-1][0][0]
    assert "RAG" in last_call or "жауабы" in last_call.lower() or "бот" in last_call.lower()


@pytest.mark.asyncio
async def test_handler_voice_processing(mock_bot, mocker):
    """Задача 23: Голосовое сообщение транскрибируется и обрабатывается."""
    from handlers.user_handlers import handle_voice_message

    voice_obj = MagicMock()
    voice_obj.file_id = "voice_123"
    voice_obj.file_unique_id = "unique_voice_123"
    voice_obj.duration = 2
    voice_obj.file_size = 500
    voice_obj.mime_type = "audio/ogg"

    message = create_tg_message(user_id=11111, voice=voice_obj)

    # Мокируем os.path.exists и os.remove чтобы не упало
    mocker.patch("os.path.exists", return_value=False)
    mocker.patch("os.remove", return_value=None)

    await handle_voice_message(message, mock_bot)

    assert message.answer.call_count >= 1


@pytest.mark.asyncio
async def test_process_text_logic_with_docker_tool(mocker):
    """Задача 23: Упоминание 'docker' триггерит function calling."""
    from handlers.user_handlers import process_text_logic

    message = create_tg_message("Проверь докер статус")
    await process_text_logic(message, message.text)

    assert message.answer.call_count >= 1
    all_calls = " ".join(call[0][0] for call in message.answer.call_args_list)
    assert "Docker" in all_calls or "docker" in all_calls.lower()


@pytest.mark.asyncio
async def test_process_text_regular_message(mocker):
    """Задача 23: Обычный текст отправляется в Groq и возвращает ответ."""
    from handlers.user_handlers import process_text_logic

    message = create_tg_message("Привет, как дела?")
    await process_text_logic(message, message.text)

    # Groq мок вернёт ответ
    assert message.answer.call_count >= 1


@pytest.mark.asyncio
async def test_handler_help_command(mocker):
    """Задача 23: /help возвращает список команд."""
    from handlers.user_handlers import cmd_help

    message = create_tg_message("/help")
    await cmd_help(message)

    message.answer.assert_called_once()
    call_text = message.answer.call_args[0][0]
    assert "/files" in call_text or "/weather" in call_text or "команда" in call_text.lower()


@pytest.mark.asyncio
async def test_process_private_mode_uses_ollama(mocker):
    """Задача 23: В приватном режиме запрос идёт в Ollama."""
    from handlers.user_handlers import process_text_logic, private_mode_users

    user_id = 9999
    private_mode_users.add(user_id)

    message = create_tg_message("Сұрақ", user_id=user_id)
    sent_msg = MagicMock()
    sent_msg.delete = AsyncMock()
    message.answer = AsyncMock(return_value=sent_msg)

    await process_text_logic(message, "Сұрақ")

    private_mode_users.discard(user_id)  # cleanup
    assert message.answer.call_count >= 1
    all_calls = " ".join(str(call) for call in message.answer.call_args_list)
    assert "PRIVATE" in all_calls or "Ollama" in all_calls or "локал" in all_calls.lower()

