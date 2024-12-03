from typing import Optional, Dict

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


### Настраиваем инлай-клавиатуру" #############
class MenuCallBack(CallbackData, prefix='menu'):
    """
       Класс для представления данных обратного вызова, связанных с пунктами меню.

       :param menu_name: Название пункта меню, который был выбран пользователем.
       :param page: Страница меню (по умолчанию 1).
       """
    menu_name: str
    page: int = 1


def get_user_main_btns(
        *,
        btns: Dict[str, str] = None,

        sizes: tuple[int] = (2, 1)):
    """
       Создает и возвращает клавиатуру с основными кнопками для пользователя.

       :param btns: Словарь кнопок, где ключ - текст кнопки, а значение - данные обратного вызова.
                    Если не передан, используется набор стандартных кнопок.
       :param sizes: Кортеж, определяющий размеры клавиатуры (число кнопок в строке и количество строк).
       :return: Объект клавиатуры с кнопками.
       """
    if btns is None:
        btns = {
            "Записаться на прием ✐": 'make an appoint',
            'О нас ✋': 'about',
            'Получить список 📝': 'view_app'

        }

    keyboard = InlineKeyboardBuilder()

    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBack(menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()
