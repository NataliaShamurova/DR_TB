from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from db.orm_query import orm_get_info_pages, orm_change_banner_image
from filt.chat_types import ChatTypesFilter, IsAdmin
from kbrd.reply import get_keyboard

handler_admin_router = Router()
handler_admin_router.message.filter(ChatTypesFilter(["private"]), IsAdmin())  # Чтобы взаимодействовал только админ

ADMIN_KB = get_keyboard(
    "Добавить/Изменить баннер",
    placeholder="Выберите действие",
    sizes=(2,),
)


@handler_admin_router.message(Command("admin"))
async def admin_features(message: types.Message):
    await message.answer("Что хотите сделать?", reply_markup=ADMIN_KB)


# FSM для загрузки/изменения баннеров

class AddBanner(StatesGroup):
    image = State()


# Отправляем перечень информационных страниц бота и становимся в состояние отправки photo
@handler_admin_router.message(StateFilter(None), F.text == 'Добавить/Изменить баннер')
async def add_image2(message: types.Message, state: FSMContext, session: AsyncSession):
    pages_names = [page.name for page in await orm_get_info_pages(session)]
    await message.answer(f"Отправьте фото баннера.\nВ описании укажите для какой страницы:\
                         \n{', '.join(pages_names)}")
    await state.set_state(AddBanner.image)


# Команда отмены
@handler_admin_router.message(StateFilter(AddBanner.image), Command("отмена"))
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()  # Сбрасываем состояние
    await message.answer("Операция отменена. Вы можете вернуться к администраторским командам.")


# Добавляем/изменяем изображение в таблице
@handler_admin_router.message(AddBanner.image, F.photo)
async def add_banner(message: types.Message, state: FSMContext, session: AsyncSession):
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
    await message.answer("Отправьте фото баннера или отмена")
