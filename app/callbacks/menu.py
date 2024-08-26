from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.services.database import is_user_registered
from app.utils.message_cleaner import message_cleaner
from app.config_reader import config
from app.services.database import get_user_info, get_user_sessions, is_user_blocked
from app.keyboards.menu import (get_main_menu_keyboard,
                                choose_game_keyboard,
                                show_profile_keyboard,
                                get_my_sessions_keyboard,
                                get_manage_users_keyboard)
from app.handlers.help import get_back_menu_keyboard
from app.utils.logger import menu_logger

router = Router()


@router.callback_query(F.data == "manage_users")

async def manage_users(callback: CallbackQuery):
    menu_logger.info(f"User {callback.from_user.id} accessed manage_users menu")
    if callback.from_user.id != config.admin_user_id:
        menu_logger.warning(f"Unauthorized access attempt to manage_users by user {callback.from_user.id}")
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return
    await callback.message.edit_text(
        "Панель управления пользователями:",
        reply_markup=get_manage_users_keyboard()
    )
    menu_logger.info(f"Manage users menu displayed for admin {callback.from_user.id}")


@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id
    menu_logger.info(f"User {user_id} returning to main menu")

    if not await is_user_registered(user_id):
        menu_logger.warning(f"Unregistered user {user_id} attempted to access main menu")
        await message_cleaner.delete_previous_messages(callback.bot, user_id)
        await callback.edit_text(
            "Вы должны зарегистрироваться, чтобы использовать меню. Используйте команду /start для регистрации.")
        return
    if await is_user_blocked(user_id):
        menu_logger.warning(f"Blocked user {user_id} attempted to access main menu")
        await callback.edit_text("Ваш аккаунт заблокирован. Обратитесь к администратору.", show_alert=True)
        return
    await message_cleaner.delete_previous_messages(callback.bot, user_id)
    response = await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))
    await message_cleaner.add_message_to_delete(user_id, response)
    await callback.edit_text()
    menu_logger.info(f"Main menu displayed for user {user_id}")


@router.callback_query(F.data == "help")
async def show_help_from_menu(callback: CallbackQuery):
    menu_logger.info(f"User {callback.from_user.id} accessed help menu")
    text = ("В случае ошибок или пожеланий прошу писать @flyerts\n\n"
            "Используйте кнопки меню для навигации и создания игровых сессий.")
    await callback.message.edit_text(text, reply_markup=get_back_menu_keyboard())
    menu_logger.info(f"Help information displayed for user {callback.from_user.id}")


@router.callback_query(F.data == "choose_game")
async def choose_game(callback: CallbackQuery):
    menu_logger.info(f"User {callback.from_user.id} accessed game selection menu")
    response = await callback.message.edit_text("Выберите игру или введите название:",
                                                reply_markup=choose_game_keyboard())
    await message_cleaner.add_message_to_delete(callback.from_user.id, response)
    menu_logger.info(f"Game selection menu displayed for user {callback.from_user.id}")


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    menu_logger.info(f"User {user_id} accessed profile information")
    user_info = await get_user_info(user_id)

    if not user_info:
        menu_logger.error(f"Failed to retrieve profile information for user {user_id}")
        await callback.edit_text("Ошибка при получении данных профиля.", show_alert=True)
        return

    profile_text = (
        f"Ваш профиль:\n"
        f"Имя: {user_info['name']}\n"
        f"Возраст: {user_info['age']}\n"
        f"Количество созданных сессий: {user_info['created_sessions']}\n"
        f"Количество посещенных сессий: {user_info['attended_sessions']}"
    )

    await callback.message.edit_text(profile_text, reply_markup=show_profile_keyboard())
    menu_logger.info(f"Profile information displayed for user {user_id}")


@router.callback_query(F.data == "my_sessions")
async def show_my_sessions(callback: CallbackQuery):
    user_id = callback.from_user.id
    menu_logger.info(f"User {user_id} accessed their sessions")
    user_sessions = await get_user_sessions(user_id)

    if not user_sessions:
        menu_logger.info(f"No upcoming sessions found for user {user_id}")
        await callback.message.edit_text("У вас нет предстоящих сессий.",
                                         reply_markup=get_back_menu_keyboard())
        return

    sessions_text = "Ваши предстоящие сессии:\n\n"
    for session in user_sessions:
        session_type = "Создана вами" if session['is_creator'] else "Участие"
        sessions_text += (f"ID: {session['id']}, Игра: {session['game']}\n"
                          f"Дата: {session['date']}, Время: {session['time']}\n"
                          f"Игроки: {session['current_players']}/{session['max_players']}\n"
                          f"Статус: {session_type}\n"
                          f"-------------------\n")

    await callback.message.edit_text(
        sessions_text, reply_markup=get_my_sessions_keyboard(user_sessions)
    )
    menu_logger.info(f"Upcoming sessions list displayed for user {user_id}")
