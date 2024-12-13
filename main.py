import logging
import http.client
import urllib.parse
import json
from aiogram import Bot, Dispatcher, types, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from config import TOKEN, API_KEY
import asyncio

# Настройка логирования
logging.basicConfig(level=logging.INFO)

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

class NewsState(StatesGroup):
    country = State()
    category = State()
    language = State()

def fetch_news(country, category, language):
    conn = http.client.HTTPConnection('api.mediastack.com')
    params = urllib.parse.urlencode({
        'access_key': API_KEY,
        'countries': country,
        'categories': category,
        'languages': language,
        'sort': 'published_desc',
        'limit': 10,
    })

    conn.request('GET', '/v1/news?{}'.format(params))
    res = conn.getresponse()
    data = res.read()
    return json.loads(data.decode('utf-8'))

@router.message(Command(commands=['start', 'help']))
async def send_welcome(message: types.Message, state: FSMContext):
    await message.reply("Привет! Я бот для получения новостей. Укажите страну, введя ее код (например, 'us' для США).")
    await state.set_state(NewsState.country)

@router.message(NewsState.country)
async def process_country(message: types.Message, state: FSMContext):
    await state.update_data(country=message.text.lower())
    await message.reply("Теперь укажите категорию новостей (например, 'business').")
    await state.set_state(NewsState.category)

@router.message(NewsState.category)
async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text.lower())
    await message.reply("Укажите язык новостей (например, 'en' для английского).")
    await state.set_state(NewsState.language)

@router.message(NewsState.language)
async def process_language(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    country = user_data['country']
    category = user_data['category']
    language = message.text.lower()

    try:
        news_data = fetch_news(country, category, language)
        if 'data' in news_data:
            news_items = news_data['data']
            response = ""
            if news_items:
                for item in news_items:
                    response += f"{item.get('title')}\n{item.get('description')}\n\n"
                response = response.strip()
            else:
                response = "Новости не найдены."
        else:
            response = "Ошибка получения данных."
    except Exception as e:
        response = f"Произошла ошибка: {e}"

    await message.reply(response)
    await state.clear()

async def main():
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())