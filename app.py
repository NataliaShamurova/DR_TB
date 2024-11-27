import logging
import os
from venv import logger
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from dotenv import find_dotenv, load_dotenv

from handlers.user_group import user_group_router
from handlers.user_private import user_private_router
from common.button_menu_list import private

load_dotenv(find_dotenv())

#Настройка логгирования

logging.basicConfig(
    filename='bot.log',  # Имя файла для записи логов
    filemode='a',  # Режим записи (append)
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ALLOWED_UPDATES = ['message, edit_message']  #Ограничиваем типы апдейтов, которые приходят к боту

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.include_router(user_private_router)
dp.include_router(user_group_router)


async def main():
    logger.info("Bot is starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


@dp.errors()
async def error_handler(update: types.Update, exception: Exception):
    logger.error(f'Update: {update} caused error: {exception}')


asyncio.run(main())
