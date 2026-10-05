import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiohttp import web

# Токен вашего бота
API_TOKEN = '8960595836:AAF-9JLDFxYYZceo_0R-q0aulPZR429Cm8A'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Бот успешно запущен и работает на Render!")

# Простейший веб-сервер для ответа на проверки Render
async def handle_ping(request):
    return web.Response(text="OK")

async def main():
    # Запуск веб-сервера на порту, который запрашивает Render
    app = web.Application()
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    # Запуск бота (long polling)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
