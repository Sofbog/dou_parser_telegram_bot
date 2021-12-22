import json
from aiogram import Bot, Dispatcher, executor, types
from aiogram.utils.markdown import hbold, hlink
from aiogram.dispatcher.filters import Text
from config import token
from main import get_wokr_list
import time


bot = Bot(token=token, parse_mode=types.ParseMode.HTML)
dp = Dispatcher(bot)


@dp.message_handler(commands="start")
async def start(message: types.Message):
    start_buttons = ["Java", "Python", "Ruby", "SQL"]
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*start_buttons)

    await message.answer("Вибери мову програмування яка тебе цікавить", reply_markup=keyboard)


@dp.message_handler(Text(equals="Python"))
async def get_python_list(message: types.Message):
    await message.answer('Очікуйте...')

    get_wokr_list(lng='python')

    with open('work.json', encoding="utf-8") as file:
        data = json.load(file)

    for index, item in enumerate(data):
        card = f'{hlink(item.get("title"), item.get("link"))}\n' \
              f'{hbold("Місто: ")}{item.get("city")}\n' \
              f'{hbold("Зарплата: ")}{item.get("salary")}\n' \

        if index % 20 == 0:
            time.sleep(3)

        await message.answer(card)


@dp.message_handler(Text(equals="Java"))
async def get_java_list(message: types.Message):
    await message.answer('Очікуйте...')

    get_wokr_list(lng='Java')

    with open('work.json', encoding="utf-8") as file:
        data = json.load(file)

    for index, item in enumerate(data):
        card = f'{hlink(item.get("title"), item.get("link"))}\n' \
               f'{hbold("Місто: ")}{item.get("city")}\n' \
               f'{hbold("Зарплата: ")}{item.get("salary")}\n' \


        if index % 20 == 0:
            time.sleep(3)

        await message.answer(card)


@dp.message_handler(Text(equals="Ruby"))
async def get_ruby_list(message: types.Message):
    await message.answer('Очікуйте...')

    get_wokr_list(lng='Ruby')

    with open('work.json', encoding="utf-8") as file:
        data = json.load(file)

    for index, item in enumerate(data):
        card = f'{hlink(item.get("title"), item.get("link"))}\n' \
               f'{hbold("Місто: ")}{item.get("city")}\n' \
               f'{hbold("Зарплата: ")}{item.get("salary")}\n' \


        if index % 20 == 0:
            time.sleep(3)

        await message.answer(card)


@dp.message_handler(Text(equals="SQL"))
async def get_sql_list(message: types.Message):
    await message.answer('Очікуйте...')

    get_wokr_list(lng='SQL')

    with open('work.json', encoding="utf-8") as file:
        data = json.load(file)

    for index, item in enumerate(data):
        card = f'{hlink(item.get("title"), item.get("link"))}\n' \
               f'{hbold("Місто: ")}{item.get("city")}\n' \
               f'{hbold("Зарплата: ")}{item.get("salary")}\n' \

        if index % 20 == 0:
            time.sleep(3)

        await message.answer(card)


def main():
    executor.start_polling(dp)


if __name__ == '__main__':
    main()
