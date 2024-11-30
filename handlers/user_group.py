from string import punctuation
from aiogram import types, Router, Bot
from aiogram.filters import Command

from filt.chat_types import ChatTypesFilter

handler_user_group_router = Router()
handler_user_group_router.message.filter(ChatTypesFilter(['group', 'supergroup']))
handler_user_group_router.edited_message.filter(ChatTypesFilter(['group', 'supergroup']))

# restricted_words = {'скотина', 'крыса', 'порно', 'козел', 'выхухоль'}  # Запрещенные слова


@handler_user_group_router.message(Command("admin"))
async def get_admins(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    admins_list = await bot.get_chat_administrators(chat_id)  # список участников
    admins_list = [
        member.user.id
        for member in admins_list
        if member.status == 'creator' or member.status == 'administrator'
    ]
    bot.a_admins_list = admins_list  # Получаем новый список
    if message.from_user.id in admins_list:
        await message.delete()


# def clean_text(text: str):  # Очищаем знаки пнкт в замаскированных словах
#     return text.translate(str.maketrans('', '', punctuation))


# @handler_user_group_router.edited_message()
# @handler_user_group_router.message()
# async def cleaner(message: types.Message):
#     if restricted_words.intersection(clean_text(message.text.lower()).split()):
#         await message.answer(f'{message.from_user.first_name}, соблюдайте порядок в чате!')
#         await message.delete()
