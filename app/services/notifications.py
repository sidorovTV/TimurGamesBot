from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.database import get_upcoming_sessions, update_session_confirmation


async def send_session_reminders(bot: Bot):
    upcoming_sessions = await get_upcoming_sessions()
    for session in upcoming_sessions:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить", callback_data=f"confirm_{session['id']}"),
                InlineKeyboardButton(text="Отклонить", callback_data=f"decline_{session['id']}")
            ]
        ])
        message = (f"Напоминание о предстоящей сессии:\n"
                   f"Игра: {session['game']}\n"
                   f"Дата: {session['date']}\n"
                   f"Время: {session['time']}\n"
                   f"Подтвердите ваше участие:")
        await bot.send_message(session['user_id'], message, reply_markup=keyboard)
