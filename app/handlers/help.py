from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


def get_help_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Главное меню", callback_data="back_to_menu")
    return builder.as_markup()


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/menu - Открыть главное меню\n"
        "/help - Показать эту справку\n\n"
        "Используйте кнопки меню для навигации и создания игровых сессий.")
    await message.answer(help_text)


@router.message(F.text)
async def handle_unknown_message(message: Message):
    unknown_text = (
        "Извините, я не понимаю эту команду. "
        "Пожалуйста, используйте /help для просмотра доступных команд "        "или вернитесь в главное меню.")
    response = await message.answer(unknown_text, reply_markup=get_help_keyboard())