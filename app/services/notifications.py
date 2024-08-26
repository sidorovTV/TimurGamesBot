from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.database import get_upcoming_sessions
from app.utils.logger import notification_logger
from app.utils.message_cleaner import message_cleaner

async def send_session_reminders(bot: Bot):
    notification_logger.info("Starting to send session reminders")
    try:
        upcoming_sessions = await get_upcoming_sessions()
        notification_logger.info(f"Found {len(upcoming_sessions)} upcoming sessions for reminders")

        for session in upcoming_sessions:
            await message_cleaner.delete_previous_messages(bot, session['user_id'])

        for session in upcoming_sessions:
            try:
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
                response = await bot.send_message(session['user_id'], message, reply_markup=keyboard)
                await message_cleaner.add_message_to_delete(session['user_id'], response)
                notification_logger.info(f"Reminder sent for session {session['id']} to user {session['user_id']}")
            except Exception as e:
                notification_logger.error(
                    f"Error sending reminder for session {session['id']} to user {session['user_id']}: {str(e)}",
                    exc_info=True)

        notification_logger.info("Finished sending session reminders")
    except Exception as e:
        notification_logger.error(f"Error in send_session_reminders: {str(e)}", exc_info=True)