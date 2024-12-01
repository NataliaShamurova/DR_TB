import os
from datetime import datetime, timedelta

from aiogram import F, Router, types
from aiogram.filters import CommandStart, StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputFile, InputMediaPhoto, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from sqlalchemy.orm import joinedload

from db.models import User
# from db.models import #Appointment
from db.orm_query import orm_get_banner, orm_add_user  # orm_add_appointment
from filt.chat_types import ChatTypesFilter
from kbrd.inline import get_user_main_btns, MenuCallBack

handler_user_router = Router()
# handler_user_router.message.filter(ChatTypesFilter(['private']))  # Для взаимодействия с пользователем

time_mapping = {
    "0": "09:00",
    "1": "10:00",
    "2": "11:00",
    "3": "12:00",
    "4": "13:00",
    "5": "14:00",
    "6": "15:00",
    "7": "16:00",
    "8": "17:00",
    "9": "18:00",
    "10": "19:00",
}


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


######################################################
class AddUser(StatesGroup):
    name = State()
    phone = State()
    confirm = State()  # состояние для подтверждения
    date = State()  # состояние для выбора даты
    time = State()  # Состояние для выбора времени


@handler_user_router.callback_query(F.data == "make an appoint")
async def register_user(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()  # Убираем индикатор загрузки
    await callback.message.answer("Пожалуйста, введите ваше имя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddUser.name)


#################################################
@handler_user_router.message(StateFilter(AddUser.name))
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)  # Сохраняем имя
    await message.answer("Пожалуйста, введите ваш телефон:")
    await state.set_state(AddUser.phone)


##################################################
def format_phone_number(phone: str) -> str:
    # Удаление нежелательных символов (например, пробелов, скобок и дефисов)
    phone_digits = ''.join(filter(str.isdigit, phone))

    # Проверка количества цифр
    if len(phone_digits) < 10:
        return "Неверный номер телефона."  # Слишком короткий номер

    # Оставляем только последние 10 цифр для формата
    phone_digits = phone_digits[-10:]

    # Форматирование нужным образом
    formatted_phone = f"+7({phone_digits[:3]}){phone_digits[3:6]}-{phone_digits[6:8]}-{phone_digits[8:10]}"

    return formatted_phone


#########################################################

@handler_user_router.message(AddUser.phone)
async def process_phone(message: types.Message, state: FSMContext):
    phone_number = message.text
    formatted_phone = format_phone_number(phone_number)  # Форматируем номер

    # Проверяем корректность номера телефона
    if formatted_phone == "Неверный номер телефона.":
        await message.answer(formatted_phone)  # Если номер неверный, уведомляем пользователя
        return

    await state.update_data(phone=formatted_phone)  # Сохраняем отформатиротелефона
    await message.answer("Пожалуйста, введите желаемую дату в формате 'ДД-ММ-ГГГГ':")
    await state.set_state(AddUser.date)


##########################################################################
@handler_user_router.message(AddUser.date)
async def process_date(message: types.Message, state: FSMContext, session: AsyncSession):
    selected_date = message.text
    await state.update_data(selected_date=selected_date)  # Здесь сохраняем текст даты в состоянии

    # Проверка текущей даты
    now = datetime.now()
    today = now.date()

    try:
        selected_date_obj = datetime.strptime(selected_date, "%d-%m-%Y").date()

        # Проверка, что дата - не вчерашняя или более ранняя
        if selected_date_obj < today:
            await message.answer("Пожалуйста, введите корректное число (не ранее сегодняшнего дня).")
            await state.set_state(AddUser.date)
            return

    except ValueError:
        await message.answer("Неверный формат даты. Пожалуйста, используйте формат 'ДД-ММ-ГГГГ'.")
        await state.set_state(AddUser.date)
        return

    # Получаем свободные слоты
    free_slots = await get_free_slots(session, selected_date)

    if free_slots:
        slots_text = "\n".join(f"{i + 1}. {slot}" for i, slot in enumerate(free_slots))
        await message.answer("Выберите время:\n" + slots_text)
        await state.set_state(AddUser.time)
    else:
        await message.answer("К сожалению, на выбранную дату записи нет. Попробуйте другую дату.")
        await state.set_state(AddUser.date)


######################################################################
async def get_free_slots(session: AsyncSession, selected_date: str) -> list:
    try:
        date_obj = datetime.strptime(selected_date, "%d-%m-%Y")
    except ValueError:
        return []  # Возвращаем пустой список в случае ошибки формата даты

    # Выполняем запрос с правильным типом данных
    result = await session.execute(select(User.time).where(func.date(User.date) == date_obj.date()))
    busy_slots = [row[0] for row in result]  # Получаем первый элемент строки, который представляет собой время

    # Все возможные временные слоты
    all_slots = ['09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00', '18:00', '19:00']
    # Только свободные слоты
    free_slots = [slot for slot in all_slots if slot not in busy_slots]

    return free_slots


##############################################################


@handler_user_router.message(AddUser.time)
async def process_time(message: types.Message, state: FSMContext, session: AsyncSession):
    user_data = await state.get_data()  # Получаем данные пользователя из состояния
    name = user_data.get('name')  # Имя
    phone_number = user_data.get('phone')  # Номер телефона
    selected_date_str = user_data.get('selected_date')  # Выбранная дата
    selected_number = message.text.strip()  # Номер от пользователя

    # Проверяем корректность ввода
    selected_index = int(selected_number) - 1  # Уменьшаем на 1 для получения индекса
    free_slots = await get_free_slots(session, selected_date_str)  # Получаем список свободных слотов

    # Убедитесь, что индекс находится в пределах доступных слотов
    if selected_index < 0 or selected_index >= len(free_slots):
        await message.answer("Некорректный номер. Пожалуйста, введите номер, соответствующий времени.")
        return

    # Получаем соответствующее время из списка свободных слотов
    selected_time = free_slots[selected_index]

    # Проверка, чтобы время было не менее чем через 1 час от текущего
    selected_datetime = datetime.strptime(f"{selected_date_str} {selected_time}", "%d-%m-%Y %H:%M")
    now = datetime.now()
    if selected_datetime < (now + timedelta(hours=1)):
        await message.answer("Выберите время, которое будет не менее чем через 1 час от текущего времени.")
        return

    # Проверяем, занято ли время
    existing_appointments = await get_existing_appointments(session, selected_date_str)
    if selected_time in existing_appointments:
        await message.answer("К сожалению, на это время записи нет. Пожалуйста, выберите другое время.")
        return

    await state.update_data(selected_time=selected_time)  # Сохраняем выбранное время

    # Теперь выводим все данные
    await message.answer(
        f"Проверьте правильность введенных данных:\nИмя: {name}\nТелефон: {phone_number}\n"
        f"\nДата и время записи {selected_date_str} в {selected_time}.\n"
        "Если данные правильные, напишите 'да', если нет - 'нет'.")
    await state.set_state(AddUser.confirm)


##################################################################
async def get_existing_appointments(session: AsyncSession, selected_date: str) -> list:
    try:
        date_obj = datetime.strptime(selected_date, "%d-%m-%Y")
    except ValueError:
        return []  # Возвращаем пустой список в случае ошибки формата даты

    # Выполняем запрос и получаем занятые слоты по выбранной дате
    result = await session.execute(select(User.time).where(func.date(User.date) == date_obj))
    busy_slots = [row[0] for row in result]  # Получаем все времена для данной даты

    return busy_slots


#####################################################################
@handler_user_router.message(AddUser.confirm)
async def process_confirm(message: types.Message, state: FSMContext, session: AsyncSession):
    user_data = await state.get_data()
    selected_date_str = user_data.get('selected_date')
    selected_time = user_data.get('selected_time')  # Получаем время
    # user_id = message.from_user.id
    name = user_data.get('name')
    phone = user_data.get('phone')

    if message.text.lower() == 'да':
        try:
            selected_date = datetime.strptime(selected_date_str, "%d-%m-%Y")
        except ValueError:
            await message.answer("Ошибка при обработке даты. Пожалуйста, попробуйте снова.")
            await state.set_state(AddUser.date)
            return

        await orm_add_user(session, name=name, phone=phone, date=selected_date,
                           time=selected_time)  # Передаем time

        await message.answer(
            f"Ваша заявка принята на {selected_date.strftime('%d-%m-%Y')} в {selected_time}.")
        await state.clear()
        await send_start_menu(message, session)

    elif message.text.lower() == 'нет':
        await state.clear()
        await message.answer("Операция отменена. Введите ваши данные заново.")
        await send_start_menu(message, session)

    else:
        await message.answer("Пожалуйста, ответьте 'да' или 'нет'.")


async def send_start_menu(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, menu_name="main")
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)
