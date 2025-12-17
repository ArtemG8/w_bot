from aiogram import Bot
from aiogram.types import BotCommand


async def set_main_menu(bot: Bot):
    """Устанавливает главное меню для бота."""
    main_menu_commands = [
        BotCommand(command='/card', description='Прямые реквизиты'),
    ]
    await bot.set_my_commands(main_menu_commands)
