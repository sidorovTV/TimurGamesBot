from aiogram import Bot
from aiogram.types import Message
from typing import Dict, List, Tuple

class MessageCleaner:
    def __init__(self):
        self.message_ids: Dict[int, List[Tuple[int, int]]] = {}

    async def add_message_to_delete(self, user_id: int, message: Message):
        if user_id not in self.message_ids:
            self.message_ids[user_id] = []
        self.message_ids[user_id].append((message.chat.id, message.message_id))

    async def delete_previous_messages(self, bot: Bot, user_id: int):
        if user_id in self.message_ids:
            for chat_id, msg_id in self.message_ids[user_id]:
                try:
                    await bot.delete_message(chat_id=chat_id, message_id=msg_id)
                except Exception as e:
                    print(f"Error deleting message {msg_id}: {e}")
            self.message_ids[user_id] = []

    async def add_user_message(self, message: Message):
        user_id = message.from_user.id
        if user_id not in self.message_ids:
            self.message_ids[user_id] = []
        self.message_ids[user_id].append((message.chat.id, message.message_id))

message_cleaner = MessageCleaner()

