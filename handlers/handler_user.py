from datetime import datetime, timedelta

from aiogram import F, Router, types
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InputMediaPhoto
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from db.models import User

from db.orm_query import orm_get_banner, orm_add_user, orm_get_appointments_by_phone, \
    orm_update_user_appointment  # orm_add_appointment
from kbrd.inline import get_user_main_btns, MenuCallBack
from logging_config import setup_logging

handler_user_router = Router()

# Настройка логгирования
app_logger = setup_logging("handler_user", "logs/user.log")

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
    """
    Получает меню баннеров для указанного меню.

    :param session: Асинхронная сессия базы данных.
    :param menu_name: Имя меню для получения баннера.
    :return: Главный баннер и кнопки меню.
    """
    banner = await orm_get_banner(session, menu_name)
    image = InputMediaPhoto(media=banner.image, caption=banner.description)

    kbds = get_user_main_btns()

    return image, kbds


async def get_menu_content(session: AsyncSession, menu_name: str):
    """
      Получает контент меню на основе запрашиваемого имени меню.

      :param session: Асинхронная сессия базы данных для выполнения запросов.
      :param menu_name: Имя меню, для которого требуется получить контент.
      :return: Контент меню, полученный из базы данных.
      """

    return await get_banner_menu(session, menu_name)


@handler_user_router.message(CommandStart())
async def start_cmd(message: types.Message, session: AsyncSession):
    """
      Запускает команду /start и отправляет приветственное сообщение.

      :param message: Сообщение от пользователя.
      :param session: Асинхронная сессия базы данных.
      """
    media, reply_markup = await get_menu_content(session, menu_name="main")
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)


@handler_user_router.callback_query(MenuCallBack.filter())
async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, session: AsyncSession,
                    state: FSMContext):
    """
        Обрабатывает нажатие кнопки в меню и выполняет соответствующее действие.

        :param callback: Объект CallbackQuery, содержащий данные о нажатой кнопке.
        :param callback_data: Данные, связанные с нажатием кнопки меню.
        :param session: Асинхронная сессия базы данных для выполнения запросов.
        :param state: Состояние машины состояний FSM, используемое для хранения данных пользователя.
        """
    if callback_data.menu_name == 'make an appoint':
        await register_user(callback, state)  # Переходим к регистрации пользователя
        return
    if callback_data.menu_name == 'view_app':
        await add_view(callback, state)  # Переходим к регистрации пользователя
        return
    media, reply_markup = await get_menu_content(session, menu_name=callback_data.menu_name)

    await callback.message.edit_media(media=media, reply_markup=reply_markup)
    await callback.answer()


######################################################
''' Настройка FSM для ввода пользователем заявки'''


class AddUser(StatesGroup):
    name = State()
    phone = State()
    confirm = State()  # состояние для подтверждения
    date = State()  # состояние для выбора даты
    time = State()  # Состояние для выбора времени


@handler_user_router.callback_query(F.data == "make an appoint")
async def register_user(callback: types.CallbackQuery, state: FSMContext):
    """
       Начинает процесс регистрации нового пользователя.

       :param callback: Объект callback от пользователя.
       :param state: Состояние машины состояний FSM.
       """
    await callback.answer()  # Убираем индикатор загрузки
    await callback.message.answer("Пожалуйста, введите ваше имя:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(AddUser.name)


#################################################
@handler_user_router.message(StateFilter(AddUser.name))
async def process_name(message: types.Message, state: FSMContext):
    """
        Обрабатывает ввод имени пользователя и переходит к следующему этапу ввода данных.

        :param message: Объект сообщения от пользователя, содержащий введенное имя.
        :param state: Состояние машины состояний FSM, хранящее данные пользователя.
    """
    await state.update_data(name=message.text)  # Сохраняем имя
    await message.answer("Пожалуйста, введите ваш телефон:")
    await state.set_state(AddUser.phone)


#####################################################################


'''Приводим номер телефона к виду +7(XXX)XXX-XX-XX'''


def format_phone_number(phone: str) -> str:
    """
        Приводит номер телефона к стандартному формату +7(XXX)XXX-XX-XX.

        :param phone: Исходный номер телефона.
        :return: Отформатированный номер телефона.
        """
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
    """
    Обрабатывает введенный пользователем номер телефона и проверяет его корректность.
    На основе введенного номера телефона запрашивает дату для записи.

    :param message: Объект сообщения от пользователя, содержащий введенный номер телефона.
    :param state: Состояние машины состояний FSM, хранящее данные пользователя.
    """
    phone_number = message.text
    formatted_phone = format_phone_number(phone_number)  # Форматируем номер

    # Проверяем корректность номера телефона
    if formatted_phone == "Неверный номер телефона.":
        await message.answer(formatted_phone)  # Если номер неверный, уведомляем пользователя
        return

    # Сохраняем отформатированный номер телефона
    await state.update_data(phone=formatted_phone)

    # Сохраняем тип операции (добавление или изменение) и переходим к введению даты
    operation_type = (await state.get_data()).get('operation_type', 'add')
    await state.update_data(operation_type=operation_type)

    await message.answer("Пожалуйста, введите желаемую дату в формате 'ДД-ММ-ГГГГ':")
    await state.set_state(AddUser.date)


##########################################################################
''' Проверка даты на корректность '''


@handler_user_router.message(AddUser.date)
async def process_date(message: types.Message, state: FSMContext, session: AsyncSession):
    """
       Обрабатывает сообщение с датой, введенной пользователем.

       :param message: Сообщение от пользователя, содержащее дату.
       :param state: Контекст состояния, используемый для хранения данных состояния FSM.
       :param session: Асинхронная сессия базы данных для работы с записями.
       """
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
    """
       Получает список свободных временных слотов на указанную дату.

       Эта функция проверяет, какие временные слоты доступны для записи, исключая занятые слоты,
       которые уже забронированы пользователями на указанную дату.

       :param session: Асинхронная сессия базы данных для выполнения запросов.
       :param selected_date: Дата, по которой нужно получить доступные слоты, в формате 'ДД-ММ-ГГГГ'.
       :return: Список свободных временных слотов.
       """
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
    """
        Обрабатывает ввод времени для записи пользователя.

        Эта функция получает данные пользователя из состояния машины, проверяет корректность введенного времени,
        и выводит пользователю все введенные данные для подтверждения. Также проверяет, что выбранное время
        является доступным и не менее чем через час от текущего времени.

        :param message: Объект сообщения от пользователя, содержащий введенное время.
        :param state: Состояние машины состояний FSM, хранящее данные пользователя.
        :param session: Асинхронная сессия базы данных для выполнения запросов.

        :raises ValueError: Если введенный номер некорректен или время занято.
        """
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
    """
        Получает все занятые временные слоты по указанной дате.

        Эта функция выполняет запрос к базе данных, чтобы найти все записи о записях на
        выбранную дату и вернуть список занятых времен.

        :param session: Асинхронная сессия базы данных для выполнения запросов.
        :param selected_date: Дата, по которой нужно получить записи, в формате 'ДД-ММ-ГГГГ'.
        :return: Список занятых временных слотов на указанную дату. Если формат даты некорректен,
                 возвращается пустой список.

        :raises ValueError: Если преобразование строки даты в объект datetime не удалось.
        """
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
    """
        Обрабатывает подтверждение введенных пользователем данных.

        Эта функция проверяет ответ пользователя на подтверждение записи. Если пользователь
        подтверждает ('да'), данные записываются в базу данных. Если пользователь отказывается ('нет'),
        состояние машины сбрасывается и начинается новый ввод данных. Функция также
        обрабатывает недопустимые ответы.

        :param message: Объект сообщения от пользователя, содержащий ответ на подтверждение ('да' или 'нет').
        :param state: Состояние машины состояний FSM, хранящее данные пользователя.
        :param session: Асинхронная сессия базы данных для выполнения запросов.

        :raises ValueError: Если преобразование строки даты в объект datetime не удалось.
        """

    user_data = await state.get_data()
    operation_type = user_data.get('operation_type')
    app_logger.info(f"Тип операции: {operation_type}")  # Логирование текущего типа операции
    selected_date_str = user_data.get('selected_date')
    selected_time = user_data.get('selected_time')
    name = user_data.get('name')
    phone = user_data.get('phone')

    if message.text.lower() == 'да':
        app_logger.info("Пользователь подтвердил действие.")

        if operation_type == 'add':
            due_date = datetime.strptime(selected_date_str, "%d-%m-%Y")
            await orm_add_user(session, name=name, phone=phone, date=due_date, time=selected_time)
            await message.answer(f"Ваша заявка принята на {due_date.strftime('%d-%m-%Y')} в {selected_time}.")

        elif operation_type == 'update':
            app_logger.info("Попытка обновления записи.")
            try:
                await orm_update_user_appointment(session, phone, selected_date_str, selected_time)
                await message.answer(f"Ваша запись была изменена на {selected_date_str} в {selected_time}.")
            except Exception as e:
                app_logger.error(f"Ошибка при обновлении записи: {e}")
                await message.answer("Произошла ошибка при изменении вашей записи.")

        await state.clear()  # Лучше оставить это после того, как операция завершена
        await send_start_menu(message, session)

    elif message.text.lower() == 'нет':
        await state.clear()
        await message.answer("Операция отменена. Вы можете ввести данные заново.")
        await send_start_menu(message, session)

    else:
        await message.answer("Пожалуйста, ответьте 'да' или 'нет'.")
        ####### ###########


async def send_start_menu(message: types.Message, session: AsyncSession):
    media, reply_markup = await get_menu_content(session, menu_name="main")
    await message.answer_photo(media.media, caption=media.caption, reply_markup=reply_markup)

    #########################Получение заявок##########################


class ViewApp(StatesGroup):
    phone = State()  # Состояние для ввода номера телефона
    action = State()  # Состояние для выбора действия (изменение или удаление заявки)
    change_data = State()  # Состояние для изменения даты заявки
    change_time = State()  # Состояние для изменения времени заявки
    delete_appointment = State()  # Состояние для удаления заявки


@handler_user_router.callback_query(F.data == 'view_app')
async def add_view(callback: types.CallbackQuery, state: FSMContext):
    """
       Начинает процесс получения списка заявок пользователя.

       :param callback: Объект callback от пользователя.
       :param state: Состояние машины состояний FSM.
       """
    await callback.answer()  # Убираем индикатор загрузки
    await callback.message.answer("Пожалуйста, введите ваш номер телефона:", reply_markup=types.ReplyKeyboardRemove())
    await state.set_state(ViewApp.phone)  # Устанавливаем состояние для ввода телефона


#################
@handler_user_router.message(ViewApp.phone)
async def process_view_app_phone(message: types.Message, state: FSMContext, session: AsyncSession):
    """
      Обрабатывает сообщение с номером телефона, введенным пользователем, и возвращает его активные заявки.

      :param message: Сообщение от пользователя, содержащее номер телефона.
      :param state: Контекст состояния, используемый для хранения данных состояния FSM.
      :param session: Асинхронная сессия базы данных для работы с записями.
      """
    phone_number = message.text
    formatted_phone = format_phone_number(phone_number)

    # Проверяем корректность номера телефона
    if formatted_phone == "Неверный номер телефона.":
        await message.answer(formatted_phone)
        return

    appointments = await orm_get_appointments_by_phone(session, formatted_phone)
    if appointments:
        # Сохраняем имя и телефон пользователя
        user_data = {"phone": formatted_phone}
        for appt in appointments:
            user_data["name"] = appt.name  # имя пользователя в моделях
        await state.update_data(**user_data)

        appointments_text = "\n".join(
            f"{i + 1}. Запись на {appt.date.strftime('%d-%m-%Y')} в {appt.time}." for i, appt in
            enumerate(appointments))
        await message.answer(
            f"Ваши заявки:\n{appointments_text}\n\nВыберите действие:"
            f"\n1. Изменить заявку\n2. Удалить заявку\n3. Оставить как есть",
            reply_markup=types.ReplyKeyboardRemove())
        await state.update_data(appointments=appointments)
        await state.set_state(ViewApp.action)
    else:
        await message.answer("У вас нет активных заявок.")

        await state.clear()
        await send_start_menu(message, session)


##########
@handler_user_router.message(ViewApp.action)
async def process_action(message: types.Message, state: FSMContext, session: AsyncSession):
    """
      Обрабатывает действие пользователя с активными заявками, предлагая изменить, удалить или оставить заявки.

      :param message: Сообщение от пользователя, содержащие действие (изменить, удалить или оставить).
      :param state: Контекст состояния, используемый для хранения данных состояния FSM.
      :param session: Асинхронная сессия базы данных для работы с записями.
      """
    user_data = await state.get_data()
    appointments = user_data.get('appointments', [])

    if not appointments:
        await message.answer("У вас нет активных заявок")
        await state.clear()
        await send_start_menu(message, session)
        return

    action = message.text.strip()
    if action == "1":  # Изменить время
        await state.update_data(operation_type='update')
        await message.answer("Пожалуйста, введите номер заявки, которую хотите изменить:")
        await state.set_state(ViewApp.change_data)

    elif action == "2":  # Удалить заявку
        await message.answer("Пожалуйста, введите номер заявки, которую хотите удалить:")
        await state.set_state(ViewApp.delete_appointment)

    elif action == "3":  # Оставить
        await state.clear()
        await send_start_menu(message, session)

    else:
        await message.answer(
            "Некорректный ввод. Пожалуйста, выберите 1 для изменения даты и времени, "
            "2 для удаления заявки или 3, если заявку не надо менять.")


###########бработчик для выбора новой даты
@handler_user_router.message(ViewApp.change_data)
async def process_change_date(message: types.Message, state: FSMContext, session: AsyncSession):
    """
       Обрабатывает изменение даты и времени для выбранной заявки пользователя.

       :param message: Сообщение от пользователя, содержащие номер заявки для изменения.
       :param state: Контекст состояния, используемый для хранения данных состояния FSM.
       :param session: Асинхронная сессия базы данных для работы с записями.
       """
    user_data = await state.get_data()
    appointments = user_data.get('appointments', [])

    if not appointments:
        await message.answer("У вас нет активных заявок.")
        await state.clear()
        await send_start_menu(message, session)
        return

    selected_index = int(message.text.strip()) - 1  # Получаем индекс выбранной заявки
    if selected_index < 0 or selected_index >= len(appointments):
        await message.answer("Некорректный номер заявки.")
        return

    appointment = appointments[selected_index]
    await state.update_data(appointment_id=appointment.id)  # Сохраняем ID заявки
    await message.answer("Пожалуйста, введите новую дату в формате 'ДД-ММ-ГГГГ':")
    await state.set_state(AddUser.date)  # Переходим к состоянию выбора новой даты


############
@handler_user_router.message(ViewApp.change_time)
async def process_change_time(message: types.Message, state: FSMContext, session: AsyncSession):
    """
       Обрабатывает изменение времени для выбранной заявки пользователя.

       :param message: Сообщение от пользователя, содержащие номер заявки для изменения времени.
       :param state: Контекст состояния, используемый для хранения данных состояния FSM.
       :param session: Асинхронная сессия базы данных для работы с записями.
       """
    user_data = await state.get_data()
    appointments = user_data.get('appointments', [])

    if not appointments:
        await message.answer("У вас нет активных заявок.")
        await state.clear()
        await send_start_menu(message, session)
        return

    try:
        selected_index = int(message.text.strip()) - 1  # Получаем индекс выбранной заявки
        if selected_index < 0 or selected_index >= len(appointments):
            await message.answer("Некорректный номер заявки.")
            return

        appointment = appointments[selected_index]
        await state.update_data(appointment_id=appointment.id)  # Сохраняем ID заявки
        await message.answer("Выберите новое время для вашей заявки:")
        free_slots = await get_free_slots(session, appointment.date.strftime('%d-%m-%Y'))

        if free_slots:
            slots_text = "\n".join(f"{i + 1}. {slot}" for i, slot in enumerate(free_slots))
            await message.answer(f"Доступные слоты:\n{slots_text}")
            await state.set_state(AddUser.time)  # Переход к состоянию выбора нового времени
        else:
            await message.answer("К сожалению, в данный момент нет доступного времени для изменения заявки.")
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заявки.")


########

@handler_user_router.message(ViewApp.delete_appointment)
async def process_delete_appointment(message: types.Message, state: FSMContext, session: AsyncSession):
    """
       Обрабатывает удаление выбранной заявки пользователя.

       :param message: Сообщение от пользователя, содержащее номер заявки для удаления.
       :param state: Контекст состояния, используемый для хранения данных состояния FSM.
       :param session: Асинхронная сессия базы данных для работы с записями.
       """
    user_data = await state.get_data()
    appointments = user_data.get('appointments', [])

    if not appointments:
        await message.answer("У вас нет активных заявок.")
        await state.clear()
        await send_start_menu(message, session)
        return

    try:
        selected_index = int(message.text.strip()) - 1  # Получаем индекс выбранной заявки
        if selected_index < 0 or selected_index >= len(appointments):
            await message.answer("Некорректный номер заявки.")
            return

        appointment = appointments[selected_index]
        await session.delete(appointment)  # Удаляем заявку из базы данных
        await session.commit()  # Сохраняем изменения

        await message.answer("Ваша заявка была удалена.")
        await state.clear()
        await send_start_menu(message, session)
    except ValueError:
        await message.answer("Пожалуйста, введите корректный номер заявки.")


#################################################

async def error_handler(update: types.Update, exception: Exception):
    app_logger.error(f'Update: {update} caused error: {exception}')
