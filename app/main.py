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


async def scheduled_reminders(bot: Bot):
    while True:
        await send_session_reminders(bot)
        await asyncio.sleep(3600)  # Проверяем каждый час


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
