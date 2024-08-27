import asyncio
import logging
from aiogram import Bot, Dispatcher
from config_reader import config
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from services.database import init_db
from handlers import register_handlers
from callbacks import register_callback
from services.notifications import send_session_reminders
from app.utils.logger import main_logger
import os
import time
from datetime import datetime
import pytz

# Установка часового пояса
os.environ['TZ'] = 'Europe/Moscow'
time.tzset()

# Проверка текущего времени
moscow_tz = pytz.timezone('Europe/Moscow')
current_time = datetime.now(moscow_tz)
print(f"Current time: {current_time}")

async def scheduled_reminders(bot: Bot):
    while True:
        await send_session_reminders(bot)
        await asyncio.sleep(600)  # Проверяем каждые 10 минут


async def main():
    main_logger.info("Starting the bot")
    logging.basicConfig(level=logging.INFO)

    await init_db()

    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Регистрация обработчиков
    register_handlers(dp)
    register_callback(dp)

    # Установка разрешенных обновлений
    allowed_updates = ["message", "callback_query"]

    asyncio.create_task(scheduled_reminders(bot))

    # Способ для пропуска старых апдейтов
    await bot.delete_webhook(drop_pending_updates=True)

    try:
        # Обработка pooling
        main_logger.info("Starting polling")
        await dp.start_polling(bot, allowed_updates=allowed_updates)
    except Exception as e:
        main_logger.error(f"An error occurred: {e}", exc_info=True)
    finally:
        main_logger.info("Bot stopped")


if __name__ == '__main__':
    # Инициализация базы данных

    asyncio.run(main())
