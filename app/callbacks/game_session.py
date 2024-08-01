from aiogram import F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.handlers.game_session import router
from app.services.database import (get_sessions,
                                   leave_session,
                                   join_session,
                                   get_session_participants,
                                   update_session_confirmation,
                                   remove_participant,
                                   get_session_participants,
                                   get_session_info)

from app.states.game_sassion import SessionCreation
from app.utils.message_cleaner import message_cleaner
from app.keyboards.sessions import get_sessions_list_keyboard
from app.services.database import update_session_confirmation
from app.keyboards.menu import get_main_menu_keyboard, back_to_main_menu_keyboard


@router.callback_query(F.data.startswith("game_"))
async def process_game_selection(callback: CallbackQuery, state: FSMContext):
    game = callback.data.split("_")[1]
    if game == "other":
        response = await callback.message.answer("Введите название игры:")
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)
        await state.set_state(SessionCreation.choosing_game)
    else:
        await state.update_data(game=game)
        response = await callback.message.answer("Выберите дату проведения игры (в формате ГГГГ-ММ-ДД):")
        await message_cleaner.add_message_to_delete(callback.from_user.id, response)
        await state.set_state(SessionCreation.setting_date)


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
    sessions = await get_sessions()
    if not sessions:
        text_message = "Нет доступных сессий."
        print(callback.message.from_user.id)
        await callback.message.edit_text(
            text_message,
            reply_markup=back_to_main_menu_keyboard(callback.message.from_user.id)
        )
        return

    text = format_sessions_list(sessions)
    keyboard = get_sessions_list_keyboard(sessions)

    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("session_info_"))
async def show_session_info(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[-1])
    sessions = await get_sessions()
    session = next((s for s in sessions if s[0] == session_id), None)

    if not session:
        await callback.edit_text("Сессия не найдена.")
        return

    session_id, game, date, time, max_players, current_players, creator_name = session
    participants = await get_session_participants(session_id)

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
    await leave_session(session_id, callback.from_user.id)
    await callback.edit_text("Вы успешно вышли из сессии!")
    await show_session_info(callback)  # Обновляем информацию о сессии


@router.callback_query(F.data.startswith("join_"))
async def join_game_session(callback: CallbackQuery):
    session_id = int(callback.data.split("_")[1])
    await join_session(session_id, callback.from_user.id)
    await callback.edit_text("Вы успешно присоединились к сессии!")
    await show_session_info(callback)  # Обновляем информацию о сессии


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    from app.keyboards.menu import get_main_menu_keyboard
    user_id = callback.from_user.id
    await callback.message.edit_text("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))


@router.callback_query(F.data.startswith("confirm_"))
async def confirm_session(callback: CallbackQuery, bot: Bot):
    session_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id
    user_name = callback.from_user.full_name
    username = callback.from_user.username

    await update_session_confirmation(session_id, user_id, "confirmed")
    confirm_text = ("Вы подтвердили свое участие в сессии!" + "\n\nСтатус: Подтверждено")

    # Отправляем сообщение с клавиатурой главного меню
    response = await callback.message.edit_text(
        confirm_text,
        reply_markup=get_main_menu_keyboard(callback.message.from_user.id)
    )

    # Отправляем уведомление всем участникам сессии
    session_info = await get_session_info(session_id)
    participants = await get_session_participants(session_id)

    notification_text = (
        f"Пользователь {user_name} (@{username}) подтвердил участие в сессии:\n"
        f"Игра: {session_info['game']}\n"
        f"Дата: {session_info['date']}\n"
        f"Время: {session_info['time']}"
    )

    for participant in participants:
        if participant['id'] != user_id:
            await bot.send_message(participant['id'], notification_text,
                                   reply_markup=get_main_menu_keyboard(participant['id']))


@router.callback_query(F.data.startswith("decline_"))
async def decline_session(callback: CallbackQuery, bot: Bot):
    session_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    await update_session_confirmation(session_id, user_id, "declined")
    await remove_participant(session_id, user_id)
    await callback.message.edit_text(
        "Вы отклонили участие в сессии и были удалены из списка участников." + "\n\nСтатус: Отклонено и удалено из сессии")

    # Отправляем уведомление всем участникам сессии
    session_info = await get_session_info(session_id)
    participants = await get_session_participants(session_id)

    notification_text = (
        f"Пользователь {callback.from_user.full_name} (@{callback.from_user.username}) "
        f"отклонил участие и был удален из сессии:\n"
        f"Игра: {session_info['game']}\n"
        f"Дата: {session_info['date']}\n"
        f"Время: {session_info['time']}"
    )

    for participant in participants:
        if participant['id'] != user_id:
            await bot.send_message(participant['id'], notification_text)
