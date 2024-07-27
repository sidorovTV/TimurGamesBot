from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.services.database import is_user_registered
from app.utils.message_cleaner import message_cleaner
from app.config_reader import config
from app.services.database import get_user_info, get_user_sessions, is_user_blocked

router = Router()


def get_main_menu_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Выбрать игру", callback_data="choose_game")
    builder.button(text="Список сессий", callback_data="list_sessions")
    builder.button(text="Мои сессии", callback_data="my_sessions")
    builder.button(text="Профиль", callback_data="profile")
    builder.button(text="Помощь", callback_data="help")

    # Добавляем кнопку управления пользователями для админа
    if user_id == config.admin_user_id:
        builder.button(text="Управление пользователями", callback_data="manage_users")

    builder.adjust(2)  # Размещаем кнопки в два столбца
    return builder.as_markup()


@router.callback_query(F.data == "manage_users")
async def manage_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    # Здесь добавьте логику для отображения списка пользователей или других опций управления
    await callback.message.edit_text("Панель управления пользователями:")


@router.callback_query(F.data == "main_menu")
async def return_to_main_menu(callback: CallbackQuery):
    user_id = callback.from_user.id

    if not await is_user_registered(user_id):
        await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
        await callback.answer(
            "Вы должны зарегистрироваться, чтобы использовать меню. Используйте команду /start для регистрации.")
        return
    if await is_user_blocked(user_id):
        await callback.answer("Ваш аккаунт заблокирован. Обратитесь к администратору.", show_alert=True)
        return
    await message_cleaner.delete_previous_messages(callback.bot, callback.from_user.id)
    response = await callback.message.answer("Главное меню:", reply_markup=get_main_menu_keyboard(user_id))
    await message_cleaner.add_message_to_delete(callback.from_user.id, response)
    await callback.answer()


@router.callback_query(F.data == "help")
async def show_help_from_menu(callback: CallbackQuery):
    text = ("Доступные команды:\n"
            "/start - Начать работу с ботом\n"
            "/menu - Открыть главное меню\n"
            "/help - Показать эту справку\n\n"
            "Используйте кнопки меню для навигации и создания игровых сессий.")
    builder = InlineKeyboardBuilder()
    builder.button(text="Назад в меню", callback_data="back_to_menu")
    await callback.message.edit_text(text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "choose_game")
async def choose_game(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="🦆 GGDuck", callback_data="game_GouseGouseDuck")
    builder.button(text="🎲 Другая игра", callback_data="game_other")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(2, 1)
    await callback.message.edit_text("Выберите игру или введите название:", reply_markup=builder.as_markup())


@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_info = await get_user_info(user_id)
    if not user_info:
        await callback.answer("Ошибка при получении данных профиля.", show_alert=True)
        return

    profile_text = (
        f"Ваш профиль:\n"
        f"Имя: {user_info['name']}\n"
        f"Возраст: {user_info['age']}\n"
        f"Количество созданных сессий: {user_info['created_sessions']}\n"
        f"Количество посещенных сессий: {user_info['attended_sessions']}"
    )

    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить профиль", callback_data="edit_profile")
    builder.button(text="Назад в меню", callback_data="back_to_menu")

    await callback.message.edit_text(profile_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "my_sessions")
async def show_my_sessions(callback: CallbackQuery):
    user_id = callback.from_user.id
    user_sessions = get_user_sessions(user_id)

    if not user_sessions:
        await callback.message.edit_text("У вас пока нет созданных или посещенных сессий.",
                                         reply_markup=InlineKeyboardBuilder().button(text="Назад в меню",
                                                                                     callback_data="back_to_menu").as_markup())
        return

    sessions_text = "Ваши сессии:\n\n"
    builder = InlineKeyboardBuilder()

    for session in user_sessions:
        session_type = "Создана вами" if session['is_creator'] else "Участие"
        sessions_text += f"ID: {session['id']}, Игра: {session['game']}, Дата: {session['date']}, {session_type}\n"
        builder.button(text=f"Сессия {session['id']}", callback_data=f"session_info_{session['id']}")

    builder.button(text="Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)

    await callback.message.edit_text(sessions_text, reply_markup=builder.as_markup())


@router.callback_query(F.data == "manage_users")
async def manage_users(callback: CallbackQuery):
    if callback.from_user.id != config.admin_user_id:
        await callback.answer("У вас нет доступа к этой функции.", show_alert=True)
        return

    # Здесь добавьте логику для отображения панели управления пользователями
    builder = InlineKeyboardBuilder()
    builder.button(text="Список пользователей", callback_data="list_users")
    builder.button(text="Заблокированные пользователи", callback_data="blocked_users")
    builder.button(text="Статистика", callback_data="user_statistics")
    builder.button(text="Назад в меню", callback_data="back_to_menu")
    builder.adjust(2)

    await callback.message.edit_text("Панель управления пользователями:", reply_markup=builder.as_markup())
