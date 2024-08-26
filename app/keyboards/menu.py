from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config_reader import config
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🎮 Выбрать игру", callback_data="choose_game")
    builder.button(text="📋 Список сессий", callback_data="list_sessions")
    builder.button(text="🔖 Мои сессии", callback_data="my_sessions")
    builder.button(text="👤 Профиль", callback_data="profile")
    builder.button(text="❓ Помощь", callback_data="help")

    # Добавляем кнопку управления пользователями для админа
    if user_id == config.admin_user_id:
        builder.button(text="⚙️ Управление", callback_data="manage_users")

    builder.adjust(2)  # Размещаем кнопки в два столбца
    return builder.as_markup()

def back_to_main_menu_keyboard(user_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    return builder.as_markup()

def choose_game_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🦆 GGDuck", callback_data="game_GouseGouseDuck")
    builder.button(text="🎲 Другая игра", callback_data="game_other")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(2, 1)
    return builder.as_markup()


def show_profile_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Изменить профиль", callback_data="edit_profile")
    builder.button(text="Назад в меню", callback_data="back_to_menu")
    return builder.as_markup()


def get_my_sessions_keyboard(user_sessions):
    builder = InlineKeyboardBuilder()

    for session in user_sessions:
        builder.button(text=f"Сессия {session['id']}", callback_data=f"session_info_{session['id']}")

    builder.button(text="История", callback_data="session_history")
    builder.button(text="Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)

    return builder.as_markup()


def get_manage_users_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Список", callback_data="list_users")
    builder.button(text="🚫 Заблокированные", callback_data="blocked_users")
    builder.button(text="📊 Статистика", callback_data="user_statistics")
    builder.button(text="⬅️ Назад", callback_data="back_to_menu")
    builder.adjust(2)
    return builder.as_markup()


def get_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Отменить и вернуться в главное меню", callback_data="cancel_session_creation")]
    ])