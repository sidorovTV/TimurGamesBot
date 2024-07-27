from aiogram import Router, F
from datetime import datetime
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.services.database import create_session, get_sessions, join_session, get_session_participants, leave_session
from app.utils.validators import is_valid_date, is_valid_time
from app.utils.message_cleaner import message_cleaner

router = Router()


class SessionCreation(StatesGroup):
    choosing_game = State()
    setting_date = State()
    setting_time = State()
    setting_max_players = State()


@router.callback_query(F.data.startswith("game_"))
async def process_game_selection(callback: CallbackQuery, state: FSMContext):
    await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
    game = callback.data.split("_")[1]
    if game == "other":
        response = await callback.message.edit_text("Введите название игры:")
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)
        await state.set_state(SessionCreation.choosing_game)
    else:
        await state.update_data(game=game)
        response = await callback.message.edit_text("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):")
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)
        await state.set_state(SessionCreation.setting_date)


@router.message(SessionCreation.choosing_game)
async def process_custom_game(message: Message, state: FSMContext):
    await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)
    await message_cleaner.add_user_message(message)
    await state.update_data(game=message.text)
    response = await message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):")
    await message_cleaner.add_message_to_delete(message.from_user.id, response)
    await state.set_state(SessionCreation.setting_date)


@router.message(SessionCreation.setting_date)
async def process_date(message: Message, state: FSMContext):
    await message_cleaner.add_user_message(message)
    await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)
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
    await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)
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
    session_id = create_session(user_data['game'], user_data['date'], user_data['time'], max_players,
                                message.from_user.id)
    await state.clear()
    await message_cleaner.delete_previous_messages(message.bot, message.from_user.id)

    join_session(session_id, message.from_user.id)
    response = await message.answer(f"Сессия успешно создана! ID сессии: {session_id}")

    await message_cleaner.add_message_to_delete(message.from_user.id, response)


@router.callback_query(F.data == "list_sessions")
async def show_sessions(callback: CallbackQuery):
    sessions = get_sessions()
    if not sessions:
        await callback.message.edit_text("Нет доступных сессий.")
        return

    text = "Доступные сессии:\n\n"
    builder = InlineKeyboardBuilder()
    for session in sessions:
        session_id, game, date, time, max_players, current_players, creator_name = session
        text += (f"ID: {session_id}, Игра: {game}\n"
                 f"Дата: {date}, Время: {time}\n"
                 f"Игроки: {current_players}/{max_players}\n"
                 f"Создатель: {creator_name}\n"
                 f"-------------------\n")
        builder.button(text=f"Подробнее о сессии {session_id}", callback_data=f"session_info_{session_id}")

    builder.button(text="Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)  # Размещаем кнопки в один столбец
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("session_info_"))
async def show_session_info(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[-1])
    sessions = get_sessions()
    session = next((s for s in sessions if s[0] == session_id), None)

    if not session:
        await callback.answer("Сессия не найдена.")
        return

    session_id, game, date, time, max_players, current_players, creator_name = session
    participants = get_session_participants(session_id)

    text = (f"Информация о сессии:\n"
            f"ID: {session_id}\n"
            f"Игра: {game}\n"
            f"Дата: {date}, Время: {time}\n"
            f"Игроки: {current_players}/{max_players}\n"
            f"Создатель: {creator_name}\n\n"
            f"Участники:\n")

    for user_id, name, username in participants:
        text += f"- {name} (@{username or 'Нет username'})\n"

    builder = InlineKeyboardBuilder()

    # Проверяем, является ли текущий пользователь участником сессии
    user_id = callback.from_user.id
    is_participant = any(user_id == participant[0] for participant in participants)

    if is_participant:
        builder.button(text="Выйти из сессии", callback_data=f"leave_{session_id}")
    else:
        builder.button(text="Присоединиться", callback_data=f"join_{session_id}")

    builder.button(text="Назад к списку", callback_data="list_sessions")
    builder.adjust(1)  # Размещаем кнопки в один столбец

    await callback.message.edit_text(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("leave_"))
async def leave_game_session(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[1])
    leave_session(session_id, callback.from_user.id)
    await callback.answer("Вы успешно вышли из сессии!")
    await show_session_info(callback)  # Обновляем информацию о сессии


@router.callback_query(F.data.startswith("join_"))
async def join_game_session(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[1])
    join_session(session_id, callback.from_user.id)
    await callback.answer("Вы успешно присоединились к сессии!")
    await show_session_info(callback)  # Обновляем информацию о сессии


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    from app.handlers.menu import get_main_menu_keyboard
    user_id = callback.from_user.id
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))
