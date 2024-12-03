# файл, отвечающий за запросы в/из БД. Изменяем,выбираем,добавляем
from datetime import datetime

from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import Banner, User
from logging_config import setup_logging

# Настройка логгирования
app_logger = setup_logging("orm_query", "logs/orm.log")


# Работа с баннерами (информационными страницами)

async def orm_add_banner_description(session: AsyncSession, data: dict):
    """
      Добавляет новый баннер или изменяет существующий, если баннер для заданного имени уже присутствует.

      Эта функция проверяет, существует ли хотя бы один баннер в базе данных.
      Если баннеры уже существуют, функция завершает выполнение.
      Если нет, то добавляет новые записи баннеров на основе переданных данных.

      :param session: Асинхронная сессия базы данных для выполнения запросов.
      :param data: Словарь с именами баннеров в качестве ключей и их описаниями в качестве значений.
                    Пример: {'main': 'Описание главного баннера', 'about': 'Описание о нас'}.

      :return: Не возвращает значения. Добавляет записи в базу данных, если они отсутствуют.
      """
    # Добавляем новый или изменяем существующий по именам
    # пунктов меню: main, about,
    query = select(Banner)
    result = await session.execute(query)
    if result.first():
        return
    session.add_all([Banner(name=name, description=description) for name, description in data.items()])
    await session.commit()


async def orm_change_banner_image(session: AsyncSession, name: str, image: str):
    """
       Обновляет изображение для указанного баннера.

       Эта функция находит баннер в базе данных по его имени и обновляет его изображение,
       если баннер существует.

       :param session: Асинхронная сессия базы данных для выполнения запросов.
       :param name: Имя баннера, для которого требуется обновить изображение.
       :param image: Новый URL-адрес изображения баннера.

       :return: Не возвращает значения. Обновляет запись в базе данных.
       """
    query = update(Banner).where(Banner.name == name).values(image=image)
    await session.execute(query)
    await session.commit()


async def orm_get_banner(session: AsyncSession, page: str):
    """
       Получает баннер по имени страницы.

       Эта функция выполняет запрос к базе данных для получения баннера, который соответствует
       заданному имени страницы. Если баннер найден, возвращается его объект, иначе возвращается None.

       :param session: Асинхронная сессия базы данных для выполнения запросов.
       :param page: Имя страницы, для которой требуется получить баннер.

       :return: Объект баннера, соответствующий имени страницы, или None, если баннер не найден.
       """
    query = select(Banner).where(Banner.name == page)
    result = await session.execute(query)
    return result.scalar()


async def orm_get_info_pages(session: AsyncSession):
    """
       Получает список всех баннеров.

       Эта функция выполняет запрос к базе данных и возвращает все записи баннеров,
       которые есть в таблице. Возвращается список объектов баннеров.

       :param session: Асинхронная сессия базы данных для выполнения запросов.

       :return: Список объектов баннеров, найденных в базе данных. Если таблица пуста, возвращается пустой список.
       """
    query = select(Banner)
    result = await session.execute(query)
    return result.scalars().all()


# Добавляем юзера в БД

async def orm_add_user(
        session: AsyncSession,
        name: str | None = None,
        phone: str | None = None,
        date: datetime | None = None,
        time: str | None = None,  # Добавлено поле времени
):
    """
        Добавляет нового пользователя в базу данных.

        Эта функция создает экземпляр модели пользователя с указанными данными и добавляет его в
        базу данных. После добавления изменений в базе данных выполняется коммит.

        :param session: Асинхронная сессия базы данных для выполнения запросов.
        :param name: Имя нового пользователя. Может быть None.
        :param phone: Номер телефона нового пользователя. Может быть None.
        :param date: Дата записи пользователя. Может быть None.
        :param time: Время записи пользователя. Может быть None.

        :return: Не возвращает значения. Добавляет запись в базу данных.
        """
    new_user = User(name=name, phone=phone, date=date, time=time)
    session.add(new_user)
    await session.commit()


async def orm_get_appointments_by_phone(session: AsyncSession, phone: str):
    """
    Получает список всех пользователей (заявок) по номеру телефона.

    :param session: Асинхронная сессия базы данных для выполнения запросов.
    :param phone: Номер телефона для поиска заявок.
    :return: Список объектов User или пустой список, если нет заявок.
    """
    query = select(User).where(User.phone == phone)  # Используем таблицу User
    result = await session.execute(query)
    return result.scalars().all()  # Возвращаем все записи


async def orm_update_user_appointment(session: AsyncSession, phone: str, new_date: str, new_time: str):
    """
    Обновляет запись о назначении в базе данных.

    :param session: Асинхронная сессия базы данных.
    :param appointment_id: ID записи для обновления.
    :param new_date: Новая дата назначения.
    :param new_time: Новое время назначения.
    """
    async with session.begin():  # Обязательно используйте контекст для транзакции
        result = await session.execute(select(User).where(User.phone == phone))
        appointment = result.scalars().first()  # Получаем экземпляр записи

        if appointment:
            app_logger.info(f'Обновление записи {phone} на дату {new_date} и время {new_time}')

            # Конвертируем строку даты в объект date
            date_obj = datetime.strptime(new_date, "%d-%m-%Y").date()

            # Оставляем время в текстовом формате 'HH:MM'
            time_str = new_time

            appointment.date = date_obj  # Присваиваем объект date
            appointment.time = time_str  # Присваиваем строку времени

            # Для корректного обновления данных
            session.add(appointment)  # добавляем изменения к сессии

            app_logger.info(f'Запись успешно обновлена: {phone}, {date_obj}, {time_str}')
        else:
            app_logger.error('Запись не найдена.')
            raise ValueError("Запись не найдена.")
