import asyncio
import logging
from aiogram import Bot, Dispatcher
from config_reader import config
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from services.database import init_db
from handlers import register_handlers


async def main():
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=config.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # Регистрация обработчиков
    register_handlers(dp)

    # Способ для пропуска старых апдейтов
    await bot.delete_webhook(drop_pending_updates=True)

    # Обработка pooling
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Инициализация базы данных
    init_db()

    asyncio.run(main())
