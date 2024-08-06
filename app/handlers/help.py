from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.utils.logger import help_logger

router = Router()


def get_back_menu_keyboard():
    help_logger.debug("Creating back to menu keyboard")
    builder = InlineKeyboardBuilder()
    builder.button(text="Главное меню", callback_data="back_to_menu")
    return builder.as_markup()


@router.message(Command("help"))
async def cmd_help(message: Message):
    user_id = message.from_user.id
    help_logger.info(f"User {user_id} requested help command")

    help_text = (
        "В случае ошибок или пожеланий прошу писать @flyerts\n\n"
        "Используйте кнопки меню для навигации и создания игровых сессий."
    )

    await message.answer(help_text, reply_markup=get_back_menu_keyboard())
    help_logger.info(f"Help information sent to user {user_id}")

# @router.message(F.text)
# async def handle_unknown_message(message: Message):
#     # Добавляем сообщение пользователя для удаления
#     await message_cleaner.add_user_message(message)
#
#     # # Удаляем предыдущие сообщения
#     # await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)
#
#     unknown_text = (
#         "Извините, я не понимаю эту команду. "
#         "Пожалуйста, используйте кнопки в главном меню."
#     )
#
#     # Отправляем новое сообщение с клавиатурой главного меню
#     response = await message.answer(unknown_text, reply_markup=get_main_menu_keyboard(message.from_user.id))
#
#     # Добавляем новое сообщение бота для последующего удаления
#     await message_cleaner.add_message_to_delete(message.from_user.id, response)
