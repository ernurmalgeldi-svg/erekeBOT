import pytest
from unittest.mock import AsyncMock, MagicMock, patch


def make_msg(text="", user_id=11111):
    from_user = MagicMock()
    from_user.id = user_id
    chat = MagicMock()
    chat.id = user_id
    msg = MagicMock()
    msg.from_user = from_user
    msg.chat = chat
    msg.text = text
    sent = MagicMock()
    sent.edit_text = AsyncMock()
    msg.answer = AsyncMock(return_value=sent)
    return msg


@pytest.mark.asyncio
async def test_mcp_files_success(mocker):
    """MCP сервер сәтті жауап берген кезде файлдар тізімі көрсетіледі."""
    from handlers.mcp_handlers import handle_files_command

    # stdio_client мок
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.content = [MagicMock(text="file1.txt\nfile2.txt")]
    mock_session.initialize = AsyncMock()
    mock_session.call_tool = AsyncMock(return_value=mock_result)

    mock_cm_session = MagicMock()
    mock_cm_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm_session.__aexit__ = AsyncMock(return_value=None)

    mock_cm_stdio = MagicMock()
    mock_cm_stdio.__aenter__ = AsyncMock(return_value=(AsyncMock(), AsyncMock()))
    mock_cm_stdio.__aexit__ = AsyncMock(return_value=None)

    mocker.patch("handlers.mcp_handlers.stdio_client", return_value=mock_cm_stdio)
    mocker.patch("handlers.mcp_handlers.ClientSession", return_value=mock_cm_session)

    msg = make_msg("/files")
    await handle_files_command(msg)

    assert msg.answer.call_count >= 1


@pytest.mark.asyncio
async def test_mcp_files_error(mocker):
    """MCP сервер қатесі кезінде пайдаланушыға хабарлама жіберіледі."""
    from handlers.mcp_handlers import handle_files_command

    mocker.patch(
        "handlers.mcp_handlers.stdio_client",
        side_effect=Exception("npx not found")
    )

    msg = make_msg("/files")
    await handle_files_command(msg)

    # edit_text немесе answer арқылы қате хабарламасы жіберілуі керек
    sent = msg.answer.return_value
    assert msg.answer.call_count >= 1 or sent.edit_text.call_count >= 1

