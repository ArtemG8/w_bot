import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove, FSInputFile
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import LEXICON_RU
from keyboards.flow_kb import admin_main_menu_keyboard, admin_choose_card_keyboard, admin_stopped_cards_menu_keyboard, main_menu_keyboard, admin_back_to_admin_menu_keyboard, admin_back_to_admin_menu_inline_keyboard, admin_manage_curators_keyboard, admin_manage_staff_keyboard
from states.states import Admin
from database.db import get_admin_password, update_admin_password, get_all_requisites, get_requisite_by_order, update_requisite, get_personal_requisites_link, update_personal_requisites_link, get_stopped_cards, add_stopped_card, remove_stopped_card, get_card_order_by_number, get_profit_check, approve_profit_check, reject_profit_check, update_statistics, get_curators, add_curator, remove_curator, get_user_by_username, get_user, get_staff, add_staff, remove_staff, is_staff, get_staff_by_username, get_user_curator
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
                             Admin.waiting_for_stopped_card_to_add,
                             Admin.waiting_for_stopped_card_to_remove,
                             Admin.manage_curators_menu,
                             Admin.waiting_for_curator_to_add,
                             Admin.waiting_for_curator_to_remove,
                             Admin.manage_staff_menu,
                             Admin.waiting_for_staff_username_to_add,
                             Admin.waiting_for_staff_position_to_add,
                             Admin.waiting_for_staff_username_to_remove,
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
    await message.answer(LEXICON_RU['admin_new_password_request'], reply_markup=admin_back_to_admin_menu_inline_keyboard())
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
    await message.answer(LEXICON_RU['admin_personal_link_request'], reply_markup=admin_back_to_admin_menu_inline_keyboard())
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
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
    card_number = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_card_number=card_number)
    await message.answer(LEXICON_RU['admin_request_card_name'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_card_name)

@router.message(Admin.waiting_for_card_name)
async def process_card_name(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
    card_name = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_card_name=card_name)
    await message.answer(LEXICON_RU['admin_request_bank_name'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_bank_name)

@router.message(Admin.waiting_for_bank_name)
async def process_bank_name(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
    bank_name = message.text
    user_data = await state.get_data()
    card_order = user_data['current_card_order']
    await state.update_data(temp_bank_name=bank_name)
    await message.answer(LEXICON_RU['admin_request_min_amount'].format(card_order=card_order), reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_min_amount)

@router.message(Admin.waiting_for_min_amount)
async def process_min_amount(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
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
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
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
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await _display_admin_main_menu(message, state)
        return
    
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

# Обработчик кнопки "Назад" из меню управления стопнутыми картами
@router.message(F.text == LEXICON_RU['admin_button_back_to_admin_main_menu'], Admin.manage_stopped_cards_menu)
async def back_from_stopped_cards_menu(message: Message, state: FSMContext):
    await _display_admin_main_menu(message, state)

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

# --- Profit Check Approval/Rejection Handlers ---

@router.callback_query(F.data.startswith("approve_profit_"))
async def process_approve_profit_check(callback: CallbackQuery):
    try:
        check_id = int(callback.data.split("_")[-1])
        profit_check = await get_profit_check(check_id)
        
        if not profit_check:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        
        if profit_check['status'] != 'pending':
            await callback.answer("Заявка уже обработана", show_alert=True)
            return
        
        # Одобряем заявку
        approved_check = await approve_profit_check(check_id)
        
        if approved_check:
            # Обновляем статистику
            await update_statistics(approved_check['amount'])
            
            # Отправляем уведомление пользователю
            user_id = approved_check['user_id']
            try:
                await callback.bot.send_message(
                    chat_id=user_id,
                    text=LEXICON_RU['profit_check_approved']
                )
            except Exception as e:
                logger.error(f"Failed to send approval notification to user {user_id}: {e}")
            
            # Отправляем уведомление в чат команды
            try:
                user = await get_user(user_id)
                username = user['username'] if user and user['username'] else "N/A"
                amount = approved_check['amount']
                
                # Проверяем наличие куратора и рассчитываем доли
                curator = await get_user_curator(user_id)
                if curator:
                    # Если есть куратор: воркер получает сумму минус 45%, куратор получает 25%
                    worker_share = int(amount * 0.55)  # 100% - 45% = 55%
                    curator_share = int(amount * 0.25)  # 25% от суммы профита
                    curator_share_line = f"\n┖ Доля куратора: <code>{curator_share} RUB</code>"
                else:
                    # Если нет куратора: воркер получает сумму минус 20%
                    worker_share = int(amount * 0.80)  # 100% - 20% = 80%
                    curator_share_line = ""
                
                team_notification_text = LEXICON_RU['team_notification_new_profit'].format(
                    username=username,
                    amount=amount,
                    worker_share=worker_share,
                    curator_share_line=curator_share_line
                )
                
                await callback.bot.send_photo(
                    chat_id=Config.TEAM_CHAT_ID,
                    photo=FSInputFile("images/main.png"),
                    caption=team_notification_text
                )
            except Exception as e:
                logger.error(f"Failed to send team chat notification about new profit: {e}")
            
            # Обновляем сообщение админа
            await callback.message.edit_caption(
                caption=callback.message.caption + "\n\n✅ Одобрено",
                reply_markup=None
            )
            await callback.answer("Заявка одобрена")
        else:
            await callback.answer("Ошибка при одобрении заявки", show_alert=True)
    except Exception as e:
        logger.error(f"Error approving profit check: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

@router.callback_query(F.data.startswith("reject_profit_"))
async def process_reject_profit_check(callback: CallbackQuery):
    try:
        check_id = int(callback.data.split("_")[-1])
        profit_check = await get_profit_check(check_id)
        
        if not profit_check:
            await callback.answer("Заявка не найдена", show_alert=True)
            return
        
        if profit_check['status'] != 'pending':
            await callback.answer("Заявка уже обработана", show_alert=True)
            return
        
        # Отклоняем заявку
        await reject_profit_check(check_id)
        
        # Отправляем уведомление пользователю
        user_id = profit_check['user_id']
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=LEXICON_RU['profit_check_rejected']
            )
        except Exception as e:
            logger.error(f"Failed to send rejection notification to user {user_id}: {e}")
        
        # Обновляем сообщение админа
        await callback.message.edit_caption(
            caption=callback.message.caption + "\n\n❌ Отклонено",
            reply_markup=None
        )
        await callback.answer("Заявка отклонена")
    except Exception as e:
        logger.error(f"Error rejecting profit check: {e}", exc_info=True)
        await callback.answer("Произошла ошибка", show_alert=True)

# --- Manage Curators ---
@router.message(F.text == LEXICON_RU['admin_button_manage_curators'], Admin.admin_main_menu)
async def show_manage_curators_menu(message: Message, state: FSMContext):
    curators = await get_curators()
    if curators:
        curators_list_str = "\n".join([f"- @{curator['username']}" for curator in curators])
    else:
        curators_list_str = "(нет кураторов)"

    await message.answer(
        LEXICON_RU['admin_curators_list'].format(curators_list=curators_list_str),
        reply_markup=admin_manage_curators_keyboard()
    )
    await state.set_state(Admin.manage_curators_menu)

@router.message(F.text == LEXICON_RU['admin_button_add_curator'], Admin.manage_curators_menu)
async def request_curator_to_add(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_curator_to_add'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_curator_to_add)

@router.message(Admin.waiting_for_curator_to_add)
async def add_new_curator(message: Message, state: FSMContext):
    curator_username = message.text.strip().lstrip('@')
    if curator_username:
        # Получаем user_id куратора по его username
        user = await get_user_by_username(curator_username)
        if user:
            await add_curator(user['user_id'], curator_username)
            await message.answer(LEXICON_RU['admin_curator_added'].format(curator_username=curator_username), reply_markup=admin_back_to_admin_menu_keyboard())
        else:
            await message.answer(f"Пользователь с username @{curator_username} не найден. Убедитесь, что он запустил бота.", reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await show_manage_curators_menu(message, state)

@router.message(F.text == LEXICON_RU['admin_button_remove_curator'], Admin.manage_curators_menu)
async def request_curator_to_remove(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_curator_to_remove'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_curator_to_remove)

@router.message(Admin.waiting_for_curator_to_remove)
async def remove_existing_curator(message: Message, state: FSMContext):
    curator_username = message.text.strip().lstrip('@')
    if curator_username:
        curators = await get_curators()
        if any(curator['username'] == curator_username for curator in curators):
            await remove_curator(curator_username)
            await message.answer(LEXICON_RU['admin_curator_removed'].format(curator_username=curator_username), reply_markup=admin_back_to_admin_menu_keyboard())
        else:
            await message.answer(LEXICON_RU['admin_curator_not_found'].format(curator_username=curator_username), reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await show_manage_curators_menu(message, state)

@router.message(F.text == LEXICON_RU['admin_button_back_to_admin_main_menu'], Admin.manage_curators_menu)
async def back_from_manage_curators_menu(message: Message, state: FSMContext):
    await _display_admin_main_menu(message, state)

# --- Manage Staff ---
@router.message(F.text == LEXICON_RU['admin_button_manage_staff'], Admin.admin_main_menu)
async def show_manage_staff_menu(message: Message, state: FSMContext):
    staff = await get_staff()
    if staff:
        staff_list_str = "\n".join([f"- @{s['username']} ({s['position']})" for s in staff])
    else:
        staff_list_str = "(нет сотрудников)"

    await message.answer(
        LEXICON_RU['admin_staff_list'].format(staff_list=staff_list_str),
        reply_markup=admin_manage_staff_keyboard()
    )
    await state.set_state(Admin.manage_staff_menu)

@router.message(F.text == LEXICON_RU['admin_button_add_staff'], Admin.manage_staff_menu)
async def request_staff_username_to_add(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_staff_username'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_staff_username_to_add)

@router.message(Admin.waiting_for_staff_username_to_add)
async def process_staff_username_to_add(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await show_manage_staff_menu(message, state)
        return
    
    staff_username = message.text.strip().lstrip('@')
    if staff_username:
        # Проверяем, существует ли пользователь
        user = await get_user_by_username(staff_username)
        if user:
            # Проверяем, не является ли уже сотрудником
            if await is_staff(user['user_id']):
                await message.answer(LEXICON_RU['admin_staff_already_staff'].format(username=staff_username), reply_markup=admin_back_to_admin_menu_keyboard())
                await show_manage_staff_menu(message, state)
            else:
                # Сохраняем username и запрашиваем должность
                await state.update_data(temp_staff_username=staff_username)
                await message.answer(LEXICON_RU['admin_request_staff_position'], reply_markup=admin_back_to_admin_menu_keyboard())
                await state.set_state(Admin.waiting_for_staff_position_to_add)
        else:
            await message.answer(LEXICON_RU['admin_staff_not_found'].format(username=staff_username), reply_markup=admin_back_to_admin_menu_keyboard())
            await show_manage_staff_menu(message, state)
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
        await show_manage_staff_menu(message, state)

@router.message(Admin.waiting_for_staff_position_to_add)
async def process_staff_position_to_add(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await show_manage_staff_menu(message, state)
        return
    
    position = message.text.strip()
    if position:
        user_data = await state.get_data()
        staff_username = user_data['temp_staff_username']
        user = await get_user_by_username(staff_username)
        if user:
            await add_staff(user['user_id'], staff_username, position)
            await message.answer(LEXICON_RU['admin_staff_added'].format(username=staff_username, position=position), reply_markup=admin_back_to_admin_menu_keyboard())
        else:
            await message.answer(LEXICON_RU['admin_staff_not_found'].format(username=staff_username), reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await show_manage_staff_menu(message, state)

@router.message(F.text == LEXICON_RU['admin_button_remove_staff'], Admin.manage_staff_menu)
async def request_staff_username_to_remove(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['admin_request_staff_username'], reply_markup=admin_back_to_admin_menu_keyboard())
    await state.set_state(Admin.waiting_for_staff_username_to_remove)

@router.message(Admin.waiting_for_staff_username_to_remove)
async def remove_existing_staff(message: Message, state: FSMContext):
    # Проверка на reply кнопку "Назад в Главное меню админки"
    if message.text == LEXICON_RU['admin_button_back_to_admin_main_menu']:
        await show_manage_staff_menu(message, state)
        return
    
    staff_username = message.text.strip().lstrip('@')
    if staff_username:
        staff_member = await get_staff_by_username(staff_username)
        if staff_member:
            await remove_staff(staff_member['user_id'])
            await message.answer(LEXICON_RU['admin_staff_removed'].format(username=staff_username), reply_markup=admin_back_to_admin_menu_keyboard())
        else:
            await message.answer(LEXICON_RU['admin_staff_not_found'].format(username=staff_username), reply_markup=admin_back_to_admin_menu_keyboard())
    else:
        await message.answer(LEXICON_RU['admin_no_changes'], reply_markup=admin_back_to_admin_menu_keyboard())
    await show_manage_staff_menu(message, state)

@router.message(F.text == LEXICON_RU['admin_button_back_to_admin_main_menu'], Admin.manage_staff_menu)
async def back_from_manage_staff_menu(message: Message, state: FSMContext):
    await _display_admin_main_menu(message, state)