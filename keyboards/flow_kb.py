from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from lexicon.lexicon_ru import LEXICON_RU

def continue_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.add(KeyboardButton(text=LEXICON_RU['button_continue']))
    return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

def experience_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.add(
        KeyboardButton(text=LEXICON_RU['button_yes']),
        KeyboardButton(text=LEXICON_RU['button_no'])
    )
    return kb_builder.as_markup(resize_keyboard=True, one_time_keyboard=True)

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

def profile_inline_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['inline_button_direct_requisites'], callback_data="direct_requisites"),
        InlineKeyboardButton(text=LEXICON_RU['inline_button_custom_tag'], callback_data="custom_tag")
    )
    return kb_builder.as_markup()

def main_menu_inline_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['button_check_receipt'], callback_data="check_receipt"),
        InlineKeyboardButton(text=LEXICON_RU['button_curators'], callback_data="curators")
    )
    return kb_builder.as_markup()

def cancel_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['button_cancel'], callback_data="cancel_profit_check")
    )
    return kb_builder.as_markup()

# --- Admin Keyboards ---
def admin_main_menu_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_edit_requisites']),
        KeyboardButton(text=LEXICON_RU['admin_button_manage_stopped_cards']),
        KeyboardButton(text=LEXICON_RU['admin_button_manage_curators'])
    )
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_change_password']),
        KeyboardButton(text=LEXICON_RU['admin_button_edit_personal_link'])
    )
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_back_to_bot_main_menu'])
    )
    return kb_builder.as_markup(resize_keyboard=True)

def admin_choose_card_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['admin_button_card_template'].format(card_order=1), callback_data="edit_card_1"),
        InlineKeyboardButton(text=LEXICON_RU['admin_button_card_template'].format(card_order=2), callback_data="edit_card_2"),
        InlineKeyboardButton(text=LEXICON_RU['admin_button_card_template'].format(card_order=3), callback_data="edit_card_3")
    )
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['admin_button_back_to_admin_main_menu'], callback_data="admin_main_menu")
    )
    return kb_builder.as_markup()

def admin_stopped_cards_menu_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_add_stopped_card']),
        KeyboardButton(text=LEXICON_RU['admin_button_remove_stopped_card'])
    )
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_back_to_admin_main_menu'])
    )
    return kb_builder.as_markup(resize_keyboard=True)

def admin_back_to_admin_menu_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.add(KeyboardButton(text=LEXICON_RU['admin_button_back_to_admin_main_menu']))
    return kb_builder.as_markup(resize_keyboard=True)

def admin_back_to_admin_menu_inline_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['admin_button_back_to_admin_main_menu'], callback_data="admin_main_menu")
    )
    return kb_builder.as_markup()

def curators_selection_keyboard(curators: list[str]) -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    for curator in curators:
        kb_builder.row(InlineKeyboardButton(text=curator, callback_data=f"select_curator_{curator}"))
    return kb_builder.as_markup()

def admin_manage_curators_keyboard() -> ReplyKeyboardMarkup:
    kb_builder = ReplyKeyboardBuilder()
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_add_curator']),
        KeyboardButton(text=LEXICON_RU['admin_button_remove_curator'])
    )
    kb_builder.row(
        KeyboardButton(text=LEXICON_RU['admin_button_back_to_admin_main_menu'])
    )
    return kb_builder.as_markup(resize_keyboard=True)

# --- Work Panel Keyboards ---
def work_panel_directions_keyboard() -> InlineKeyboardMarkup:
    kb_builder = InlineKeyboardBuilder()
    # Первый ряд: ESCORT и Trade
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['button_escort'], url="https://t.me/EscortAgensyAlert_bot"),
        InlineKeyboardButton(text=LEXICON_RU['button_trade_soon'], callback_data="work_trade")
    )
    # Второй ряд: MREO (одна кнопка по центру)
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['button_mreo'], url="https://t.me/+Idshw1uE9KIzOWEy")
    )
    # Третий ряд: NARKO и VAPE
    kb_builder.row(
        InlineKeyboardButton(text=LEXICON_RU['button_mtz_shop'], url="https://t.me/Torion4200_bot"),
        InlineKeyboardButton(text=LEXICON_RU['button_vape'], url="https://t.me/+-dSz7Jaqq_dmNDgy")
    )
    return kb_builder.as_markup()
