from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.registration import RegistrationStates
from app.services.database import save_user
from app.utils.validators import is_valid_age, is_valid_russian_name
from app.keyboards.menu import get_main_menu_keyboard
router = Router()


@router.message(RegistrationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if not is_valid_russian_name(message.text):
        await message.answer("Пожалуйста, введите корректное имя на русском языке.")
        return

    await state.update_data(name=message.text, username=message.from_user.username, user_id=message.from_user.id)
    await message.answer("Отлично! Теперь введите ваш возраст:")
    await state.set_state(RegistrationStates.waiting_for_age)


@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: Message, state: FSMContext):
    if not is_valid_age(message.text):
        await message.answer("Пожалуйста, введите корректный возраст (только цифры).")
        return
    user_id = message.from_user.id
    age = int(message.text)
    user_data = await state.get_data()
    await state.clear()

    await save_user(user_data['name'], age, user_data['username'], user_data['user_id'])

    await message.answer(
        f"Регистрация завершена!\n"
        f"Имя: {user_data['name']}\n"
        f"Возраст: {age}\n"
        f"Username: @{user_data['username'] or 'Не указан'}\n\n"
        "Добро пожаловать в главное меню!",
        reply_markup=get_main_menu_keyboard(user_id)
    )