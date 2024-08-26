from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import CallbackQuery

from app.keyboards.menu import get_cancel_keyboard


def get_time_picker_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="00:00", callback_data="time_00:00"),
            InlineKeyboardButton(text="01:00", callback_data="time_01:00"),
            InlineKeyboardButton(text="02:00", callback_data="time_02:00"),
            InlineKeyboardButton(text="03:00", callback_data="time_03:00"),
        ],
        [
            InlineKeyboardButton(text="04:00", callback_data="time_04:00"),
            InlineKeyboardButton(text="05:00", callback_data="time_05:00"),
            InlineKeyboardButton(text="06:00", callback_data="time_06:00"),
            InlineKeyboardButton(text="07:00", callback_data="time_07:00"),
        ],
        [
            InlineKeyboardButton(text="08:00", callback_data="time_08:00"),
            InlineKeyboardButton(text="09:00", callback_data="time_09:00"),
            InlineKeyboardButton(text="10:00", callback_data="time_10:00"),
            InlineKeyboardButton(text="11:00", callback_data="time_11:00"),
        ],
        [
            InlineKeyboardButton(text="12:00", callback_data="time_12:00"),
            InlineKeyboardButton(text="13:00", callback_data="time_13:00"),
            InlineKeyboardButton(text="14:00", callback_data="time_14:00"),
            InlineKeyboardButton(text="15:00", callback_data="time_15:00"),
        ],
        [
            InlineKeyboardButton(text="16:00", callback_data="time_16:00"),
            InlineKeyboardButton(text="17:00", callback_data="time_17:00"),
            InlineKeyboardButton(text="18:00", callback_data="time_18:00"),
            InlineKeyboardButton(text="19:00", callback_data="time_19:00"),
        ],
        [
            InlineKeyboardButton(text="20:00", callback_data="time_20:00"),
            InlineKeyboardButton(text="21:00", callback_data="time_21:00"),
            InlineKeyboardButton(text="22:00", callback_data="time_22:00"),
            InlineKeyboardButton(text="23:00", callback_data="time_23:00"),
        ],
        [
            InlineKeyboardButton(text="Другое время", callback_data="time_custom"),
        ],
        [
            InlineKeyboardButton(text="Отмена", callback_data="cancel_session_creation")
        ]
    ])
    return keyboard

async def process_time_picking(callback: CallbackQuery):
    if callback.data == "time_custom":
        await callback.message.edit_text("Введите время в формате ЧЧ:ММ (например, 14:30):")
        return None
    else:
        time = callback.data.split("_")[1]
        await callback.message.edit_text(f"Вы выбрали время: {time}")
        return time