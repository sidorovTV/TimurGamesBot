import asyncio
from aiogram import F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.callbacks.menu import show_my_sessions
from app.handlers.game_session import router
from app.handlers.help import get_back_menu_keyboard
from app.services.database import (get_sessions,
                                   leave_session,
                                   join_session,
                                   remove_participant,
                                   get_session_participants,
                                   get_session_info,
                                   delete_session,
                                   get_user_session_history, add_user_session_event)

from app.states.game_sassion import SessionCreation
from app.utils.message_cleaner import message_cleaner
from app.keyboards.sessions import get_sessions_list_keyboard
from app.services.database import update_session_confirmation
from app.keyboards.menu import get_main_menu_keyboard, back_to_main_menu_keyboard
from app.utils.logger import session_logger

@router.callback_query(F.data.startswith("game_"))
async def process_game_selection(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    game = callback.data.split("_")[1]
    session_logger.info(f"User {user_id} selected game: {game}")
    if game == "other":
        response = await callback.message.answer("Введите название игры:")
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.set_state(SessionCreation.choosing_game)
        session_logger.info(f"User {user_id} prompted to enter custom game name")
    else:
        await state.update_data(game=game)
        response = await callback.message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):")
        await message_cleaner.add_message_to_delete(user_id, response)
        await state.set_state(SessionCreation.setting_date)
        session_logger.info(f"User {user_id} prompted to enter date for game {game}")


def format_sessions_list(sessions):
    text = "Доступные сессии:\n\n"
    for session in sessions:
        session_id, game, date, time, max_players, current_players, creator_name = session
        text += (f"ID: {session_id}, Игра: {game}\n"
                 f"Дата: {date}, Время: {time}\n"
                 f"Игроки: {current_players}/{max_players}\n"
                 f"Создатель: {creator_name}\n"
                 f"-------------------\n")
    return text


@router.callback_query(F.data == "list_sessions")
async def show_sessions(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_logger.info(f"User {user_id} requested session list")
    sessions = await get_sessions()
    if not sessions:
        text_message = "Нет доступных сессий."
        session_logger.info(f"No available sessions for user {user_id}")
        await callback.message.edit_text(
            text_message,
            reply_markup=back_to_main_menu_keyboard(user_id)
        )
        return

    text = format_sessions_list(sessions)
    keyboard = get_sessions_list_keyboard(sessions)

    await callback.message.edit_text(text, reply_markup=keyboard)
    session_logger.info(f"Session list displayed for user {user_id}")


@router.callback_query(F.data.startswith("session_info_"))
async def show_session_info(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[-1])
    session_logger.info(f"User {user_id} requested info for session {session_id}")

    session = await get_session_info(session_id)  # Предполагаем, что эта функция возвращает полную информацию о сессии

    if not session:
        session_logger.warning(f"Session {session_id} not found for user {user_id}")
        await callback.answer("Сессия не найдена.", show_alert=True)
        return

    participants = await get_session_participants(session_id)

    text = (f"Информация о сессии:\n"
            f"ID: {session_id}\n"
            f"Игра: {session['game']}\n"
            f"Дата: {session['date']}, Время: {session['time']}\n"
            f"Игроки: {len(participants)}/{session['max_players']}\n"
            f"Создатель: {session['creator_name']}\n\n"
            f"Участники:\n")

    for participant in participants:
        text += f"- {participant['name']} (@{participant['username'] or 'Нет username'})\n"

    builder = InlineKeyboardBuilder()

    is_participant = any(participant['id'] == user_id for participant in participants)
    is_creator = session['creator_id'] == user_id  # Теперь мы сравниваем user_id

    if is_creator:
        builder.button(text="Удалить сессию", callback_data=f"delete_session_{session_id}")
    elif is_participant:
        builder.button(text="Выйти из сессии", callback_data=f"leave_{session_id}")
    else:
        builder.button(text="Присоединиться", callback_data=f"join_{session_id}")

    builder.button(text="Назад к списку", callback_data="list_sessions")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    session_logger.info(f"Session info displayed for user {user_id}, session {session_id}")

@router.callback_query(F.data.startswith("leave_"))
async def leave_game_session(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[1])
    session_logger.info(f"User {user_id} attempting to leave session {session_id}")
    await leave_session(session_id, user_id)
    await callback.answer("Вы успешно вышли из сессии!", show_alert=True)
    session_logger.info(f"User {user_id} left session {session_id}")
    await show_session_info(callback)


@router.callback_query(F.data.startswith("join_"))
async def join_game_session(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[1])
    session_logger.info(f"User {user_id} attempting to join session {session_id}")
    await join_session(session_id, user_id)
    await callback.answer("Вы успешно присоединились к сессии!", show_alert=True)
    session_logger.info(f"User {user_id} joined session {session_id}")
    await show_session_info(callback)


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_logger.info(f"User {user_id} returning to main menu")
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_session(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[1])
    user_name = callback.from_user.full_name
    username = callback.from_user.username

    session_logger.info(f"User {user_id} confirming participation in session {session_id}")
    await update_session_confirmation(session_id, user_id, "confirmed")
    await add_user_session_event(user_id, session_id, "confirmed")

    await callback.message.delete()
    await message_cleaner.delete_previous_messages(bot, user_id)
    new_message = await callback.message.answer(
        "Вы подтвердили свое участие в сессии. Вот главное меню:",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    await message_cleaner.add_message_to_delete(user_id, new_message)

    session_info = await get_session_info(session_id)
    participants = await get_session_participants(session_id)

    notification_text = (
        f"Пользователь {user_name} (@{username or 'Нет username'}) подтвердил участие в сессии:\n"
        f"Игра: {session_info['game']}\n"
        f"Дата: {session_info['date']}\n"
        f"Время: {session_info['time']}"
    )

    for participant in participants:
        if participant['id'] != user_id:
            try:
                confirm_response = await bot.send_message(participant['id'], notification_text)
                session_logger.info(f"Notification sent to user {participant['id']} about {user_id} confirming session {session_id}")
                await message_cleaner.add_message_to_delete(callback.from_user.id, confirm_response)
                await asyncio.sleep(5)
                await message_cleaner.delete_previous_messages(bot, user_id)

                new_message = await callback.message.answer(
                    "Вот главное меню:",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                await message_cleaner.add_message_to_delete(user_id, new_message)

            except Exception as e:
                session_logger.error(f"Failed to send notification to user {participant['id']}: {e}", exc_info=True)

    session_logger.info(f"User {user_id} confirmed participation in session {session_id}. Notifications sent.")
    await callback.answer()

@router.callback_query(F.data.startswith("decline_"))
async def decline_session(callback: CallbackQuery, bot: Bot):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[1])
    user_name = callback.from_user.full_name
    username = callback.from_user.username

    session_logger.info(f"User {user_id} declining participation in session {session_id}")

    await callback.message.delete()
    await message_cleaner.delete_previous_messages(bot, user_id)

    await update_session_confirmation(session_id, user_id, "declined")
    await remove_participant(session_id, user_id)
    await add_user_session_event(user_id, session_id, "declined")

    new_message = await callback.message.answer(
        "Вы отклонили участие в сессии и были удалены из списка участников. Вот главное меню:",
        reply_markup=get_main_menu_keyboard(user_id)
    )
    await message_cleaner.add_message_to_delete(user_id, new_message)

    session_info = await get_session_info(session_id)
    participants = await get_session_participants(session_id)

    notification_text = (
        f"Пользователь {user_name} (@{username or 'Нет username'}) отклонил участие и был удален из сессии:\n"
        f"Игра: {session_info['game']}\n"
        f"Дата: {session_info['date']}\n"
        f"Время: {session_info['time']}"
    )

    for participant in participants:
        if participant['id'] != user_id:
            try:
                decline_response = await bot.send_message(participant['id'], notification_text)
                session_logger.info(f"Notification sent to user {participant['id']} about {user_id} declining session {session_id}")
                await message_cleaner.add_message_to_delete(callback.from_user.id, decline_response)
                await asyncio.sleep(5)
                await message_cleaner.delete_previous_messages(bot, user_id)

                new_message = await callback.message.answer(
                    "Вот главное меню:",
                    reply_markup=get_main_menu_keyboard(user_id)
                )
                await message_cleaner.add_message_to_delete(user_id, new_message)

            except Exception as e:
                session_logger.error(f"Failed to send notification to user {participant['id']}: {e}", exc_info=True)

    session_logger.info(f"User {user_id} declined participation in session {session_id}. Notifications sent.")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_session_"))
async def delete_game_session(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_id = int(callback.data.split("_")[-1])
    session_logger.info(f"User {user_id} attempting to delete session {session_id}")

    success = await delete_session(session_id, user_id)

    if success:
        await add_user_session_event(user_id, session_id, "deleted")
        await callback.answer("Сессия успешно удалена.", show_alert=True)
        await show_my_sessions(callback)
        session_logger.info(f"Session {session_id} successfully deleted by user {user_id}")
    else:
        await callback.answer("Не удалось удалить сессию. Возможно, у вас нет прав на это действие.", show_alert=True)
        session_logger.warning(f"Failed to delete session {session_id} by user {user_id}")


@router.callback_query(F.data == "session_history")
async def show_session_history(callback: CallbackQuery):
    user_id = callback.from_user.id
    session_logger.info(f"User {user_id} requested session history")

    history = await get_user_session_history(user_id)

    if not history:
        await callback.answer("У вас пока нет истории событий.", show_alert=True)
        return

    history_text = ""
    for event in history:
        event_type_text = {
            "confirmed": "подтвердил ",
            "declined": "отклонил ",
            "deleted": "удалил"
        }.get(event['event_type'], event['event_type'])

        history_text += (f"{event['timestamp'][11:16]} - {event['user_name']} {event_type_text} "
                         f"(ID: {event['session_id']})\n")

    # Разбиваем историю на части по 200 символов
    max_length = 200
    history_parts = [history_text[i:i+max_length] for i in range(0, len(history_text), max_length)]

    await callback.answer(history_parts[0], show_alert=True)

    session_logger.info(f"Session history displayed for user {user_id}")
