import json
import os
from http.server import BaseHTTPRequestHandler

from aiogram import Bot, Dispatcher, types
from aiogram.types import Update
import google.generativeai as genai

# =========================
# 🔑 ENV ПЕРЕМЕННЫЕ
# =========================
API_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# =========================
# 🤖 AI
# =========================
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-pro")

# =========================
# 📦 ДАННЫЕ (в памяти)
# ⚠️ Vercel не хранит файлы!
# =========================
data = {
    "players": [],
    "tasks": [],
    "storage": {}
}

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


# =========================
# 🧠 AI распределение
# =========================
async def smart_distribution(players, task):
    prompt = f"""
Игроки: {players}
Задача: {task}

Распредели справедливо.
Формат:
username - количество
"""
    response = model.generate_content(prompt)
    return response.text


# =========================
# 🚀 СТАРТ
# =========================
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer(
            "👑 Панель админа\n\n"
            "Напиши:\n"
            "add username\n"
            "task 100 железа\n"
            "announce текст"
        )


# =========================
# 🧠 ВСЯ ЛОГИКА
# =========================
@dp.message_handler()
async def all_messages(message: types.Message):
    text = message.text

    # ➕ добавить игрока
    if text.startswith("add ") and message.from_user.id == ADMIN_ID:
        username = text.split(" ", 1)[1].replace("@", "")
        if username not in data["players"]:
            data["players"].append(username)
            await message.answer(f"✅ @{username} добавлен")

    # 📋 задача
    elif text.startswith("task "):
        task = text.split(" ", 1)[1]

        if not data["players"]:
            return await message.answer("Нет игроков")

        result = await smart_distribution(data["players"], task)

        await message.answer(f"📋 Задание:\n\n{result}")

    # 📢 объявление
    elif text.startswith("announce ") and message.from_user.id == ADMIN_ID:
        msg = text.split(" ", 1)[1]

        for p in data["players"]:
            try:
                await bot.send_message(p, f"📢 {msg}")
            except:
                pass

    # 📦 склад (демо)
    elif message.photo:
        data["storage"]["ресурс"] = data["storage"].get("ресурс", 0) + 10
        await message.answer("📦 Добавлено +10 ресурса (демо)")


# =========================
# 🌐 WEBHOOK (Vercel)
# =========================
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)

        update = Update(**json.loads(body))

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(dp.process_update(update))

        self.send_response(200)
        self.end_headers()
      
