from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from database.db import is_banned
from lexicon.lexicon_ru import LEXICON_RU


class BanCheckMiddleware(BaseMiddleware):
    """Middleware для проверки бана пользователя"""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # Получаем user_id из события
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
        
        # Если это не сообщение или callback от пользователя, пропускаем
        if user_id is None:
            return await handler(event, data)
        
        # Проверяем, не забанен ли пользователь
        if await is_banned(user_id):
            # Если забанен, отправляем сообщение и не обрабатываем дальше
            if isinstance(event, Message):
                await event.answer(LEXICON_RU['user_banned_message'])
            elif isinstance(event, CallbackQuery):
                await event.answer(LEXICON_RU['user_banned_message'], show_alert=True)
            return  # Прерываем обработку
        
        # Если не забанен, продолжаем обработку
        return await handler(event, data)

