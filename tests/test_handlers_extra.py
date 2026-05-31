import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_msg(text="", user_id=11111, voice=None, photo=None, caption=None):
    from_user = MagicMock()
    from_user.id = user_id
    from_user.is_bot = False
    from_user.first_name = "Тестер"
    from_user.username = "tester"
    chat = MagicMock()
    chat.id = user_id
    chat.type = "private"
    msg = MagicMock()
    msg.message_id = 999
    msg.from_user = from_user
    msg.chat = chat
    msg.text = text
    msg.voice = voice
    msg.photo = photo
    msg.caption = caption
    sent = MagicMock()
    sent.message_id = 1000
    sent.edit_text = AsyncMock()
    sent.delete = AsyncMock()
    msg.answer = AsyncMock(return_value=sent)
    msg.answer_document = AsyncMock()
    msg.reply = AsyncMock()
    return msg


# ── /imagine ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_imagine_no_prompt(mock_bot):
    from handlers.user_handlers import cmd_imagine
    msg = make_msg("/imagine")
    await cmd_imagine(msg, mock_bot)
    msg.answer.assert_called_once()
    assert "/imagine" in msg.answer.call_args[0][0] or "Мысалы" in msg.answer.call_args[0][0] or "генерация" in msg.answer.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_cmd_imagine_with_prompt(mock_bot, mocker):
    from handlers.user_handlers import cmd_imagine
    mocker.patch("services.image_service.generate_image", new=AsyncMock(return_value=b"png_data"))
    mocker.patch("handlers.user_handlers.generate_image", new=AsyncMock(return_value=b"png_data"))
    msg = make_msg("/imagine a cat in space")
    sent = MagicMock()
    sent.delete = AsyncMock()
    sent.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=sent)
    mock_bot.send_photo = AsyncMock()
    await cmd_imagine(msg, mock_bot)
    assert msg.answer.call_count >= 1


# ── /handle_photo ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_handle_photo_with_caption(mock_bot, mocker):
    from handlers.user_handlers import handle_photo
    mocker.patch("handlers.user_handlers.analyze_image", new=AsyncMock(return_value="Бұл мысық"))
    photo_item = MagicMock()
    photo_item.file_id = "photo_abc"
    msg = make_msg(user_id=11111, photo=[photo_item], caption="Бұл не?")
    sent = MagicMock()
    sent.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=sent)
    mock_bot.get_file = AsyncMock(return_value=MagicMock(file_path="photos/abc.jpg"))
    file_data = MagicMock()
    file_data.read.return_value = b"image_bytes"
    mock_bot.download_file = AsyncMock(return_value=file_data)
    await handle_photo(msg, mock_bot)
    assert sent.edit_text.call_count >= 1


# ── /benchmark ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_benchmark_success(mocker):
    from handlers.user_handlers import cmd_benchmark
    mocker.patch("handlers.user_handlers.run_benchmark", new=AsyncMock(return_value="result.xlsx"))
    mocker.patch("aiogram.types.FSInputFile", return_value=MagicMock())
    msg = make_msg("/benchmark")
    await cmd_benchmark(msg)
    assert msg.answer.call_count >= 1


# ── callback кнопки ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_callback_files():
    from handlers.user_handlers import cb_files
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_files(cb)
    cb.message.answer.assert_called_once()
    cb.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_weather():
    from handlers.user_handlers import cb_weather
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_weather(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_time():
    from handlers.user_handlers import cb_time
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_time(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_calc():
    from handlers.user_handlers import cb_calc
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_calc(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_resources():
    from handlers.user_handlers import cb_resources
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_resources(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_prompts():
    from handlers.user_handlers import cb_prompts
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_prompts(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_tools():
    from handlers.user_handlers import cb_tools
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_tools(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_mcpstatus():
    from handlers.user_handlers import cb_mcpstatus
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_mcpstatus(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_myrole():
    from handlers.user_handlers import cb_myrole
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_myrole(cb)
    cb.message.answer.assert_called_once()


@pytest.mark.asyncio
async def test_callback_clear():
    from handlers.user_handlers import cb_clear
    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await cb_clear(cb)
    cb.message.answer.assert_called_once()


# ── /search ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_search_no_query():
    from handlers.user_handlers import cmd_search
    msg = make_msg("/search")
    await cmd_search(msg)
    msg.answer.assert_called_once()
    assert "/search" in msg.answer.call_args[0][0] or "Мысалы" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_search_with_query():
    from handlers.user_handlers import cmd_search
    msg = make_msg("/search Python туралы")
    await cmd_search(msg)
    assert msg.answer.call_count >= 1


# ── /gcal_auth / gcal_code / gcal_events / gcal_add ──────────────────────────

@pytest.mark.asyncio
async def test_cmd_gcal_auth():
    from handlers.user_handlers import cmd_gcal_auth
    msg = make_msg("/gcal_auth")
    await cmd_gcal_auth(msg)
    msg.answer.assert_called_once()
    assert "Google" in msg.answer.call_args[0][0] or "auth" in msg.answer.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_cmd_gcal_code_empty():
    from handlers.user_handlers import cmd_gcal_code
    msg = make_msg("/gcal_code")
    await cmd_gcal_code(msg)
    msg.answer.assert_called_once()
    assert "Код" in msg.answer.call_args[0][0] or "код" in msg.answer.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_cmd_gcal_code_with_code():
    from handlers.user_handlers import cmd_gcal_code
    msg = make_msg("/gcal_code abc123")
    await cmd_gcal_code(msg)
    assert msg.answer.call_count >= 1


@pytest.mark.asyncio
async def test_cmd_gcal_events():
    from handlers.user_handlers import cmd_gcal_events
    msg = make_msg("/gcal_events")
    await cmd_gcal_events(msg)
    msg.answer.assert_called_once()


@pytest.mark.asyncio
async def test_cmd_gcal_add_no_args():
    from handlers.user_handlers import cmd_gcal_add
    msg = make_msg("/gcal_add")
    await cmd_gcal_add(msg)
    msg.answer.assert_called_once()
    assert "Формат" in msg.answer.call_args[0][0] or "gcal_add" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_gcal_add_with_args():
    from handlers.user_handlers import cmd_gcal_add
    msg = make_msg("/gcal_add Кездесу|2026-06-01|14:00")
    await cmd_gcal_add(msg)
    msg.answer.assert_called_once()


# ── /tools_test ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_tools_test_no_query():
    from handlers.user_handlers import cmd_tools_test
    msg = make_msg("/tools_test")
    await cmd_tools_test(msg)
    msg.answer.assert_called_once()


@pytest.mark.asyncio
async def test_cmd_tools_test_with_query():
    from handlers.user_handlers import cmd_tools_test
    msg = make_msg("/tools_test Алматыда ауа райы қандай?")
    await cmd_tools_test(msg)
    assert msg.answer.call_count >= 1


# ── /model ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cmd_model_not_admin(mock_bot):
    from handlers.user_handlers import cmd_model
    msg = make_msg("/model", user_id=11111)
    await cmd_model(msg, mock_bot)
    msg.answer.assert_called_once()
    assert "Админ" in msg.answer.call_args[0][0] or "Admin" in msg.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_cmd_model_list(mock_bot):
    from handlers.user_handlers import cmd_model
    msg = make_msg("/model", user_id=7777777)
    await cmd_model(msg, mock_bot)
    assert msg.answer.call_count >= 1


# ── handle_text_message ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_handle_text_message():
    from handlers.user_handlers import handle_text_message
    msg = make_msg("Сәлем дүние!")
    await handle_text_message(msg)
    assert msg.answer.call_count >= 1


# ── history empty ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_handler_history_empty(mocker):
    from handlers.user_handlers import show_history
    mocker.patch("handlers.user_handlers.db", new_callable=lambda: lambda: MagicMock(
        get_chat_history=AsyncMock(return_value=[])
    ))
    msg = make_msg("/history")
    # db пустой — отдельно патчим
    import handlers.user_handlers as uh
    uh.db.get_chat_history = AsyncMock(return_value=[])
    await show_history(msg)
    msg.answer.assert_called_once()
    assert "База бос" in msg.answer.call_args[0][0] or "тарих" in msg.answer.call_args[0][0].lower()


# ── process_text_logic: role keyword ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_process_text_role_keyword():
    from handlers.user_handlers import process_text_logic
    msg = make_msg("менің рөлім қандай?")
    await process_text_logic(msg, "менің рөлім қандай?")
    assert msg.answer.call_count >= 1


# ── private mode: ollama unavailable ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_private_ollama_unavailable(mocker):
    from handlers.user_handlers import cmd_private, private_mode_users
    import handlers.user_handlers as uh
    private_mode_users.discard(777)
    uh.check_ollama_available = AsyncMock(return_value=False)
    mocker.patch("handlers.user_handlers.check_ollama_available", new=AsyncMock(return_value=False))
    msg = make_msg("/private", user_id=777)
    await cmd_private(msg)
    assert msg.answer.call_count >= 1
    call_text = msg.answer.call_args[0][0]
    assert "Ollama" in call_text or "қосылмаған" in call_text.lower() or "ollama" in call_text.lower()
