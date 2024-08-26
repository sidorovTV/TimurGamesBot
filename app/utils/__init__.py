from . import validators
from . import message_cleaner

from functools import wraps
from aiogram.types import Message, CallbackQuery
from app.services.database import is_user_blocked
from app.utils.message_cleaner import message_cleaner

def check_user_not_blocked(func):
    @wraps(func)
    async def wrapper(message_or_callback, *args, **kwargs):
        user_id = message_or_callback.from_user.id
        if await is_user_blocked(user_id):
            if isinstance(message_or_callback, Message):
                await message_or_callback.answer("Вы заблокированы и не можете использовать бота.")
            elif isinstance(message_or_callback, CallbackQuery):
                await message_or_callback.answer("Вы заблокированы и не можете использовать бота.", show_alert=True)
            return
        return await func(message_or_callback, *args, **kwargs)

    return wrapper
