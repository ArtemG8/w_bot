import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config.config import Config
from database.connection import init_db, Database
from handlers import private_user as user_handlers
from handlers import admin as admin_handlers # Добавлено

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация базы данных
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация роутеров
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router) # Добавлено

    # Запуск обработки обновлений
    logging.info("Starting bot...")
    await dp.start_polling(bot)
    logging.info("Bot stopped.")

    # Закрытие соединения с базой данных при завершении работы
    await Database.close()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped by user.")
