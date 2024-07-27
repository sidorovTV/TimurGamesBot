from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.registration import RegistrationStates
from app.services.database import is_user_registered
from app.handlers.menu import get_main_menu_keyboard
from app.utils.message_cleaner import message_cleaner

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    # Удаляем предыдущие сообщения
    await message_cleaner.delete_previous_messages(message.bot, user_id)

    # Добавляем сообщение пользователя для удаления
    await message_cleaner.add_user_message(message)

    if await is_user_registered(user_id):
        response = await message.answer("Вы уже зарегистрированы. Добро пожаловать в главное меню!",
                                        reply_markup=get_main_menu_keyboard(user_id))
        # Удаляем предыдущие сообщения
        await message_cleaner.delete_previous_messages(message.bot, user_id)
        return

    response = await message.answer("Добро пожаловать! Давайте начнем регистрацию. Как вас зовут?")
    await state.set_state(RegistrationStates.waiting_for_name)
    # Удаляем предыдущие сообщения
    await message_cleaner.delete_previous_messages(message.bot, user_id)
