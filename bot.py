import json
import time
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.utils.markdown import hbold, hlink  # Import directly
from config import token
from main import get_wokr_list

# Initialize Bot and Dispatcher
bot = Bot(token=token)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    start_buttons = [
        [KeyboardButton(text="Java")],
        [KeyboardButton(text="Python")],
        [KeyboardButton(text="Ruby")],
        [KeyboardButton(text="SQL")]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=start_buttons, resize_keyboard=True)
    await message.answer("Вибери мову програмування яка тебе цікавить", reply_markup=keyboard)

async def send_job_list(message: types.Message, language: str):
    await message.answer("Очікуйте...", parse_mode=ParseMode.HTML)
    await get_wokr_list(lng=language)

    with open("work.json", encoding="utf-8") as file:
        data = json.load(file)

    for index, item in enumerate(data):
        card = (
            f'{hlink(item.get("title"), item.get("link"))}\n'  # Use `hlink` directly
            f'{hbold("Місто: ")}{item.get("city")}\n'
            f'{hbold("Зарплата: ")}{item.get("salary")}\n'
        )

        if index % 20 == 0:
            time.sleep(3)

        await message.answer(card, parse_mode=ParseMode.HTML)

# Handlers for different programming languages
@dp.message(F.text == "Python")
async def get_python_list(message: types.Message):
    await send_job_list(message, "python")

@dp.message(F.text == "Java")
async def get_java_list(message: types.Message):
    await send_job_list(message, "Java")

@dp.message(F.text == "Ruby")
async def get_ruby_list(message: types.Message):
    await send_job_list(message, "Ruby")

@dp.message(F.text == "SQL")
async def get_sql_list(message: types.Message):
    await send_job_list(message, "SQL")

# Main function to start polling
def main():
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
