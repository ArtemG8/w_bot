import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config.config import Config
from database.connection import init_db, Database
from handlers import private_user as user_handlers
from handlers import admin as admin_handlers # Добавлено
from keyboards.set_menu import set_main_menu
from middlewares.ban_check import BanCheckMiddleware

# Настройка логирования
logging.basicConfig(level=logging.INFO)

async def main():
    # Инициализация базы данных
    await init_db()

    # Инициализация бота и диспетчера
    bot = Bot(token=Config.BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрация middleware для проверки бана (только для пользовательских обработчиков)
    user_handlers.router.message.middleware(BanCheckMiddleware())
    user_handlers.router.callback_query.middleware(BanCheckMiddleware())

    # Регистрация роутеров
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router) # Добавлено

    # Запуск обработки обновлений
    await set_main_menu(bot)
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
