from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_sessions_list_keyboard(sessions):
    builder = InlineKeyboardBuilder()
    for session in sessions:
        session_id = session[0]
        builder.button(text=f"Подробнее о сессии {session_id}", callback_data=f"session_info_{session_id}")

    builder.button(text="Назад в меню", callback_data="back_to_menu")
    builder.adjust(1)  # Размещаем кнопки в один столбец
    return builder.as_markup()