from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.states.game_sassion import SessionCreation
from app.services.database import create_session, join_session
from app.utils.validators import is_valid_date, is_valid_time
from app.utils.message_cleaner import message_cleaner
from app.keyboards.menu import get_main_menu_keyboard, get_cancel_keyboard
from app.utils.logger import session_logger

router = Router()


@router.callback_query(F.data.startswith("game_"))
async def process_game_selection(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    game = callback.data.split("_")[1]
    session_logger.info(f"User {user_id} selected game: {game}")
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    if game == "other":
        response = await callback.message.answer("Введите название игры:", reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.set_state(SessionCreation.choosing_game)
        session_logger.info(f"User {user_id} prompted to enter custom game name")
    else:
        await state.update_data(game=game)
        response = await callback.message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):",
                                                 reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.set_state(SessionCreation.setting_date)
        session_logger.info(f"User {user_id} prompted to enter date for game {game}")


@router.message(SessionCreation.choosing_game)
async def process_custom_game(message: Message, state: FSMContext):
    user_id = message.from_user.id
    game_name = message.text
    session_logger.info(f"User {user_id} entered custom game name: {game_name}")
    await message_cleaner.add_user_message(message)
    await state.update_data(game=game_name)
    response = await message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):",
                                    reply_markup=get_cancel_keyboard())
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(SessionCreation.setting_date)
    session_logger.info(f"User {user_id} prompted to enter date for custom game {game_name}")


@router.message(SessionCreation.setting_date)
async def process_date(message: Message, state: FSMContext):
    user_id = message.from_user.id
    date_input = message.text
    session_logger.info(f"User {user_id} entered date: {date_input}")
    await message_cleaner.add_user_message(message)
    if not is_valid_date(date_input):
        session_logger.warning(f"User {user_id} entered invalid date: {date_input}")
        response = await message.answer("Пожалуйста, введите корректную дату в формате ГГГГ-ММ-ДД. "
                                        "Дата должна быть сегодняшней или будущей.", reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
        return

    await state.update_data(date=date_input)
    response = await message.answer("Выберите время проведения игры (в формате ЧЧ:ММ):",
                                    reply_markup=get_cancel_keyboard())
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(SessionCreation.setting_time)
    session_logger.info(f"User {user_id} prompted to enter time for the game")


@router.message(SessionCreation.setting_time)
async def process_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    time_input = message.text
    session_logger.info(f"User {user_id} entered time: {time_input}")
    await message_cleaner.add_user_message(message)
    if not is_valid_time(time_input):
        session_logger.warning(f"User {user_id} entered invalid time: {time_input}")
        response = await message.answer("Пожалуйста, введите корректное время в формате ЧЧ:ММ (например, 14:30).",
                                        reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
        return

    await state.update_data(time=time_input)
    response = await message.answer("Укажите максимальное количество игроков:", reply_markup=get_cancel_keyboard())
    await message_cleaner.add_message_to_delete(user_id, response)
    await state.set_state(SessionCreation.setting_max_players)
    session_logger.info(f"User {user_id} prompted to enter max players for the game")


@router.message(SessionCreation.setting_max_players)
async def process_max_players(message: Message, state: FSMContext):
    user_id = message.from_user.id
    max_players_input = message.text
    session_logger.info(f"User {user_id} entered max players: {max_players_input}")
    await message_cleaner.add_user_message(message)
    await message_cleaner.delete_previous_messages(message.bot, user_id)
    if not max_players_input.isdigit():
        session_logger.warning(f"User {user_id} entered invalid max players: {max_players_input}")
        response = await message.answer("Пожалуйста, введите число.", reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
        return

    max_players = int(max_players_input)
    user_data = await state.get_data()
    session_id = await create_session(user_data['game'], user_data['date'], user_data['time'], max_players, user_id)
    await state.clear()

    await join_session(session_id, user_id)

    success_message = (
        f"✅ Сессия успешно создана!\n\n"
        f"🆔 ID сессии: {session_id}\n"
        f"🎮 Игра: {user_data['game']}\n"
        f"📅 Дата: {user_data['date']}\n"
        f"🕒 Время: {user_data['time']}\n"
        f"👥 Максимум игроков: {max_players}\n\n"
        f"Вы автоматически присоединены к этой сессии."
    )

    response = await message.answer(
        success_message,
        reply_markup=get_main_menu_keyboard(user_id)
    )

    await message_cleaner.add_message_to_delete(user_id, response)
    session_logger.info(f"User {user_id} successfully created session {session_id} for game {user_data['game']}")


@router.callback_query(F.data == "cancel_session_creation")
async def cancel_session_creation(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    session_logger.info(f"User {user_id} cancelled session creation")
    await state.clear()
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    response = await callback.message.answer("Создание сессии отменено. Вы вернулись в главное меню.",
                                             reply_markup=get_main_menu_keyboard(user_id))
    await message_cleaner.add_message_to_delete(user_id, response)
