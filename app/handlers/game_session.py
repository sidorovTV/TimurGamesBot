from aiogram import Router
from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states.game_sassion import SessionCreation
from app.services.database import create_session, join_session
from app.utils.validators import is_valid_date, is_valid_time
from app.utils.message_cleaner import message_cleaner
from app.keyboards.menu import get_main_menu_keyboard

router = Router()


@router.message(SessionCreation.choosing_game)
async def process_custom_game(message: Message, state: FSMContext):
    await message_cleaner.add_user_message(message)
    await state.update_data(game=message.text)
    response = await message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):")
    await message_cleaner.add_message_to_delete(message.from_user.id, response)
    await state.set_state(SessionCreation.setting_date)


@router.message(SessionCreation.setting_date)
async def process_date(message: Message, state: FSMContext):
    await message_cleaner.add_user_message(message)
    if not is_valid_date(message.text):
        response = await message.answer("Пожалуйста, введите корректную дату в формате ГГГГ-ММ-ДД. "
                                        "Дата должна быть сегодняшней или будущей.")
        await message_cleaner.add_message_to_delete(message.from_user.id, response)
        return

    await state.update_data(date=message.text)
    response = await message.answer("Выберите время проведения игры (в формате ЧЧ:ММ):")
    await message_cleaner.add_message_to_delete(message.from_user.id, response)
    await state.set_state(SessionCreation.setting_time)


@router.message(SessionCreation.setting_time)
async def process_time(message: Message, state: FSMContext):
    await message_cleaner.add_user_message(message)
    if not is_valid_time(message.text):
        response = await message.answer("Пожалуйста, введите корректное время в формате ЧЧ:ММ (например, 14:30).")
        await message_cleaner.add_message_to_delete(message.from_user.id, response)
        return

    user_data = await state.get_data()
    date_string = user_data.get('date')

    if date_string:
        current_datetime = datetime.now()
        input_datetime = datetime.strptime(f"{date_string} {message.text}", "%Y-%m-%d %H:%M")

        if input_datetime <= current_datetime:
            response = await message.answer("Пожалуйста, выберите время в будущем.")
            await message_cleaner.add_message_to_delete(message.from_user.id, response)
            return

    await state.update_data(time=message.text)
    response = await message.answer("Укажите максимальное количество игроков:")
    await message_cleaner.add_message_to_delete(message.from_user.id, response)
    await state.set_state(SessionCreation.setting_max_players)


@router.message(SessionCreation.setting_max_players)
async def process_max_players(message: Message, state: FSMContext):
    await message_cleaner.add_user_message(message)
    await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)
    if not message.text.isdigit():
        response = await message.answer("Пожалуйста, введите число.")
        await message_cleaner.add_message_to_delete(message.from_user.id, response)
        return

    max_players = int(message.text)
    user_data = await state.get_data()
    session_id = await create_session(user_data['game'], user_data['date'], user_data['time'], max_players,
                                message.from_user.id)
    await state.clear()

    await join_session(session_id, message.from_user.id)

    # Создаем сообщение об успешном создании сессии
    success_message = (
        f"✅ Сессия успешно создана!\n\n"
        f"🆔 ID сессии: {session_id}\n"
        f"🎮 Игра: {user_data['game']}\n"
        f"📅 Дата: {user_data['date']}\n"
        f"🕒 Время: {user_data['time']}\n"
        f"👥 Максимум игроков: {max_players}\n\n"
        f"Вы автоматически присоединены к этой сессии."
    )

    # Отправляем сообщение с клавиатурой главного меню
    response = await message.answer(
        success_message,
        reply_markup=get_main_menu_keyboard(message.from_user.id)
    )

    await message_cleaner.add_message_to_delete(message.from_user.id, response)





