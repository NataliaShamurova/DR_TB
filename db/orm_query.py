# файл, отвечающий за запросы в/из БД. Изменяем,выбираем,добавляем
from datetime import datetime

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Banner, User


# Работа с баннерами (информационными страницами)

async def orm_add_banner_description(session: AsyncSession, data: dict):
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, about,
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


# Добавляем юзера в БД

async def orm_add_user(
        session: AsyncSession,
        #user_id: int,
        name: str | None = None,
        phone: str | None = None,
        date: datetime | None = None,
        time: str | None = None,  # Добавлено поле времени
):
    new_user = User(name=name, phone=phone, date=date, time=time)
    session.add(new_user)
    await session.commit()
    #query = select(User).where(User.user_id == user_id)
    # result = await session.execute(query)
    # existing_user = result.scalar()

    # if existing_user is None:
    #     # Создаем нового пользователя
    #     session.add(
    #         User(user_id=user_id, name=name, phone=phone, date=date, time=time)  # Добавил time здесь
    #     )
    # else:
    #     # Обновляем только поля имени, телефона и дату записи
    #     existing_user.name = name
    #     existing_user.phone = phone
    #     existing_user.date = date
    #     existing_user.time = time  # Обновляем время записи

    # await session.commit()



