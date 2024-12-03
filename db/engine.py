import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from common.text_for import description_for_info_pages
from db.models import Base
from db.orm_query import orm_add_banner_description


engine = create_async_engine(os.getenv("DB_LITE"), echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def create_db():
    """
        Создает базу данных и добавляет данные в таблицу базы данных.

        Функция выполняет следующие действия:
        1. Создает структуру базы данных, основанную на метаданных модели `Base`.
        2. Открывает новую асинхронную сессию для взаимодействия с базой данных.
        3. Добавляет описание баннера, полученное из `description_for_info_pages`, используя функцию `orm_add_banner_description`.

        Использует:
            - engine: асинхронный движок базы данных.
            - session_maker: фабрикатор сессий для создания асинхронных сессий.
        """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        await orm_add_banner_description(session, description_for_info_pages)


