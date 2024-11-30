import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv, find_dotenv

from handlers.handler_admin import handler_admin_router
from handlers.handler_user import handler_user_router
from handlers.user_group import handler_user_group_router
from logging_config import setup_logging

# Загружаем переменные окружения
load_dotenv(find_dotenv())

from db.engine import create_db, session_maker, drop_db
from middlewares.db import DataBaseSession

# Настройка логгирования
app_logger = setup_logging("main", "logs/main.log")

# ALLOWED_UPDATES = ['message, edit_message']  # Ограничиваем типы апдейтов, которые приходят к боту

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.a_admins_list = []  # список администраторов наполняем из user_group

dp = Dispatcher()

dp.include_router(handler_user_router)
dp.include_router(handler_user_group_router)
dp.include_router(handler_admin_router)


async def on_startup(bot):
    # await drop_db() # Убираем старые таблицы, надо заккоментировать
    await create_db()


async def on_shutdown(bot):
    # app_logger.info('Бот остановлен')  # Используем logging для записи информации
    print('Бот остановлен')


async def main():
    app_logger.info("Bot is starting...")  # Используем app_logger
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    # await create_db()
    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats()) #Закомментировать (создан для удаления)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())  # Подтягиваются автоматом все апдейты


async def error_handler(update: types.Update, exception: Exception):
    app_logger.error(f'Update: {update} caused error: {exception}')


if __name__ == '__main__':
    asyncio.run(main())
