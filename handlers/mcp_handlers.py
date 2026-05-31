import os
from aiogram import Router, F
from aiogram.types import Message
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

router = Router()

# 🛠️ MCP СЕРВЕРДІҢ ПАРАМЕТРЛЕРІ
# Сәлден кейін өз папкаңның нақты жолын (absolute path) жаз
ALLOWED_DIR = os.path.abspath("./shared_files") 

# Егер бұл папка жоқ болса, автоматты түрде құрылады
if not os.path.exists(ALLOWED_DIR):
    os.makedirs(ALLOWED_DIR)

server_params = StdioServerParameters(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-filesystem", ALLOWED_DIR],
    env=None
)

@router.message(F.text == "/files")
async def handle_files_command(message: Message):
    status_msg = await message.answer("📁 MCP сервер арқылы файлдарды оқып жатырмын...")
    
    try:
        # MCP серверге stdio транспорты арқылы қосылу (tools/list және tools/call)
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Сессияны иницилизация жасау
                await session.initialize()
                
                # ИИ-сіз тікелей MCP құралын (tool) шақыру
                # Ресми серверде папканы көру құралы 'list_directory' деп аталады
                result = await session.call_tool(
                    name="list_directory",
                    arguments={"path": ALLOWED_DIR}
                )
                
                # Нәтижені өңдеу
                if result and result.content:
                    files_text = result.content[0].text
                    await status_msg.edit_text(f"📄 **Рұқсат етілген директория құрамы ({ALLOWED_DIR}):**\n\n{files_text}")
                else:
                    await status_msg.edit_text("📁 Папка іші бос немесе файлдар табылмады.")
                    
    except Exception as e:
        print(f"MCP Filesystem Error: {e}")
        await status_msg.edit_text("❌ MCP сервермен байланыс орнату кезінде қате шықты. Node.js немесе npx орнатылғанын тексеріңіз.")