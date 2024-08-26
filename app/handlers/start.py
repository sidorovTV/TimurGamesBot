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
import random

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    start_logger.info(f"User {user_id} started the bot")

    # Путь к папке с изображениями
    images_folder = Path("images")

    # Получаем список всех файлов изображений в папке
    image_files = list(images_folder.glob("*.png")) + list(images_folder.glob("*.jpg")) + list(
        images_folder.glob("*.jpeg"))

    if image_files:
        # Выбираем случайное изображение
        random_image = random.choice(image_files)

        # Отправляем случайное изображение
        welcome_image = FSInputFile(random_image)
        await message.answer_photo(
            photo=welcome_image,
            caption="Добро пожаловать в бот для создания игровых сессий!"
        )
    else:
        # Если изображений нет, отправляем текстовое сообщение
        await message.answer("Добро пожаловать в бот для создания игровых сессий!")

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