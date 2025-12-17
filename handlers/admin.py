import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import LEXICON_RU
from keyboards.flow_kb import admin_main_menu_keyboard, admin_choose_card_keyboard, admin_stopped_cards_menu_keyboard, main_menu_keyboard, admin_back_to_admin_menu_keyboard
from states.states import Admin
from database.db import get_admin_password, update_admin_password, get_all_requisites, get_requisite_by_order, update_requisite, get_personal_requisites_link, update_personal_requisites_link, get_stopped_cards, add_stopped_card, remove_stopped_card, get_card_order_by_number
from config.config import Config

router = Router()
logger = logging.getLogger(__name__)

# --- Helper to display Admin Main Menu ---
async def _display_admin_main_menu(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_main_menu_text'], reply_markup=admin_main_menu_keyboard())
    await state.set_state(Admin.admin_main_menu)

# --- Handlers for "Back to Admin Main Menu" (GENERIC) ---
@router.message(F.text == LEXICON_RU['admin_button_back_to_admin_main_menu'],
                F.state.in_([Admin.waiting_for_admin_password,
                             Admin.waiting_for_new_password,
                             Admin.waiting_for_personal_requisites_link,
                             Admin.waiting_for_card_number,
                             Admin.waiting_for_card_name,
                             Admin.waiting_for_bank_name,
                             Admin.waiting_for_min_amount,
                             Admin.waiting_for_max_amount,
                             Admin.waiting_for_percentage,
                             Admin.manage_stopped_cards_menu,
                             Admin.waiting_for_stopped_card_to_add,
                             Admin.waiting_for_stopped_card_to_remove,
                             Admin.admin_main_menu
                            ]))
async def admin_back_to_admin_main_menu_reply_handler(message: Message, state: FSMContext):
    await _display_admin_main_menu(message, state)


@router.callback_query(F.data == "admin_main_menu")
async def admin_back_to_admin_main_menu_callback_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await _display_admin_main_menu(callback.message, state)
    await callback.answer()


# --- Admin Panel Entry Point ---
@router.message(Command("admin"))
async def process_admin_command(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_password_request'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_admin_password)

@router.message(Admin.waiting_for_admin_password)
async def process_admin_password_entry(message: Message, state: FSMContext):
    entered_password = message.text
    stored_password = await get_admin_password()

    if entered_password == stored_password:
        await _display_admin_main_menu(message, state)
    else:
        await message.answer(LEXICON_RU['admin_incorrect_password'], reply_markup=admin_back_to_admin_menu_keyboard())


# --- Handler for "Exit Admin Panel" ---
@router.message(F.text == LEXICON_RU['admin_button_back_to_bot_main_menu'], Admin.admin_main_menu)
async def admin_back_to_bot_main_menu_handler(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['main_menu_welcome'].format(chat_link="https://t.me/+VOfK0G4A8n45ZGIy"), reply_markup=main_menu_keyboard())
    await state.clear()


# --- Change Admin Password ---
@router.message(F.text == LEXICON_RU['admin_button_change_password'], Admin.admin_main_menu)
async def request_new_admin_password(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_new_password_request'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_new_password)

@router.message(Admin.waiting_for_new_password)
async def set_new_admin_password(message: Message, state: FSMContext):
    new_password = message.text
    if new_password:
        await update_admin_password(new_password)
        await message.answer(LEXICON_RU['admin_password_changed'], reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await _display_admin_main_menu(message, state)

# --- Edit Personal Requisites Link ---
@router.message(F.text == LEXICON_RU['admin_button_edit_personal_link'], Admin.admin_main_menu)
async def request_personal_requisites_link(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_personal_link_request'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_personal_requisites_link)

@router.message(Admin.waiting_for_personal_requisites_link)
async def set_personal_requisites_link(message: Message, state: FSMContext):
    new_link = message.text
    if new_link == '-':
        await update_personal_requisites_link(None)
        await message.answer(LEXICON_RU['admin_personal_link_removed'], reply_markup=admin_back_to_admin_menu_keyboard())
    elif new_link:
        await update_personal_requisites_link(new_link)
        await message.answer(LEXICON_RU['admin_personal_link_saved'], reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await _display_admin_main_menu(message, state)


# --- Edit Requisites ---
@router.message(F.text == LEXICON_RU['admin_button_edit_requisites'], Admin.admin_main_menu)
async def choose_card_to_edit(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_choose_card_to_edit'], reply_markup=admin_choose_card_keyboard())
    await state.set_state(Admin.choosing_card_to_edit)

@router.callback_query(F.data.startswith("edit_card_"), Admin.choosing_card_to_edit)
async def start_editing_card(callback: CallbackQuery, state: FSMContext):
    card_order = int(callback.data.split('_')[2])
    await state.update_data(current_card_order=card_order)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(LEXICON_RU['admin_request_card_number'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_card_number)
    await callback.answer()

@router.message(Admin.waiting_for_card_number)
async def process_card_number(message: Message, state: FSMContext):
    card_number = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_card_number=card_number)
    await message.answer(LEXICON_RU['admin_request_card_name'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_card_name)

@router.message(Admin.waiting_for_card_name)
async def process_card_name(message: Message, state: FSMContext):
    card_name = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_card_name=card_name)
    await message.answer(LEXICON_RU['admin_request_bank_name'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_bank_name)

@router.message(Admin.waiting_for_bank_name)
async def process_bank_name(message: Message, state: FSMContext):
    bank_name = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_bank_name=bank_name)
    await message.answer(LEXICON_RU['admin_request_min_amount'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_min_amount)

@router.message(Admin.waiting_for_min_amount)
async def process_min_amount(message: Message, state: FSMContext):
    try:
        min_amount = int(message.text)
        user_data = await state.get_data()
        card_order = user_data['current_card_order']
        await state.update_data(temp_min_amount=min_amount)
        await message.answer(LEXICON_RU['admin_request_max_amount'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
        await state.set_state(Admin.waiting_for_max_amount)
    except ValueError:
        await message.answer(LEXICON_RU['admin_invalid_amount'], reply_markup=admin_back_to_admin_menu_keyboard())

@router.message(Admin.waiting_for_max_amount)
async def process_max_amount(message: Message, state: FSMContext):
    try:
        max_amount = int(message.text)
        user_data = await state.get_data()
        card_order = user_data['current_card_order']
        await state.update_data(temp_max_amount=max_amount)
        await message.answer(LEXICON_RU['admin_request_percentage'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
        await state.set_state(Admin.waiting_for_percentage)
    except ValueError:
        await message.answer(LEXICON_RU['admin_invalid_amount'], reply_markup=admin_back_to_admin_menu_keyboard())

@router.message(Admin.waiting_for_percentage)
async def process_percentage(message: Message, state: FSMContext):
    try:
        percentage = int(message.text)
        if not (0 <= percentage <= 100):
            raise ValueError
        user_data = await state.get_data()
        card_order = user_data['current_card_order']
        max_amount = user_data['temp_max_amount']

        old_requisite = await get_requisite_by_order(card_order)

        await update_requisite(
            card_order=card_order,
            card_number=user_data['temp_card_number'],
            card_name=user_data['temp_card_name'],
            bank_name=user_data['temp_bank_name'],
            min_amount=user_data['temp_min_amount'],
            max_amount=max_amount,
            percentage=percentage
        )
        await message.answer(LEXICON_RU['admin_requisite_updated_success'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())

        # Отправка уведомления в чат команды, если банк изменился или номер
        if old_requisite and (old_requisite['bank_name'] != user_data['temp_bank_name'] or old_requisite['card_number'] != user_data['temp_card_number']):
            try:
                # Используем card_order вместо номера карты для уведомления о смене реквизитов
                await message.bot.send_message(
                    chat_id=Config.TEAM_CHAT_ID,
                    text=LEXICON_RU['team_notification_requisite_changed'].format(
                        card_order=card_order,
                        requisites_info_footer=LEXICON_RU['requisites_info_footer']
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send team chat notification on requisite change: {e}")

    except ValueError:
        await message.answer(LEXICON_RU['admin_invalid_percentage'], reply_markup=admin_back_to_admin_menu_keyboard())
    except Exception as e:
        logger.error(f"Error updating requisite: {e}")
        await message.answer("Произошла ошибка при обновлении реквизитов.", reply_markup=admin_back_to_admin_menu_keyboard())
    await _display_admin_main_menu(message, state)


# --- Manage Stopped Cards ---
@router.message(F.text == LEXICON_RU['admin_button_manage_stopped_cards'], Admin.admin_main_menu)
async def show_stopped_cards_menu(message: Message, state: FSMContext):
    stopped_cards = await get_stopped_cards()
    if stopped_cards:
        stopped_cards_list_str = "\n".join([f"- {card['card_number']}" for card in stopped_cards])
    else:
        stopped_cards_list_str = "(нет стопнутых карт)"

    await message.answer(
        LEXICON_RU['admin_stopped_cards_menu'].format(stopped_cards_list=stopped_cards_list_str),
        reply_markup=admin_stopped_cards_menu_keyboard()
    )
    await state.set_state(Admin.manage_stopped_cards_menu)

@router.message(F.text == LEXICON_RU['admin_button_add_stopped_card'], Admin.manage_stopped_cards_menu)
async def request_stopped_card_to_add(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_stopped_card_to_add'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_stopped_card_to_add)

@router.message(Admin.waiting_for_stopped_card_to_add)
async def add_new_stopped_card(message: Message, state: FSMContext):
    card_number = message.text
    if card_number:
        await add_stopped_card(card_number)
        await message.answer(LEXICON_RU['admin_stopped_card_added'].format(card_number=card_number), reply_markup=admin_back_to_admin_menu_keyboard())
        # Отправка уведомления в чат команды при добавлении в стоп-лист (с новой строкой)
        try:
            await message.bot.send_message(
                chat_id=Config.TEAM_CHAT_ID,
                text=LEXICON_RU['team_notification_card_stopped'].format( # <<<<<< БЕЗ ИЗМЕНЕНИЙ, ТАК И ДОЛЖНО БЫТЬ
                    card_number=card_number,
                    requisites_info_footer=LEXICON_RU['requisites_info_footer']
                )
            )
        except Exception as e:
            logger.error(f"Failed to send team chat notification on adding stopped card: {e}")
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await _display_admin_main_menu(message, state)

@router.message(F.text == LEXICON_RU['admin_button_remove_stopped_card'], Admin.manage_stopped_cards_menu)
async def request_stopped_card_to_remove(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_stopped_card_to_remove'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_stopped_card_to_remove)

@router.message(Admin.waiting_for_stopped_card_to_remove)
async def remove_existing_stopped_card(message: Message, state: FSMContext):
    card_number = message.text
    if card_number:
        stopped_cards = await get_stopped_cards()
        if any(card['card_number'] == card_number for card in stopped_cards):
            # Получаем card_order по номеру карты для уведомления
            card_order = await get_card_order_by_number(card_number)
            await remove_stopped_card(card_number)
            await message.answer(LEXICON_RU['admin_stopped_card_removed'].format(card_number=card_number), reply_markup=admin_back_to_admin_menu_keyboard())
            
            # Отправка уведомления в чат команды о выводе карты из стоп-листа
            try:
                if card_order:
                    # Используем card_order если найден
                    notification_text = LEXICON_RU['team_notification_card_removed_from_stop'].format(
                        card_order=card_order,
                        requisites_info_footer=LEXICON_RU['requisites_info_footer']
                    )
                else:
                    # Если card_order не найден, используем номер карты
                    logger.warning(f"Card order not found for card_number: {card_number}, using card_number in notification")
                    notification_text = LEXICON_RU['team_notification_card_removed_from_stop_with_number'].format(
                        card_number=card_number,
                        requisites_info_footer=LEXICON_RU['requisites_info_footer']
                    )
                
                await message.bot.send_message(
                    chat_id=Config.TEAM_CHAT_ID,
                    text=notification_text
                )
                logger.info(f"Notification sent to team chat about card {card_order or card_number} removed from stop list")
            except Exception as e:
                logger.error(f"Failed to send team chat notification on removing stopped card: {e}", exc_info=True)
        else:
            await message.answer(LEXICON_RU['admin_stopped_card_not_found'].format(card_number=card_number), reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await _display_admin_main_menu(message, state)

