from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_query import orm_get_info_pages, orm_change_banner_image
from kbrd.reply import get_keyboard

handler_admin_router = Router()


ADMIN_KB = get_keyboard(
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)


@handler_admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Вы вошли в админ-панель", reply_markup=ADMIN_KB)


# FSM для загрузки/изменения баннеров

class AddBanner(StatesGroup):
    image = State()


# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@handler_admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    """
       Обрабатывает отправку сообщения для добавления или изменения баннера.

       Эта функция вызывается, когда администратор выбирает опцию
       'Добавить/Изменить баннер' в интерфейсе чата. Она запрашивает у администратора
       фото баннера и информацию о соответствующей странице.

       Параметры:
           message (types.Message): Сообщение, содержащее текст, который инициировал команду.
           state (FSMContext): Контекст состояния для управления состоянием состояния машины.
           session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.

       Процесс:
           1. Получает названия страниц из базы данных с помощью функции `orm_get_info_pages`.
           2. Отправляет администратору сообщение с просьбой отправить фото баннера и указать страницу,
              для которой предназначен баннер.
           3. Устанавливает состояние бота в `AddBanner.image`, чтобы ожидать получения изображения.
       """
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)


# Команда отмены
@handler_admin_router.message(StateFilter(AddBanner.image), Command("отмена"))
async def cancel_process(message: types.Message, state: FSMContext):
    """
        Обрабатывает команду отмены, когда пользователь находится в процессе добавления изображения баннера.

        Эта функция вызывается, когда администратор вводит команду "отмена" в состоянии
        добавления изображения баннера. Функция сбрасывает текущее состояние
        и уведомляет админа о том, что операция была отменена.

        Параметры:
            message (types.Message): Сообщение, содержащее команду на отмену.
            state (FSMContext): Контекст состояния для управления текущим состоянием в состоянии машины.

        Процесс:
            1. Сбрасывает текущее состояние с помощью метода `state.clear()`.
            2. Отправляет сообщение пользователю о том, что операция была отменена и что он может
               вернуться к администраторским командам.
        """
    await state.clear()  # Сбрасываем состояние
    await message.answer("Операция отменена. Вы можете вернуться к администраторским командам.")


# Добавляем/изменяем изображение в таблице
@handler_admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
    """
        Обрабатывает добавление или изменение баннера на основе полученного изображения и описания страницы.

         Функция проверяет, есть ли указание на корректную страницу,
        обновляет изображение баннера в базе данных и уведомляет пользователя об успешном добавлении.

        Параметры:
            message (types.Message): Сообщение, содержащее изображение и описание страницы.
            state (FSMContext): Контекст состояния для управления текущим состоянием в состоянии машины.
            session (AsyncSession): Асинхронная сессия SQLAlchemy для взаимодействия с базой данных.

        Процесс:
            1. Извлекает идентификатор изображения из сообщения.
            2. Получает название страницы из описания (caption) сообщения.
            3. Проверяет, существует ли указанная страница в базе данных.
               - Если страница некорректна, отправляет сообщение с просьбой указать правильное название.
            4. Обновляет изображение баннера для указанной страницы с помощью функции `orm_change_banner_image`.
            5. Уведомляет пользователя о успешном добавлении или изменении баннера.
            6. Очищает состояние.
        """
    image_id = message.photo[-1].file_id
    for_page = message.caption.strip()
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    if for_page not in pages_names:
        await message.answer(f"Введите нормальное название страницы, например:\
                         \n{', '.join(pages_names)}")
        return
    await orm_change_banner_image(session, for_page, image_id, )
    await message.answer("Баннер добавлен/изменен.")
    await state.clear()


# ловим некоррекный ввод
@handler_admin_router.message(AddBanner.image)
async def add_banner2(message: types.Message, state: FSMContext):
    """
       Обрабатывает некорректный ввод, когда пользователь отправляет не изображение.

              Параметры:
           message (types.Message): Сообщение, содержащее текст, который не является изображением.
           state (FSMContext): Контекст состояния для управления текущим состоянием в состоянии машины.

       Процесс:
           1. Отправляет сообщение пользователю с просьбой отправить фото баннера или команду на отмену.
       """
    await message.answer("Отправьте фото баннера или отмена")
