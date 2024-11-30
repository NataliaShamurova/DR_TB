import os
from aiogram import F, Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputFile, InputMediaPhoto, FSInputFile
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_query import orm_get_banner, orm_add_user
from filt.chat_types import ChatTypesFilter
from kbrd.inline import get_user_main_btns, MenuCallBack

handler_user_router = Router()
handler_user_router.message.filter(ChatTypesFilter(['private']))  # Для взаимодействия с пользователем


async def get_banner_menu(session: AsyncSession, menu_name: str):
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns()

    return image, kbds


async def get_menu_content(session: AsyncSession, menu_name: str):
    return await get_banner_menu(session, menu_name)


@handler_user_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, menu_name="main")

    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


@handler_user_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession,
                    state: FSMContext):
    if callback_data.menu_name == 'make an appoint':
        await register_user(callback, state)  # Переходим к регистрации пользователя
        return

    media, reply_markup = await get_menu_content(session, menu_name=callback_data.menu_name)

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


class AddUser(StatesGroup):
    name = State()
    phone = State()


@handler_user_router.callback_query(F.data == "make an appoint")
async def register_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()  # Убираем индикатор загрузки
    await callback.message.answer("Пожалуйста, введите ваше имя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddUser.name)


@handler_user_router.message(AddUser.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)  # Сохраняем имя
    await message.answer("Пожалуйста, введите ваш телефон:")
    await state.set_state(AddUser.phone)


def is_valid_phone_number(phone_number: str) -> bool:
    # Удаляем все пробелы и символы
    phone_number = phone_number.replace(' ', '').replace('-', '')

    # Проверяем, состоит ли строка только из цифр
    if not phone_number.isdigit():
        return False

    # Проверка длины номера (например, 10 или 11 цифр)
    return len(phone_number) == 10 or len(phone_number) == 11


@handler_user_router.message(AddUser.phone)
async def process_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    phone_number = message.text

    # Проверяем корректность номера телефона
    if is_valid_phone_number(phone_number):
        user_data = await state.get_data()
        name = user_data.get('name')

        # Добавляем пользователя в БД
        await orm_add_user(session, message.from_user.id, name=name, phone=phone_number)

        await message.answer("Ваша заявка принята, менеджер свяжется с вами в течении ближайшего часа.")
        await state.clear()  # Завершаем состояние
    else:
        await message.answer("Номер телефона введен некорректно. Пожалуйста, введите номер, "
                             "состоящий только из цифр (10 или 11 цифр):")
