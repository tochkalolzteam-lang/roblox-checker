import os
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
# Читаем ID, убираем лишние пробелы и создаем список
admin_raw = os.getenv("ADMIN_ID", "")
ADMIN_IDS = [int(i.strip()) for i in admin_raw.split(",") if i.strip()]

bot = Bot(token=TOKEN)
dp = Dispatcher()