from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from sqlalchemy.ext.asyncio import async_sessionmaker


class DataBaseSession(BaseMiddleware):
    """
       Middleware для управления сессиями базы данных.

       Этот класс обеспечивает доступ к асинхронной сессии базы данных из всех обработчиков.
       Он открывает сессию перед вызовом обработчика и закрывает ее после выполнения,
       тем самым гарантируя правильное управление ресурсами.

       :param session_pool: Асинхронный пул сессий для работы с базой данных.
       """
    def __init__(self, session_pool: async_sessionmaker) -> None:
        """
               Инициализирует класс DataBaseSession.

               :param session_pool: Асинхронный пул сессий, используемый для взаимодействия с базой данных.
               """
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:
        """
                Вызывает обработчик с открытой сессией базы данных.

                Эта функция открывает новую сессию и добавляет ее в параметр `data`,
                который будет доступен в каждом обработчике. После выполнения обработчика
                сессия автоматически закрывается.

                :param handler: Обработчик, который будет вызван с параметрами события и данных.
                :param event: Объект события, передаваемый в обработчик.
                :param data: Словарь данных, который передается в обработчик.

                :return: Возвращает результат выполнения обработчика.
                """
        async with self.session_pool() as session:
            data['session'] = session  #По параметру сессия в каждом хендлере будет доступна сессия
            return await handler(event, data)
