# w_bot/keyboard/set_menu.py

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU

def main_menu_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['button_main_menu']),
        KeyboardButton(text=LEXICON_RU['button_profile'])
    )
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['button_work_panel'])
    )
    return kb_builder.as_markup(resize_keyboard=True)


