from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.registration import RegistrationStates
from app.services.database import save_user
from app.utils.validators import is_valid_age, is_valid_russian_name
from app.keyboards.menu import get_main_menu_keyboard
from app.utils.logger import registration_logger

router = Router()


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    name = message.text
    registration_logger.info(f"User {user_id} attempting to register with name: {name}")

    if not is_valid_russian_name(name):
        registration_logger.warning(f"Invalid name entered by user {user_id}: {name}")
        await message.answer("Пожалуйста, введите корректное имя на русском языке.")
        return

    await state.update_data(name=name, username=message.from_user.username, user_id=user_id)
    await message.answer("Отлично! Теперь введите ваш возраст:")
    await state.set_state(RegistrationStates.waiting_for_age)
    registration_logger.info(f"Name accepted for user {user_id}. Waiting for age input.")


@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    user_id = message.from_user.id
    age = message.text
    registration_logger.info(f"User {user_id} entered age: {age}")

    if not is_valid_age(age):
        registration_logger.warning(f"Invalid age entered by user {user_id}: {age}")
        await message.answer("Пожалуйста, введите корректный возраст (только цифры).")
        return

    age = int(age)
    user_data = await state.get_data()
    await state.clear()

    try:
        await save_user(user_data['name'], age, user_data['username'], user_data['user_id'])
        registration_logger.info(f"User {user_id} successfully registered. Name: {user_data['name']}, Age: {age}")

        await message.answer(
            f"Регистрация завершена!\n"
            f"Имя: {user_data['name']}\n"
            f"Возраст: {age}\n"
            f"Username: @{user_data['username'] or 'Не указан'}\n\n"
            "Добро пожаловать в главное меню!",
            reply_markup=get_main_menu_keyboard(user_id)
        )
    except Exception as e:
        registration_logger.error(f"Error saving user {user_id} to database: {str(e)}", exc_info=True)
        await message.answer(
            "Произошла ошибка при регистрации. Пожалуйста, попробуйте еще раз или обратитесь к администратору.")
