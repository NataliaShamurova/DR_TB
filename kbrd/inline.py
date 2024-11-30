from typing import Optional, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallBack(CallbackData, prefix='menu'):
    #level: int
    menu_name: str
    page: int = 1


def get_user_main_btns(
        *,
        btns: Dict[str, str] = None,

        sizes: tuple[int] = (2,)):

    if btns is None:
        btns = {
            "Записаться на прием ✐": 'make an appoint',
            'О нас ✋': 'about',
        }

    keyboard = InlineKeyboardBuilder()

    for text, menu_name in btns.items():
        if menu_name == menu_name:

            keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBack(menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()
