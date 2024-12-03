from sqlalchemy import String, Text, DateTime, func, DECIMAL, BigInteger, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    '''Класс Base является базовым классом для всех моделей, использующих SQLAlchemy с декларативной базой данных.
    Он включает в себя два поля: created и update, которые автоматически отслеживают время создания
    и последнего обновления записей в базе данных.

Атрибуты:
created (Mapped[DateTime]):

Тип: DateTime
Описание: Это поле автоматически устанавливается на текущее время при создании записи в базе данных.
Значение по умолчанию: Используется функция func.now(), которая возвращает текущее время сервера базы данных.
Роль: Поле для отслеживания времени создания записи.
update (Mapped[DateTime]):

Тип: DateTime
Описание: Это поле автоматически устанавливается на текущее время при создании записи и обновляется каждый раз, когда запись изменяется.
Значение по умолчанию: Используется функция func.now() для установки времени при первом создании записи.
Параметр onupdate=func.now(): Обеспечивает обновление значения поля update каждый раз, когда запись изменяется.
Роль: Поле для отслеживания времени последнего обновления записи.'''

    created: Mapped[DateTime] = mapped_column(DateTime,
                                              default=func.now())  # Поле для хранения времени создания записи.
    # Это значение устанавливается в момент вставки записи в базу данных.
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())  # Поле для хранения
    # времени последнего обновления записи. Значение этого поля обновляется каждый раз, когда запись изменяется.


class Banner(Base):
    '''Класс Banner представляет модель для таблицы banner в базе данных, наследуя от базового класса Base.
    Эта модель используется для хранения информации о баннерах, включая их уникальное название, изображение и описание.'''
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)


class User(Base):
    """
        Модель пользователя в базе данных.

        Атрибуты:
            id (Mapped[int]): Уникальный идентификатор записи (первичный ключ).
            name (Mapped[str]): Имя пользователя, необязательное поле (до 150 символов).
            phone (Mapped[str]): Номер телефона пользователя, необязательное поле (до 13 символов).
            date (Mapped[DateTime]): Дата записи, обязательное поле.
            time (Mapped[str]): Время записи, обязательное поле (например, '10:00').

        Ограничения:
            __table_args__: Уникальность записи по сочетанию полей `date` и `time`, чтобы гарантировать,
                            что на одну дату не может быть записано более одной записи в одно и то же время.
        """

    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # Уникальный идентификатор записи
    name: Mapped[str] = mapped_column(String(150), nullable=True)  # Не уникальное
    phone: Mapped[str] = mapped_column(String(13), nullable=True)  # Не уникальное
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)  # Дата записи
    time: Mapped[str] = mapped_column(String(5), nullable=False)  # Время записи (например, '10:00')
    __table_args__ = (
        UniqueConstraint('date', 'time', name='uq_user_date_time'),
        # Уникальность по user_id, date и time
    )
