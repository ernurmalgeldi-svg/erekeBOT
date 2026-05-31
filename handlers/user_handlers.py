from services.calendar_service import get_auth_url, exchange_code, create_event, list_events
from services.image_service import generate_image, analyze_image
from services.search_service import search_web, format_search_results
from services.voice_service import transcribe_audio
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart, Command
from utils.mcp_aggregator import get_remote_docker_status, get_mcp_tools_list
from utils.db_manager import db  

import groq
import os
import logging

from services.benchmark_service import run_benchmark
from services.model_manager_service import pull_model, list_models
from services.function_calling_service import run_with_tools

from services.ollama_service import get_ollama_response, check_ollama_available
private_mode_users: set = set()
from services.rag_service import search_similar, load_sample_documents, add_document, init_db
router = Router()
logger = logging.getLogger(__name__)

groq_client = groq.AsyncGroq(api_key=os.getenv("GROQ_API_KEY"))

# 👑 .env файлынан админ ID-ін оқимыз
ADMIN_ID = os.getenv("ADMIN_ID")

# 🎛️ ӘДЕМІ ИНЛАЙН БАТЫРМАЛАР МӘЗІРІ (KEYBOARD MAP)
def get_user_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📁 /files", callback_data="btn_files"),
            InlineKeyboardButton(text="☀️ /weather Almaty", callback_data="btn_weather")
        ],
        [
            InlineKeyboardButton(text="⏱️ /time", callback_data="btn_time"),
            InlineKeyboardButton(text="🧮 /calc 2+2", callback_data="btn_calc")
        ],
        [
            InlineKeyboardButton(text="📋 /resources", callback_data="btn_resources"),
            InlineKeyboardButton(text="💬 /prompts", callback_data="btn_prompts")
        ],
        [
            InlineKeyboardButton(text="🔧 /tools", callback_data="btn_tools"),
            InlineKeyboardButton(text="📡 /mcpstatus", callback_data="btn_mcpstatus")
        ],
        [
            InlineKeyboardButton(text="👤 /myrole", callback_data="btn_myrole"),
            InlineKeyboardButton(text="🗑️ /clear", callback_data="btn_clear")
        ]
    ])
    return keyboard


# 🚀 /START КОМАНДАСЫ
@router.message(CommandStart())
async def cmd_start(message: Message):
    welcome_text = (
        "👋 **Сәлем, радной! Мен ақылды MCP ботпын.**\n\n"
        "📚 Barklyq funksiyalardy koru ushin tomendegi batyrmalardy qoldan nemeese ** /help ** komandasyn jaz!"
    )
    await message.answer(welcome_text, reply_markup=get_user_menu_keyboard())


# 📚 /HELP КОМАНДАСЫ (ДӘЛ ҚАСЫҢДАҒЫ БАЛАНЫКІНДЕЙ ӘДЕМІ МӘЗІР)
@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📚 **Командалар тізімі (Admin 👑)**\n\n"
        "⎯⎯⎯⎯⎯⎯ **Жалпы командалар** ⎯⎯⎯⎯⎯⎯\n"
        "📁 `/files` — Файлдарды қарау\n"
        "☀️ `/weather Almaty` — Ауа райын білу\n"
        "⏱️ `/time` — Ағымдағы уақыт\n"
        "🧮 `/calc 2+2` — Калькулятор есептеу\n"
        "📋 `/resources` — Қорларды тексеру\n"
        "💬 `/prompts` — Промптар тізімі\n"
        "🔧 `/tools` — Қолжетімді құралдар\n"
        "📡 `/mcpstatus` — MCP серверінің күйі\n"
        "👤 `/myrole` — Пайдаланушы рөлі\n"
        "🗑️ `/clear` — Контекстті тазалау\n\n"
        "⎯⎯⎯⎯⎯⎯ **Мұғалім командалары** ⎯⎯⎯⎯⎯⎯\n"
        "📊 `/stats` — Жалпы статистика\n"
        "👥 `/users` — Қолданушылар тізімі\n\n"
        "⎯⎯⎯⎯⎯⎯ **Admin командалары** ⎯⎯⎯⎯⎯⎯\n"
        "📥 `/export` — Базаны экспорттау\n"
        "🔍 `/mcpcall` — Тікелей MCP шақыру"
    )
    await message.answer(help_text, reply_markup=get_user_menu_keyboard())


# 👑 АДМИН ПАНЕЛЬГЕ КІРУ КОМАНДАСЫ
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    user_id = str(message.from_user.id)
    if ADMIN_ID and user_id == str(ADMIN_ID):
        await message.answer(
            "👑 **ҚОШ КЕЛДІҢІЗ, АДМИНИСТРАТОР!**\n\n"
            "🔐 Сіз жүйеге **Админ** рөлімен кірдіңіз.\n"
            "🛠 Серверді және Docker контейнерлерін басқару толық ашық."
        )
    else:
        await message.answer("❌ **РҰҚСАТ ЖОҚ!**\n\n👤 Сіздің рөліңіз: **Пайдаланушы (User)**.")


# 👤 ӨЗ РӨЛІН ТЕКСЕРУ КОМАНДАСЫ (/myrole)
@router.message(Command("myrole"))
async def cmd_myrole(message: Message):
    user_id = str(message.from_user.id)
    if ADMIN_ID and user_id == str(ADMIN_ID):
        await message.answer("👑 Сіздің жүйедегі рөліңіз — **Администратор (Admin)**. Барлық рұқсаттар ашық!")
    else:
        await message.answer("👤 Сіздің жүйедегі рөліңіз — **Пайдаланушы (User)**. Қарапайым құқықтар.")

@router.message(Command("imagine"))
async def cmd_imagine(message: Message, bot):
    prompt = message.text.replace("/imagine", "").strip()

    if not prompt:
        await message.answer(
            "🎨 <b>Сурет генерациясы</b>\n\n"
            "Мысалы:\n"
            "<code>/imagine sunset over mountains</code>\n"
            "<code>/imagine cute cat in space</code>",
            parse_mode="HTML"
        )
        return

    msg = await message.answer("🎨 <i>Сурет жасалуда, күт...</i>", parse_mode="HTML")

    try:
        image_bytes = await generate_image(prompt)

        if image_bytes:
            from aiogram.types import BufferedInputFile
            await bot.send_photo(
                chat_id=message.chat.id,
                photo=BufferedInputFile(image_bytes, filename="image.png"),
                caption=f"🎨 <b>Prompt:</b> {prompt}",
                parse_mode="HTML"
            )
            await msg.delete()
        else:
            await msg.edit_text("⏳ Модель жүктелуде, 1 минуттан кейін қайта көр!")

    except Exception as e:
        await msg.edit_text(f"❌ Қате: {str(e)}")


@router.message(F.photo)
async def handle_photo(message: Message, bot):
    msg = await message.answer("🔍 <i>Сурет анализделуде...</i>", parse_mode="HTML")

    try:
        photo = message.photo[-1]
        file = await bot.get_file(photo.file_id)
        
        image_bytes = await bot.download_file(file.file_path)
        image_data = image_bytes.read()

        question = message.caption if message.caption else "Суретте не бар? Қазақша түсіндір."
        result = await analyze_image(image_data, question)

        await msg.edit_text(
            f"🖼 <b>Сурет анализі:</b>\n\n{result}",
            parse_mode="HTML"
        )

    except Exception as e:
        await msg.edit_text(f"❌ Қате: {str(e)}")

@router.message(Command("private"))
async def cmd_private(message: Message):
    user_id = message.from_user.id

    if user_id in private_mode_users:
        private_mode_users.discard(user_id)
        await message.answer(
            "🌐 <b>Қалыпты режим</b> — Groq API\n\n"
            "Енді хабарламаларыңыз Groq-қа жіберіледі.\n"
            "Қайта /private десе — жергілікті режим қосылады.",
            parse_mode="HTML"
        )
    else:
        is_available = await check_ollama_available()
        if not is_available:
            await message.answer(
                "❌ <b>Ollama іске қосылмаған!</b>\n\n"
                "Терминалда мынаны жаз:\n"
                "<code>ollama serve</code>\n\n"
                "Содан кейін қайта /private деп көр.",
                parse_mode="HTML"
            )
            return

        private_mode_users.add(user_id)
        await message.answer(
            "🔒 <b>Жергілікті режим ҚОСЫЛДЫ</b>\n\n"
            "✅ Хабарламаларың <b>Ollama</b> арқылы өңделеді\n"
            "✅ Ештеңе бұлтқа кетпейді\n"
            "✅ Модель: <code>llama3.2:3b</code>\n\n"
            "🔓 Өшіру үшін қайта /private деп жаз.",
            parse_mode="HTML"
        )
async def cmd_myrole(message: Message):
    user_id = str(message.from_user.id)
    if ADMIN_ID and user_id == str(ADMIN_ID):
        await message.answer("👑 Сіздің жүйедегі рөліңіз — **Администратор (Admin)**. Барлық рұқсаттар ашық!")
    else:
        await message.answer("👤 Сіздің жүйедегі рөліңіз — **Пайдаланушы (User)**. Қарапайым құқықтар.")


# 📜 POSTGRESQL БАЗАСЫНАН ТАРИХТЫ ШЫҒАРУ (/history)
@router.message(Command("history"))
async def show_history(message: Message):
    user_id = message.from_user.id
    history = await db.get_chat_history(user_id=user_id, limit=10)
    
    if not history:
        await message.answer("🗄️ База бос, тарих сақталмаған!")
        return
        
    history_text = "📜 **Сіздің хабарламаларыңыздың тарихы (PostgreSQL):**\n\n"
    for msg in history:
        role_label = "👤 Пайдаланушы" if msg["role"] == "user" else "🤖 Бот"
        history_text += f"🔹 **{role_label}:** {msg['content']}\n\n"
        
    await message.answer(history_text)


# 🎤 ДАУЫСТЫҚ ХАБАРЛАМАЛАРДЫ (ГОЛОСОВОЙ) ӨҢДЕУ
@router.message(F.voice)
async def handle_voice_message(message: Message, bot):
    await message.answer("🎧 Дауыстық хабарлама қабылданды, өңделуде...")
    try:
        voice_file_id = message.voice.file_id
        file = await bot.get_file(voice_file_id)
        file_path = file.file_path

        # Файл өлшемін тексер
        file_size_mb = message.voice.file_size / (1024 * 1024)
        if file_size_mb > 25:
            await message.answer("❌ Файл тым үлкен! Максимум 25 МБ.")
            return

        local_filename = "voice_message.ogg"
        await bot.download_file(file_path, local_filename)

        # ffmpeg арқылы конвертация және транскрипция
        user_text = await transcribe_audio(local_filename)

        if local_filename and os.path.exists(local_filename):
            os.remove(local_filename)

        if user_text.startswith("❌"):
            await message.answer(user_text)
            return

        await message.answer(f"🗣 <b>Сіздің сөзіңіз:</b>\n<i>{user_text}</i>", parse_mode="HTML")
        await process_text_logic(message, user_text)

    except Exception as e:
        logger.error(f"Голосовой қатесі: {e}")
        await message.answer("❌ Кешіріңіз, дауыстық хабарламаны тану сәтсіз аяқталды.")
@router.message(Command("benchmark"))
async def cmd_benchmark(message: Message):
    await message.answer("⏳ Бенчмарк басталды... 20 сұрақ Groq + Ollama арқылы тексерілуде. 2-3 минут күт!")
    try:
        filename = await run_benchmark()
        from aiogram.types import FSInputFile
        await message.answer_document(
            document=FSInputFile(filename),
            caption="📊 Бенчмарк дайын! Groq vs Ollama нәтижелері."
        )
    except Exception as e:
        await message.answer(f"❌ Қате: {str(e)}")
        
    except Exception as e:
        await message.answer(f"❌ Қате: {str(e)}")


# 📝 ЖАЙ МӘТІНДІК ХАБАРЛАМАЛАРДЫ ҚАБЫЛДАУ
@router.message(F.text & ~F.text.startswith("/"))
async def handle_text_message(message: Message):
    await process_text_logic(message, message.text)

# 🧠 БАСТЫ ИИ ЛОГИКАСЫ ЖӘНЕ ДИНАМИКАЛЫҚ РӨЛДЕРДІ БАСҚАРУ
async def process_text_logic(message: Message, user_text: str):
    user_id = message.from_user.id
    user_text_lower = user_text.lower()

    # --- ЗАДАЧА 13: Приватты режим ---
    if user_id in private_mode_users:
        messages_context = [
            {
                "role": "system",
                "content": "Сен қазақша сөйлейтін көмекші ассистентсің. Қысқа және анық жауап бер."
            },
            {"role": "user", "content": user_text}
        ]
        processing_msg = await message.answer("🔒 <i>Lokal Ollama өңдеуде...</i>", parse_mode="HTML")
        bot_answer = await get_ollama_response(messages_context)
        await processing_msg.delete()
        await message.answer(
            f"🔒 <b>[PRIVATE · Ollama]</b>\n\n{bot_answer}",
            parse_mode="HTML",
            reply_markup=get_user_menu_keyboard()
        )
        return
    # --- Қалыпты Groq режимі төменде жалғасады ---
    
    if "рөлім қандай" in user_text_lower or "ролим кандай" in user_text_lower or "рөл" in user_text_lower:
        if ADMIN_ID and str(user_id) == str(ADMIN_ID):
            bot_reply = "👑 Сіздің жүйедегі рөліңіз — **Администратор (Admin)**. Барлық рұқсаттар ашық!"
        else:
            bot_reply = "👤 Сіздің жүйедегі рөліңіз — **Пайдаланушы (User)**. Сізде қарапайым құқықтар."
        await message.answer(bot_reply, reply_markup=get_user_menu_keyboard())
        await db.save_message(user_id=user_id, user_message=user_text, bot_response=bot_reply)
        return

    keywords = ["статус", "docker", "докер", "контейнер", "тексер", "сервер", "жағдайы"]
    should_use_tool = any(word in user_text_lower for word in keywords)
    
    try:
        db_history = await db.get_chat_history(user_id=user_id)
        current_role = "Admin" if ADMIN_ID and str(user_id) == str(ADMIN_ID) else "User"
        
        messages_context = [
            {
                "role": "system", 
                "content": f"Сен қазақша сөйлейтін ИИ ассистентсің. Пайдаланушының жүйедегі рөлі: {current_role}."
            }
        ]
        
        if db_history:
            for msg in db_history:
                messages_context.append({"role": msg["role"], "content": msg["content"]})
            
        messages_context.append({"role": "user", "content": user_text})

        if should_use_tool:
            await message.answer("🔄 Docker контейнердің ішкі жүйесі тексерілуде...")
            status_result = await get_remote_docker_status()
            
            ai_explain = await groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "Docker контейнерінің статусын қазақша түсіндіріп бер."},
                    {"role": "user", "content": f"Status: {status_result}"}
                ]
            )
            bot_answer = ai_explain.choices[0].message.content
            await message.answer(f"🐳 **Docker Жауабы:**\n\n{bot_answer}", reply_markup=get_user_menu_keyboard())
            await db.save_message(user_id=user_id, user_message=user_text, bot_response=bot_answer)
            return
        
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_context
        )
        
        if response.choices[0].message.content:
            bot_answer = response.choices[0].message.content
            await message.answer(bot_answer, reply_markup=get_user_menu_keyboard())
            await db.save_message(user_id=user_id, user_message=user_text, bot_response=bot_answer)
            
    except Exception as e:
        logger.error(f"Қате пайда болды: {e}")
        await message.answer("❌ Кешіріңіз, сұранысты өңдеу кезінде ішкі қате шықты.")


@router.callback_query(F.data == "btn_files")
      
      
       
async def cb_files(callback):
    await callback.message.answer("📁 /files командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_weather")
async def cb_weather(callback):
    await callback.message.answer("☀️ /weather Almaty командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_time")
async def cb_time(callback):
    await callback.message.answer("⏱️ /time командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_calc")
async def cb_calc(callback):
    await callback.message.answer("🧮 /calc 2+2 командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_resources")
async def cb_resources(callback):
    await callback.message.answer("📋 /resources командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_prompts")
async def cb_prompts(callback):
    await callback.message.answer("💬 /prompts командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_tools")
async def cb_tools(callback):
    await callback.message.answer("🔧 /tools командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_mcpstatus")
async def cb_mcpstatus(callback):
    await callback.message.answer("📡 /mcpstatus командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_myrole")
async def cb_myrole(callback):
    await callback.message.answer("👤 /myrole командасы")
    await callback.answer()

@router.callback_query(F.data == "btn_clear")
async def cb_clear(callback):
    await callback.message.answer("🗑️ /clear командасы")
    await callback.answer()
    from services.rag_service import search_similar, load_sample_documents, add_document, init_db

@router.message(Command("ask"))
async def cmd_ask(message: Message):
    query = message.text.replace("/ask", "").strip()
    
    if not query:
        await message.answer("❓ Мысалы: /ask Python дегеніміз не?")
        return

    await message.answer("🔍 Іздеуде...")
    
    docs = search_similar(query, top_k=3)
    
    if not docs:
        await message.answer("📭 Деректер базасында ештеңе табылмады.")
        return

    context = "\n\n".join([f"📄 {doc}" for doc in docs])
    
    messages_context = [
        {
            "role": "system",
            "content": f"Сен көмекші ассистентсің. Төмендегі деректерді пайдаланып жауап бер:\n\n{context}"
        },
        {"role": "user", "content": query}
    ]
    
    response = await groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_context
    )
    
    bot_answer = response.choices[0].message.content
    await message.answer(
        f"🧠 <b>[RAG жауабы]</b>\n\n{bot_answer}\n\n"
        f"📚 <b>Қолданылған деректер:</b>\n{context}",
        parse_mode="HTML"
    )
@router.message(Command("tools_test"))
async def cmd_tools_test(message: Message):
    query = message.text.replace("/tools_test", "").strip()
    
    if not query:
        await message.answer(
            "🔧 <b>Function Calling тесті</b>\n\n"
            "Мысалдар:\n"
            "/tools_test Алматыда ауа райы қандай?\n"
            "/tools_test 25 * 48 есепте\n"
            "/tools_test Қазір сағат нешеде?",
            parse_mode="HTML"
        )
        return

    await message.answer("⚙️ <i>Ollama құралдарды іске қосуда...</i>", parse_mode="HTML")
    
    try:
        result = await run_with_tools(query)
        
        tool_info = ""
        if result["tool_calls"]:
            tool_info = "\n\n🔧 <b>Қолданылған құралдар:</b>\n"
            for tc in result["tool_calls"]:
                tool_info += f"▪️ <code>{tc['tool']}</code> → {tc['result']}\n"

        await message.answer(
            f"🤖 <b>[Function Calling · Ollama]</b>\n\n"
            f"{result['answer']}"
            f"{tool_info}",
            parse_mode="HTML",
            reply_markup=get_user_menu_keyboard()
        )
    except Exception as e:
        await message.answer(f"❌ Қате: {str(e)}")


@router.message(Command("gcal_auth"))
async def cmd_gcal_auth(message: Message):
    user_id = message.from_user.id
    auth_url = get_auth_url(user_id)
    await message.answer(
        "📅 <b>Google Calendar байланыстыру</b>\n\n"
        "1️⃣ Мына сілтемеге өт:\n"
        f"<a href='{auth_url}'>🔗 Google-ге кіру</a>\n\n"
        "2️⃣ Рұқсат бергеннен кейін код аласыз\n"
        "3️⃣ Кодты мына форматта жібер:\n"
        "<code>/gcal_code КОДЫҢЫЗ</code>",
        parse_mode="HTML",
        disable_web_page_preview=True
    )


@router.message(Command("gcal_code"))
async def cmd_gcal_code(message: Message):
    user_id = message.from_user.id
    code = message.text.replace("/gcal_code", "").strip()

    if not code:
        await message.answer("❌ Код жазыңыз: <code>/gcal_code КОДЫҢЫЗ</code>", parse_mode="HTML")
        return

    await message.answer("⏳ Тексерілуде...")
    success = exchange_code(user_id, code)

    if success:
        await message.answer("✅ <b>Google Calendar сәтті байланыстырылды!</b>\n\n"
                           "Енді /gcal_events немесе /gcal_add қолдана аласыз.",
                           parse_mode="HTML")
    else:
        await message.answer("❌ Код дұрыс емес, қайта көріңіз.")


@router.message(Command("gcal_events"))
async def cmd_gcal_events(message: Message):
    user_id = message.from_user.id
    result = await list_events(user_id)
    await message.answer(result, parse_mode="HTML")


@router.message(Command("gcal_add"))
async def cmd_gcal_add(message: Message):
    user_id = message.from_user.id
    args = message.text.replace("/gcal_add", "").strip().split("|")

    if len(args) < 3:
        await message.answer(
            "📅 <b>Оқиға қосу</b>\n\n"
            "Формат:\n"
            "<code>/gcal_add Кездесу|2026-06-01|14:00</code>",
            parse_mode="HTML"
        )
        return

    title = args[0].strip()
    date = args[1].strip()
    time = args[2].strip()

    result = await create_event(user_id, title, date, time)
    await message.answer(result, parse_mode="HTML")
    
@router.message(Command("search"))
async def cmd_search(message: Message):
    query = message.text.replace("/search", "").strip()

    if not query:
        await message.answer(
            "🔍 <b>Интернет іздеу</b>\n\n"
            "Мысалы:\n"
            "<code>/search Қазақстан астанасы</code>\n"
            "<code>/search Python tutorial 2024</code>",
            parse_mode="HTML"
        )
        return

    await message.answer("🔍 <i>Іздеуде...</i>", parse_mode="HTML")

    try:
        results = search_web(query, max_results=5)
        formatted = format_search_results(results)

        # Groq арқылы нәтижелерді қорыту
        context = "\n".join([r.get("body", "") for r in results])
        response = await groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Сен іздеу нәтижелерін қорытып, қысқаша жауап беретін ассистентсің."
                },
                {
                    "role": "user",
                    "content": f"Сұрақ: {query}\n\nІздеу нәтижелері:\n{context}"
                }
            ]
        )
        summary = response.choices[0].message.content

        await message.answer(
            f"🤖 <b>AI жауабы:</b>\n{summary}\n\n"
            f"🔍 <b>Іздеу нәтижелері:</b>\n{formatted}",
            parse_mode="HTML",
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Іздеу қатесі: {e}")
        await message.answer(f"❌ Қате: {str(e)}")
@router.message(Command("model"))
async def cmd_model(message: Message, bot):
    user_id = str(message.from_user.id)
    
    if not ADMIN_ID or user_id != str(ADMIN_ID):
        await message.answer("❌ Бұл команда тек <b>Админге</b> қол жетімді!", parse_mode="HTML")
        return

    args = message.text.split()
    
    if len(args) < 3 or args[1] != "pull":
        models = await list_models()
        models_text = "\n".join([f"▪️ {m}" for m in models]) if models else "Модельдер жоқ"
        await message.answer(
            "🤖 <b>Модель басқару</b>\n\n"
            "Жүктеу үшін:\n"
            "<code>/model pull llama3.2:1b</code>\n"
            "<code>/model pull qwen2.5:0.5b</code>\n\n"
            f"📦 <b>Қазір бар модельдер:</b>\n{models_text}",
            parse_mode="HTML"
        )
        return

    model_name = args[2]
    msg = await message.answer(
        f"⬇️ <b>{model_name}</b> жүктеу басталды...",
        parse_mode="HTML"
    )
    
    await pull_model(model_name, bot, message.chat.id, msg.message_id)
