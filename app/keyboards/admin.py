from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_user_management_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Список", callback_data="list_users")
    builder.button(text="🚫 Заблок.", callback_data="blocked_users")
    builder.button(text="🔒 Блок", callback_data="block_user")
    builder.button(text="🔓 Разблок", callback_data="unblock_user")
    builder.button(text="📊 Стат.", callback_data="user_statistics")
    builder.button(text="🔙 Назад", callback_data="back_to_menu")
    builder.adjust(3, 3)  # Располагаем кнопки в две строки по три кнопки
    return builder.as_markup()


def get_user_statistics_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Обновить статистику", callback_data="refresh_statistics")
    builder.button(text="⬅️ Назад к управлению", callback_data="manage_users")
    builder.adjust(1)
    return builder.as_markup()
