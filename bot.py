import asyncio
import logging
import os
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
from dotenv import load_dotenv
from yandex_gpt import generate_yandex_gpt_quote

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()
logging.basicConfig(level=logging.INFO)

def update_stats(user_id: int, category: str):
    stats_file = "stats.json"
    try:
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
        else:
            stats = {}
        user_key = str(user_id)
        stats.setdefault(user_key, {}).setdefault(category, 0)
        stats[user_key][category] += 1
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Ошибка обновления статистики: {e}")

def get_user_stats(user_id: int) -> str:
    stats_file = "stats.json"
    try:
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats = json.load(f)
            user_stats = stats.get(str(user_id), {})
            if not user_stats:
                return "📊 Вы пока не использовали ни одной категории."

            lines = []
            for cat, count in user_stats.items():
                if isinstance(count, int):
                    lines.append(f"— Вы выбирали категорию «{cat}» {count} раз(а)")
                else:
                    lines.append(f"⚠️ Ошибка в категории «{cat}»: данные повреждены.")
            return "\n".join(lines)
        return "📊 Статистика пока пуста."
    except Exception as e:
        logging.error(f"Ошибка чтения статистики: {e}")
        return "⚠️ Ошибка при чтении статистики."

keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🚀 Старт")],
        [KeyboardButton(text="📋 Категории"), KeyboardButton(text="⏰ Напоминание")],
        [KeyboardButton(text="📊 Статистика")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
@dp.message(lambda message: message.text == "🚀 Старт")
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот с мотивационными цитатами 💬", reply_markup=keyboard)

@dp.message(lambda message: message.text == "🔙 Назад")
async def go_back(message: types.Message):
    await message.answer("🔙 Вернулись в главное меню", reply_markup=keyboard)

@dp.message(Command("напоминание"))
@dp.message(lambda message: message.text == "⏰ Напоминание")
async def set_reminder(message: types.Message):
    user_id = message.from_user.id

    async def send_daily(uid):
        try:
            quote = await generate_yandex_gpt_quote("Саморазвитие")
        except Exception as e:
            quote = "⚠️ Не удалось получить цитату. Попробуйте позже."
            logging.error(f"Ошибка генерации: {e}")
        await bot.send_message(chat_id=uid, text=f"🌅 Утреняя цитата:\n\n{quote}")

    scheduler.add_job(send_daily, trigger="cron", hour=9, minute=0, args=[user_id], id=f"reminder_{user_id}")
    await message.answer("✅ Ежедневное напоминание установлено на 9:00")

@dp.message(lambda message: message.text == "📋 Категории")
@dp.message(Command("категории"))
async def show_categories(message: types.Message):
    categories = ["Бизнес", "Саморазвитие", "Любовь к себе", "Спорт"]
    category_keyboard = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cat)] for cat in categories] + [[KeyboardButton(text="🔙 Назад")]],
        resize_keyboard=True
    )
    await message.answer("Выберите категорию:", reply_markup=category_keyboard)

@dp.message(lambda message: message.text in ["Бизнес", "Саморазвитие", "Любовь к себе", "Спорт"])
async def handle_category(message: types.Message):
    category = message.text
    update_stats(message.from_user.id, category)
    try:
        quote = await generate_yandex_gpt_quote(category)
    except Exception as e:
        quote = "⚠️ Не удалось получить цитату. Попробуйте позже."
        logging.error(f"Ошибка генерации: {e}")

    await message.answer(f"✨ {quote}")

@dp.message(Command("статистика"))
@dp.message(lambda message: message.text == "📊 Статистика")
async def show_stats(message: types.Message):
    stats = get_user_stats(message.from_user.id)
    await message.answer(f"📈 Ваша статистика:\n{stats}")

async def main():
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())