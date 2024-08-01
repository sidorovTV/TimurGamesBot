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

router = Router()


@router.callback_query(F.data == "manage_users")
async def manage_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.edit_text("У вас нет доступа к этой функции.", show_alert=True)
        return
    await callback.message.edit_text(
        "Панель управления пользователями:",
        reply_markup=get_manage_users_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await is_user_registered(user_id):
        await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
        await callback.edit_text(
            "Вы должны зарегистрироваться, чтобы использовать меню. Используйте команду /start для регистрации.")
        return
    if await is_user_blocked(user_id):
        await callback.edit_text("Ваш аккаунт заблокирован. Обратитесь к администратору.", show_alert=True)
        return
    await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
    response = await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))
    await message_cleaner.add_message_to_delete(callback.from_user.id, response)
    await callback.edit_text()


@router.callback_query(F.data == "help")
async def show_help_from_menu(callback: CallbackQuery):
    text = ("В случае ошибок или пожеланий прошу писать @flyerts\n\n"
            "Используйте кнопки меню для навигации и создания игровых сессий.")
    await callback.message.edit_text(text, reply_markup=get_back_menu_keyboard())


@router.callback_query(F.data == "choose_game")
async def choose_game(callback: CallbackQuery):
    response = await callback.message.edit_text("Выберите игру или введите название:",
                                                reply_markup=choose_game_keyboard())
    await message_cleaner.add_message_to_delete(callback.from_user.id, response)


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = await get_user_info(user_id)

    if not user_info:
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


@router.callback_query(F.data == "my_sessions")
async def show_my_sessions(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_sessions = await get_user_sessions(user_id)

    if not user_sessions:
        await callback.message.edit_text("У вас пока нет созданных или посещенных сессий.",
                                         reply_markup=get_back_menu_keyboard())
        return

    sessions_text = "Ваши сессии:\n\n"
    for session in user_sessions:
        session_type = "Создана вами" if session['is_creator'] else "Участие"
        sessions_text += f"ID: {session['id']}, Игра: {session['game']}, Дата: {session['date']}, {session_type}\n"

    await callback.message.edit_text(
        sessions_text, reply_markup=get_my_sessions_keyboard(user_sessions)
    )
