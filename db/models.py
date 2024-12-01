from sqlalchemy import String, Text, DateTime, func, DECIMAL, BigInteger, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    update: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Banner(Base):
    __tablename__ = 'banner'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(15), unique=True)
    image: Mapped[str] = mapped_column(String(150), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

class User(Base):
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # Уникальный идентификатор записи
    #user_id: Mapped[int] = mapped_column(BigInteger)  # Не уникальное поле
    name: Mapped[str] = mapped_column(String(150), nullable=True)  # Не уникальное
    phone: Mapped[str] = mapped_column(String(13), nullable=True)  # Не уникальное
    date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)  # Дата записи
    time: Mapped[str] = mapped_column(String(5), nullable=False)  # Время записи (например, '10:00')
    __table_args__ = (
        UniqueConstraint('date', 'time', name='uq_user_date_time'),
        # Уникальность по user_id, date и time
        )
# class User(Base):
#     __tablename__ = 'user'
#
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
#     user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
#     name: Mapped[str] = mapped_column(String(150), nullable=True)
#     phone: Mapped[str] = mapped_column(String(13), nullable=True)
#     date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)  # Дата записи
#     time: Mapped[str] = mapped_column(String(5), nullable=False)  # Время записи (например, '10:00')

# class User(Base):
#     __tablename__ = 'user'
#
#     id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # Уникальный идентификатор записи
#     user_id: Mapped[int] = mapped_column(BigInteger)  # Не уникальное поле
#     name: Mapped[str] = mapped_column(String(150), nullable=True)  # Не уникальное
#     phone: Mapped[str] = mapped_column(String(13), nullable=True)  # Не уникальное
#     date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)  # Дата записи
#     time: Mapped[str] = mapped_column(String(5), nullable=False)  # Время записи (например, '10:00')
#
#     __table_args__ = (
#         UniqueConstraint('user_id', 'time', name='uq_user_time'),  # Уникальность комбинации user_id и time
    #) # Добавление UniqueConstraint для полей user_id и time
    # гарантирует, что для данного пользователя на одну и ту же дату не будет двух записей с одинаковым временем. Это позволяет одному и тому же пользователю запланировать
    # несколько записей, например, на разные даты или время.