from aiogram_calendar import SimpleCalendar as BaseSimpleCalendar
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime


class CustomSimpleCalendar(BaseSimpleCalendar):
    async def start_calendar(
            self,
            year: int = datetime.now().year,
            month: int = datetime.now().month
    ) -> InlineKeyboardMarkup:
        markup = await super().start_calendar(year, month)

        # Заменяем кнопку "Cancel" на "Отмена"
        for row in markup.inline_keyboard:
            for button in row:
                if button.text == "Cancel":
                    button.text = "Отмена"
                    button.callback_data = "cancel_session_creation"

        return markup