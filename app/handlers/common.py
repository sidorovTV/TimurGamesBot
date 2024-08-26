# app/handlers/common.py

import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.exceptions import TelegramBadRequest
from app.utils.logger import common_logger

router = Router()


async def delete_message_with_delay(message: Message, delay: int):
    await asyncio.sleep(delay)
    try:
        await message.delete()
        common_logger.info(f"Deleted reminder message {message.message_id} after {delay} seconds")
    except TelegramBadRequest as e:
        common_logger.error(f"Failed to delete reminder message {message.message_id}: {e}")
    except Exception as e:
        common_logger.error(f"Unexpected error when deleting reminder message {message.message_id}: {e}")


@router.message(~Command("start"))
async def delete_irrelevant_message(message: Message):
    user_id = message.from_user.id
    common_logger.info(f"Received message from user {user_id}: {message.text}")
    common_logger.info(f"Message ID: {message.message_id}, Chat ID: {message.chat.id}")

    try:
        await message.delete()
        common_logger.info(f"Successfully deleted message {message.message_id} from user {user_id}")
    except TelegramBadRequest as e:
        common_logger.error(f"TelegramBadRequest when deleting message {message.message_id} from user {user_id}: {e}")
    except Exception as e:
        common_logger.error(f"Unexpected error when deleting message {message.message_id} from user {user_id}: {e}")

    try:
        reminder = await message.answer("Пожалуйста, используйте кнопки меню.")
        common_logger.info(f"Sent reminder (message ID: {reminder.message_id}) to user {user_id}")

        # Запускаем задачу на удаление сообщения-напоминания через 2 секунд
        asyncio.create_task(delete_message_with_delay(reminder, 3))
    except Exception as e:
        common_logger.error(f"Failed to send reminder to user {user_id}: {e}")