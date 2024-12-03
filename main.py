import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from dotenv import load_dotenv, find_dotenv

from handlers.handler_admin import handler_admin_router
from handlers.handler_user import handler_user_router
from logging_config import setup_logging

# Загружаем переменные окружения
load_dotenv(find_dotenv())

from db.engine import create_db, session_maker
from middlewares.db import DataBaseSession

# Настройка логгирования
app_logger = setup_logging("main", "logs/main.log")

bot = Bot(token=os.getenv('TOKEN'), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
bot.a_admins_list = []  # Вносим id администратора/ов,

dp = Dispatcher()

dp.include_router(handler_user_router)
dp.include_router(handler_admin_router)


async def on_startup(bot):
    app_logger.info("Starting the bot...")
    # await drop_db() # Убираем старые таблицы, надо заккоментировать
    await create_db()


async def on_shutdown(bot):
    app_logger.info('Бот остановлен')


async def main():
    '''Функция main() является основной точкой запуска для бота, использующего библиотеку aiogram.
    Она отвечает за настройку логирования, регистрацию обработчиков событий старта и остановки бота,
    а также за управление вебхуками и процессом получения обновлений.

Логика работы:
Логирование: Функция начинается с записи в лог сообщение о старте бота с использованием app_logger.
Регистрация обработчиков событий:
Регистрация функции on_startup для обработки старта бота через dp.startup.register(on_startup).
Регистрация функции on_shutdown для обработки остановки бота через dp.shutdown.register(on_shutdown).
Мидлвар для работы с базой данных: Добавление мидлвара DataBaseSession в обработчик обновлений для обеспечения сессий с базой данных, используя session_pool и session_maker.
Удаление вебхуков: Функция удаляет вебхук с помощью метода bot.delete_webhook(drop_pending_updates=True), что гарантирует, что бот больше не будет получать обновления через вебхук.
Запуск получения обновлений: Используется метод dp.start_polling(), который начинает опрос бота для получения новых обновлений. Параметр allowed_updates фильтрует типы обновлений, которые бот будет обрабатывать, автоматически подбирая используемые типы через dp.resolve_used_update_types().
Обработка исключений: В случае возникновения ошибки в процессе выполнения основной логики, ошибка записывается в лог с уровнем error.'''
    try:
        app_logger.info("Bot is starting...")  # Используем app_logger
        dp.startup.register(on_startup)
        dp.shutdown.register(on_shutdown)

        dp.update.middleware(DataBaseSession(session_pool=session_maker)) #Добавление мидлвара DataBaseSession
        # в обработчик обновлений для обеспечения сессий с базой данных, используя session_pool и session_maker.

        await bot.delete_webhook(drop_pending_updates=True)
        # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats()) #Закомментировать (создан для удаления)
        await dp.start_polling(bot,
                               allowed_updates=dp.resolve_used_update_types())  # Подтягиваются автоматом все апдейты
    except Exception as e:
        app_logger.error(f'An error occurred: {e}')


async def error_handler(update: types.Update, exception: Exception):
    app_logger.error(f'Update: {update} caused error: {exception}')


if __name__ == '__main__':
    asyncio.run(main())
