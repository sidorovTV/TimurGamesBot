from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_edit_profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Имя", callback_data="edit_name")],
        [InlineKeyboardButton(text="Возраст", callback_data="edit_age")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_edit")]
    ])