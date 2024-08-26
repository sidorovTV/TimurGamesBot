from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.states.game_sassion import SessionCreation
from app.services.database import create_session, join_session
from app.utils.validators import is_valid_time
from app.utils.message_cleaner import message_cleaner
from app.keyboards.menu import get_main_menu_keyboard, get_cancel_keyboard
from app.utils.logger import session_logger
from aiogram_calendar import SimpleCalendar, SimpleCalendarCallback
from app.keyboards.time_picker import get_time_picker_keyboard
from app.utils import check_user_not_blocked
from app.utils.calendar import CustomSimpleCalendar

router = Router()


@router.callback_query(F.data.startswith("game_"))
@check_user_not_blocked
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
        await state.set_state(SessionCreation.setting_date)
        await show_calendar(callback.message, state)
        session_logger.info(f"User {user_id} prompted to enter date for game {game}")


@router.message(SessionCreation.choosing_game)
@check_user_not_blocked
async def process_custom_game(message: Message, state: FSMContext):
    user_id = message.from_user.id
    game_name = message.text
    session_logger.info(f"User {user_id} entered custom game name: {game_name}")
    await message_cleaner.add_user_message(message)
    await state.update_data(game=game_name)
    await state.set_state(SessionCreation.setting_date)
    await message_cleaner.delete_previous_messages(message.bot, user_id)
    await show_calendar(message, state)
    session_logger.info(f"User {user_id} prompted to enter date for custom game {game_name}")


async def show_calendar(message: Message, state: FSMContext):
    calendar = CustomSimpleCalendar()
    response = await message.answer(
        "Выберите дату проведения игры:",
        reply_markup=await calendar.start_calendar()
    )

    await message_cleaner.add_message_to_delete(message.from_user.id, response)
    await state.update_data(calendar_message_id=response.message_id)


@router.callback_query(SimpleCalendarCallback.filter())
@check_user_not_blocked
async def process_calendar(callback: CallbackQuery, callback_data: SimpleCalendarCallback, state: FSMContext):
    calendar = SimpleCalendar()
    selected, date = await calendar.process_selection(callback, callback_data)
    if selected:
        user_id = callback.from_user.id
        await state.update_data(date=date.strftime("%Y-%m-%d"))
        await state.set_state(SessionCreation.setting_time)

        # Удаляем сообщение с календарем
        state_data = await state.get_data()
        calendar_message_id = state_data.get('calendar_message_id')
        if calendar_message_id:
            await callback.bot.delete_message(user_id, calendar_message_id)

        await message_cleaner.delete_previous_messages(callback.bot, user_id)
        response = await callback.message.answer("Выберите время проведения игры:",
                                                 reply_markup=get_time_picker_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)


@router.callback_query(F.data.startswith("time_"))
@check_user_not_blocked
async def process_time_selection(callback: CallbackQuery, state: FSMContext):
    if callback.data == "cancel_session_creation":
        await cancel_session_creation(callback, state)
        return

    if callback.data == "time_custom":
        await state.set_state(SessionCreation.setting_custom_time)
        await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
        response = await callback.message.answer(
            "Введите время в формате ЧЧ:ММ (например, 14:30):",
            reply_markup=get_cancel_keyboard()
        )
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)
    else:
        time = callback.data.split("_")[1]
        await state.update_data(time=time)
        await state.set_state(SessionCreation.setting_max_players)
        await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
        response = await callback.message.answer(
            "Укажите максимальное количество игроков:",
            reply_markup=get_cancel_keyboard()
        )
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)

    await callback.answer()


@router.message(SessionCreation.setting_custom_time)
@check_user_not_blocked
async def process_custom_time(message: Message, state: FSMContext):
    user_id = message.from_user.id
    time_input = message.text
    session_logger.info(f"User {user_id} entered custom time: {time_input}")
    await message_cleaner.add_user_message(message)

    if is_valid_time(time_input):
        await state.update_data(time=time_input)
        await state.set_state(SessionCreation.setting_max_players)
        await message_cleaner.delete_previous_messages(message.bot, user_id)
        response = await message.answer("Укажите максимальное количество игроков:", reply_markup=get_cancel_keyboard())
        await message_cleaner.add_message_to_delete(user_id, response)
    else:
        response = await message.answer(
            "Неверный формат времени. Пожалуйста, введите время в формате ЧЧ:ММ (например, 14:30):")
        await message_cleaner.add_message_to_delete(user_id, response)


@router.message(SessionCreation.setting_max_players)
@check_user_not_blocked
async def process_max_players(message: Message, state: FSMContext):
    user_id = message.from_user.id
    max_players_input = message.text
    session_logger.info(f"User {user_id} entered max players: {max_players_input}")
    await message_cleaner.add_user_message(message)

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

    await message_cleaner.delete_previous_messages(message.bot, user_id)

    success_message = (
        f"✅ Сессия успешно создана!\n\n"
        f"🎴 ID сессии: {session_id}\n"
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
@check_user_not_blocked
async def cancel_session_creation(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id

    # Получаем ID сообщения с календарем из состояния
    state_data = await state.get_data()
    calendar_message_id = state_data.get('calendar_message_id')

    # Удаляем сообщение с календарем, если его ID сохранен
    if calendar_message_id:
        try:
            await callback.bot.delete_message(user_id, calendar_message_id)
        except Exception as e:
            session_logger.error(f"Failed to delete calendar message: {e}")

    # Удаляем все остальные сообщения
    await message_cleaner.delete_previous_messages(callback.bot, user_id)

    # Очищаем состояние
    await state.clear()

    # Отправляем сообщение о возврате в главное меню
    response = await callback.message.answer(
        "Создание сессии отменено. Вы вернулись в главное меню:",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    await message_cleaner.add_message_to_delete(user_id, response)

    # Отвечаем на callback, чтобы убрать "часики" на кнопке
    await callback.answer()

    session_logger.info(f"User {user_id} cancelled session creation and returned to main menu")