from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.registration import RegistrationStates
from app.services.database import is_user_registered
from app.keyboards.menu import get_main_menu_keyboard
from app.utils.message_cleaner import message_cleaner
from app.utils.logger import start_logger

from aiogram.types import FSInputFile
from pathlib import Path

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start_logger.info(f"User {user_id} started the bot")


    # Путь к изображению
    image_path = Path("images/2.png")

    # Отправляем изображение вместо текстового сообщения
    welcome_image = FSInputFile(image_path)
    await message.answer_photo(
        photo=welcome_image,
        caption="Добро пожаловать в бот для создания игровых сессий!"
    )

    await message.delete()

    # Удаляем предыдущие сообщения
    await message_cleaner.delete_previous_messages(message.bot, user_id)

    if await is_user_registered(user_id):
        start_logger.info(f"User {user_id} is already registered")
        response = await message.answer("Вы уже зарегистрированы. Добро пожаловать в главное меню!",
                                        reply_markup=get_main_menu_keyboard(user_id))
        await message_cleaner.add_message_to_delete(user_id, response)
        return

    start_logger.info(f"Starting registration process for user {user_id}")
    response = await message.answer("Добро пожаловать! Давайте начнем регистрацию. Как вас зовут?")
    await state.set_state(RegistrationStates.waiting_for_name)
    await message_cleaner.add_message_to_delete(user_id, response)
    start_logger.info(f"Registration state set to waiting_for_name for user {user_id}")