import datetime
import logging

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery, FSInputFile # Import FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import LEXICON_RU
from keyboards.flow_kb import continue_keyboard, experience_keyboard, main_menu_keyboard, profile_inline_keyboard, work_panel_directions_keyboard, main_menu_inline_keyboard, cancel_keyboard, curators_selection_keyboard, staff_panel_keyboard
from states.states import Registration, Profile, ProfitCheck
from database.db import add_user, get_user, update_user_registration_data, update_user_unique_tag, get_all_requisites, get_personal_requisites_link, get_stopped_cards, get_statistics, create_profit_check, get_user_profit_statistics, get_curators, set_user_curator, get_user_curator, is_curator, is_staff, toggle_shift_status, get_staff_shift_status
from config.config import Config

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    await add_user(user_id, username, first_name)
    user = await get_user(user_id)

    if user and user['registration_complete']:
        # Пользователь уже зарегистрирован, показываем главное меню
        await message.answer_photo(
            photo=FSInputFile("images/main.png"), # Use FSInputFile for local files
            caption=LEXICON_RU['main_menu_welcome'].format(chat_link="https://t.me/+VOfK0G4A8n45ZGIy"),
            reply_markup=main_menu_keyboard()
        )
    else:
        # Новый пользователь или незавершенная регистрация
        await message.answer(
            LEXICON_RU['welcome_new_user'].format(user_first_name=first_name),
            reply_markup=continue_keyboard()
        )
        await state.set_state(Registration.waiting_for_experience)

# ... (rest of your code)


@router.message(F.text == LEXICON_RU['button_continue'], Registration.waiting_for_experience)
async def process_continue_button(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['experience_question'], reply_markup=experience_keyboard())

@router.message(Registration.waiting_for_experience)
async def process_experience_answer(message: Message, state: FSMContext):
    experience = message.text
    if experience not in [LEXICON_RU['button_yes'], LEXICON_RU['button_no']]:
        await message.answer("Пожалуйста, ответьте 'Да' или 'Нет'.", reply_markup=experience_keyboard())
        return

    await state.update_data(experience=experience)
    await message.answer(LEXICON_RU['time_commitment_question'], reply_markup=ReplyKeyboardRemove())
    await state.set_state(Registration.waiting_for_time_commitment)

@router.message(Registration.waiting_for_time_commitment)
async def process_time_commitment_answer(message: Message, state: FSMContext):
    time_commitment = message.text
    await state.update_data(time_commitment=time_commitment)
    await message.answer(LEXICON_RU['source_question'])
    await state.set_state(Registration.waiting_for_source)

@router.message(Registration.waiting_for_source)
async def process_source_answer(message: Message, state: FSMContext):
    source = message.text
    user_data = await state.get_data()
    experience = user_data.get('experience')
    time_commitment = user_data.get('time_commitment')

    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    # Сохраняем данные в БД
    await update_user_registration_data(user_id, experience, time_commitment, source)

    # Отправляем заявку в админский чат
    admin_message_text = LEXICON_RU['admin_new_application'].format(
        user_id=user_id,
        experience=experience,
        time_commitment=time_commitment,
        source=source,
        username=username if username else "N/A",
        user_first_name=first_name if first_name else "N/A"
    )

    await message.bot.send_message(chat_id=Config.ADMIN_CHAT_ID, text=admin_message_text)

    await message.answer(LEXICON_RU['application_accepted'])
    await state.clear()

# Обработчик кнопки "Главное меню"
@router.message(F.text == LEXICON_RU['button_main_menu'])
async def process_main_menu_button(message: Message):
    stats = await get_statistics()
    total_profits_count = stats['total_profits_count'] if stats else 0
    total_profits_amount = stats['total_profits_amount'] if stats else 0
    
    menu_text = LEXICON_RU['main_menu_info'].format(
        total_profits_count=total_profits_count,
        total_profits_amount=total_profits_amount
    )
    await message.answer(menu_text, reply_markup=main_menu_inline_keyboard())

@router.message(F.text == LEXICON_RU['button_work_panel'])
async def process_work_panel_button(message: Message):
    await message.answer(
        LEXICON_RU['work_panel_choose_direction'],
        reply_markup=work_panel_directions_keyboard()
    )

@router.message(F.text == LEXICON_RU['button_profile'])
async def process_profile_button(message: Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if user:
        username = user['username'] if user['username'] else "N/A"
        # Используем .get() для безопасного доступа к ключу 'unique_tag', который может быть NULL
        unique_tag = user.get('unique_tag')
        unique_tag_display = f"#{unique_tag}" if unique_tag else "(не установлен)" # Убрал # из заглушки
        current_date = datetime.date.today().strftime('%d.%m.%Y')
        
        # Получаем личную статистику профитов пользователя
        user_stats = await get_user_profit_statistics(user_id)
        user_profits_count = user_stats['total_profits_count']
        user_profits_amount = user_stats['total_profits_amount']

        profile_text = LEXICON_RU['profile_text'].format(
            username=username,
            user_id=user_id,
            unique_tag=unique_tag_display,
            current_date=current_date,
            user_profits_count=user_profits_count,
            user_profits_amount=user_profits_amount
        )
        await message.answer(profile_text, reply_markup=profile_inline_keyboard())
    else:
        await message.answer("Произошла ошибка при загрузке вашего профиля. Пожалуйста, попробуйте снова или напишите /start.")

async def _build_direct_requisites_text() -> str:
    requisites = await get_all_requisites()
    personal_link = await get_personal_requisites_link()
    stopped_cards = await get_stopped_cards()

    # Создаем множества для проверки стоп-листа
    # Нормализуем номера: убираем пробелы и приводим к строке
    stopped_card_numbers = {str(card['card_number']).strip().replace(' ', '') for card in stopped_cards} if stopped_cards else set()
    
    # Проверяем, есть ли в стоп-листе значения, которые могут быть card_order (числа 1, 2, 3)
    stopped_card_orders = set()
    for stopped_num in stopped_card_numbers:
        try:
            # Если значение можно преобразовать в число, это может быть card_order
            order = int(stopped_num)
            if 1 <= order <= 3:  # Валидные значения card_order
                stopped_card_orders.add(order)
        except ValueError:
            pass  # Не число, значит это номер карты

    response_text = LEXICON_RU['direct_requisites_header']

    for req in requisites:
        # Нормализуем номер карты из реквизитов для сравнения
        req_card_number_normalized = str(req['card_number']).strip().replace(' ', '') if req['card_number'] else ''
        
        # Проверяем, находится ли карта в стоп-листе
        # 1. Проверка по card_order (если в стоп-листе число 1, 2, 3)
        is_stopped_by_order = req['card_order'] in stopped_card_orders
        
        # 2. Проверка по номеру карты (точное совпадение)
        is_stopped_by_number = req_card_number_normalized in stopped_card_numbers
        
        # 3. Проверка частичного совпадения (если номер из стоп-листа содержится в номере карты или наоборот)
        is_stopped_by_partial = any(
            stopped_num in req_card_number_normalized or req_card_number_normalized in stopped_num 
            for stopped_num in stopped_card_numbers 
            if stopped_num and req_card_number_normalized and len(stopped_num) > 1 and len(req_card_number_normalized) > 1
        )
        
        is_stopped = is_stopped_by_order or is_stopped_by_number or is_stopped_by_partial
        
        # Если карта в стоп-листе, заменяем данные на 0 или "-"
        if is_stopped:
            response_text += LEXICON_RU['card_template'].format(
                card_order=req['card_order'],
                min_amount=0,
                max_amount=0,
                card_number="-",
                card_name="-",
                bank_name="-",
                percentage=0
            )
        else:
            response_text += LEXICON_RU['card_template'].format(
                card_order=req['card_order'],
                min_amount=req['min_amount'],
                max_amount=req['max_amount'],
                card_number=req['card_number'],
                card_name=req['card_name'],
                bank_name=req['bank_name'],
                percentage=req['percentage']
            )

    if personal_link:
        response_text += LEXICON_RU['personal_requisites_contact'].format(link=personal_link)

    if stopped_cards:
        stopped_cards_list_str = ", ".join([card['card_number'] for card in stopped_cards])
        response_text += LEXICON_RU['stopped_cards_display'].format(stopped_cards_list_str=stopped_cards_list_str)

    return response_text


# Заглушка для inline-кнопки "Прямой реквизит"
@router.callback_query(F.data == "direct_requisites")
async def process_direct_requisites_callback(callback: CallbackQuery):
    await callback.answer() # Убираем индикатор загрузки
    response_text = await _build_direct_requisites_text()
    await callback.message.answer(response_text)


# Команда /card — показать прямые реквизиты
@router.message(Command("card"))
async def process_direct_requisites_command(message: Message):
    response_text = await _build_direct_requisites_text()
    await message.answer(response_text)


# Обработчик для inline-кнопки "Кастомный Тег"
@router.callback_query(F.data == "custom_tag")
async def process_custom_tag_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None) # Убираем inline клавиатуру
    await callback.message.answer(LEXICON_RU['request_unique_tag'])
    await state.set_state(Profile.waiting_for_unique_tag)
    await callback.answer()

# Обработчик для получения уникального тега от пользователя
@router.message(Profile.waiting_for_unique_tag)
async def process_new_unique_tag(message: Message, state: FSMContext):
    new_tag = message.text
    user_id = message.from_user.id

    await update_user_unique_tag(user_id, new_tag)
    await message.answer(LEXICON_RU['unique_tag_saved'])
    await state.clear()
    await process_profile_button(message)

# Обработчик для кнопки Trade (заглушка)
@router.callback_query(F.data == "work_trade")
async def process_work_trade_callback(callback: CallbackQuery):
    await callback.answer()  # Убираем индикатор загрузки

@router.callback_query(F.data == "curators")
async def process_curators_callback(callback: CallbackQuery):
    await callback.answer() # Убираем индикатор загрузки
    curators = await get_curators()
    if curators:
        curator_usernames = [curator['username'] for curator in curators]
        await callback.message.answer(LEXICON_RU['curator_selection_message'], reply_markup=curators_selection_keyboard(curator_usernames))
    else:
        await callback.message.answer("На данный момент кураторы отсутствуют.")

@router.callback_query(F.data.startswith("select_curator_"))
async def process_select_curator_callback(callback: CallbackQuery):
    await callback.answer() # Убираем индикатор загрузки
    
    # Извлекаем username из callback_data
    curator_username = callback.data.replace("select_curator_", "", 1)
    logger.info(f"Processing curator selection: username={curator_username}, callback_data={callback.data}")
    
    curators = await get_curators()
    logger.info(f"Available curators: {[c['username'] for c in curators]}")
    
    curator_id = None
    for curator in curators:
        # Сравниваем без учета регистра и удаляем @ если есть
        curator_db_username = str(curator['username']).lower().lstrip('@')
        curator_callback_username = curator_username.lower().lstrip('@')
        if curator_db_username == curator_callback_username:
            curator_id = curator['user_id']
            logger.info(f"Found curator: user_id={curator_id}, username={curator['username']}")
            break

    if curator_id:
        await set_user_curator(callback.from_user.id, curator_id)
        await callback.message.edit_reply_markup(reply_markup=None) # Убираем inline клавиатуру
        await callback.message.answer(LEXICON_RU['curator_info_message'].format(curator_username=curator_username))
        
        # Отправляем уведомление куратору
        student_username = callback.from_user.username or "N/A"
        student_first_name = callback.from_user.first_name or "N/A"
        student_id = callback.from_user.id
        
        logger.info(f"Sending notification to curator {curator_id} (@{curator_username}) about new student {student_id} (@{student_username})")
        
        try:
            notification_text = LEXICON_RU['curator_notification_new_student'].format(
                student_username=student_username,
                student_first_name=student_first_name,
                student_id=student_id
            )
            await callback.bot.send_message(
                chat_id=curator_id,
                text=notification_text
            )
            logger.info(f"Successfully sent notification to curator {curator_id}")
        except Exception as e:
            # Логируем ошибку, но не прерываем выполнение
            logger.error(f"Failed to send notification to curator {curator_id} (@{curator_username}): {e}", exc_info=True)
    else:
        logger.warning(f"Curator with username {curator_username} not found in database. Available curators: {[c['username'] for c in curators]}")
        await callback.message.answer("Произошла ошибка при выборе куратора. Пожалуйста, попробуйте снова.")

# --- Profit Check Handlers ---

# Обработчик inline кнопки "Проверка чека"
@router.callback_query(F.data == "check_receipt")
async def process_check_receipt_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(LEXICON_RU['profit_check_request_amount'])
    await state.set_state(ProfitCheck.waiting_for_amount)
    await callback.answer()

# Обработчик отмены проверки чека
@router.callback_query(F.data == "cancel_profit_check")
async def process_cancel_profit_check_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(LEXICON_RU['profit_check_cancelled'])
    await state.clear()
    # Возвращаем в главное меню
    stats = await get_statistics()
    total_profits_count = stats['total_profits_count'] if stats else 0
    total_profits_amount = stats['total_profits_amount'] if stats else 0
    
    menu_text = LEXICON_RU['main_menu_info'].format(
        total_profits_count=total_profits_count,
        total_profits_amount=total_profits_amount
    )
    await callback.message.answer(menu_text, reply_markup=main_menu_inline_keyboard())
    await callback.answer()

# Обработчик отмены через текст
@router.message(ProfitCheck.waiting_for_photo, F.text == LEXICON_RU['button_cancel'])
async def process_cancel_profit_check_text(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['profit_check_cancelled'])
    await state.clear()
    # Возвращаем в главное меню
    stats = await get_statistics()
    total_profits_count = stats['total_profits_count'] if stats else 0
    total_profits_amount = stats['total_profits_amount'] if stats else 0
    
    menu_text = LEXICON_RU['main_menu_info'].format(
        total_profits_count=total_profits_count,
        total_profits_amount=total_profits_amount
    )
    await message.answer(menu_text, reply_markup=main_menu_inline_keyboard())

# Обработчик ввода суммы платежа
@router.message(ProfitCheck.waiting_for_amount)
async def process_profit_check_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text)
        if amount == 0:
            # Возврат в главное меню
            await state.clear()
            stats = await get_statistics()
            total_profits_count = stats['total_profits_count'] if stats else 0
            total_profits_amount = stats['total_profits_amount'] if stats else 0
            
            menu_text = LEXICON_RU['main_menu_info'].format(
                total_profits_count=total_profits_count,
                total_profits_amount=total_profits_amount
            )
            await message.answer(menu_text, reply_markup=main_menu_inline_keyboard())
            return
        elif amount > 0:
            await state.update_data(amount=amount)
            await message.answer(LEXICON_RU['profit_check_request_photo'], reply_markup=cancel_keyboard())
            await state.set_state(ProfitCheck.waiting_for_photo)
        else:
            await message.answer(LEXICON_RU['profit_check_invalid_amount'])
    except ValueError:
        await message.answer(LEXICON_RU['profit_check_invalid_amount'])

# Обработчик загрузки фото чека
@router.message(ProfitCheck.waiting_for_photo, F.photo)
async def process_profit_check_photo(message: Message, state: FSMContext):
    photo = message.photo[-1]  # Берем фото наибольшего размера
    photo_file_id = photo.file_id
    
    user_data = await state.get_data()
    amount = user_data.get('amount')
    
    if not amount:
        await message.answer("Произошла ошибка. Пожалуйста, начните заново.")
        await state.clear()
        return
    
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    first_name = message.from_user.first_name or "N/A"
    
    # Сохраняем заявку в БД
    check_id = await create_profit_check(user_id, amount, photo_file_id)
    
    # Отправляем заявку админам
    admin_message_text = LEXICON_RU['admin_profit_check_notification'].format(
        username=username,
        user_id=user_id,
        user_first_name=first_name,
        amount=amount,
        check_id=check_id
    )
    
    # Создаем клавиатуру с кнопками одобрения/отклонения
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    
    admin_kb_builder = InlineKeyboardBuilder()
    admin_kb_builder.row(
        InlineKeyboardButton(
            text=LEXICON_RU['admin_button_approve'],
            callback_data=f"approve_profit_{check_id}"
        ),
        InlineKeyboardButton(
            text=LEXICON_RU['admin_button_reject'],
            callback_data=f"reject_profit_{check_id}"
        )
    )
    
    # Отправляем сообщение админам с фото
    await message.bot.send_photo(
        chat_id=Config.ADMIN_CHAT_ID,
        photo=photo_file_id,
        caption=admin_message_text,
        reply_markup=admin_kb_builder.as_markup()
    )
    
    await message.answer(LEXICON_RU['profit_check_submitted'])
    await state.clear()

# Обработчик, если пользователь отправил не фото
@router.message(ProfitCheck.waiting_for_photo)
async def process_profit_check_not_photo(message: Message, state: FSMContext):
    await message.answer(LEXICON_RU['profit_check_need_photo'], reply_markup=cancel_keyboard())

# --- Staff Panel Handlers ---

@router.message(Command("staff"))
async def process_staff_command(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    # Проверяем, является ли пользователь сотрудником
    if not await is_staff(user_id):
        await message.answer(LEXICON_RU['staff_not_staff'])
        return
    
    # Получаем текущий статус смены
    is_on_shift = await get_staff_shift_status(user_id)
    
    # Получаем информацию о пользователе для получения должности
    user = await get_user(user_id)
    position = user.get('position', 'Сотрудник') if user else 'Сотрудник'
    
    await message.answer(
        LEXICON_RU['staff_welcome'],
        reply_markup=staff_panel_keyboard(is_on_shift)
    )

@router.message(F.text == LEXICON_RU['staff_button_start_shift'])
async def process_start_shift(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    # Проверяем, является ли пользователь сотрудником
    if not await is_staff(user_id):
        await message.answer(LEXICON_RU['staff_not_staff'])
        return
    
    # Переключаем статус смены
    new_status = await toggle_shift_status(user_id)
    
    if new_status:  # Смена начата
        # Получаем информацию о пользователе для получения должности
        user = await get_user(user_id)
        position = user.get('position', 'Сотрудник') if user else 'Сотрудник'
        
        await message.answer(LEXICON_RU['staff_shift_started'], reply_markup=staff_panel_keyboard(True))
        
        # Отправляем уведомление в чат команды
        try:
            notification_text = LEXICON_RU['staff_team_notification_start'].format(
                username=username,
                position=position
            )
            await message.bot.send_message(
                chat_id=Config.TEAM_CHAT_ID,
                text=notification_text
            )
        except Exception as e:
            logger.error(f"Failed to send team chat notification about shift start: {e}")

@router.message(F.text == LEXICON_RU['staff_button_end_shift'])
async def process_end_shift(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "N/A"
    
    # Проверяем, является ли пользователь сотрудником
    if not await is_staff(user_id):
        await message.answer(LEXICON_RU['staff_not_staff'])
        return
    
    # Переключаем статус смены
    new_status = await toggle_shift_status(user_id)
    
    if not new_status:  # Смена закончена
        # Получаем информацию о пользователе для получения должности
        user = await get_user(user_id)
        position = user.get('position', 'Сотрудник') if user else 'Сотрудник'
        
        await message.answer(LEXICON_RU['staff_shift_ended'], reply_markup=staff_panel_keyboard(False))
        
        # Отправляем уведомление в чат команды
        try:
            notification_text = LEXICON_RU['staff_team_notification_end'].format(
                username=username,
                position=position
            )
            await message.bot.send_message(
                chat_id=Config.TEAM_CHAT_ID,
                text=notification_text
            )
        except Exception as e:
            logger.error(f"Failed to send team chat notification about shift end: {e}")

@router.message(F.text == LEXICON_RU['staff_button_exit'])
async def process_exit_staff_panel(message: Message):
    user_id = message.from_user.id
    
    # Проверяем, является ли пользователь сотрудником
    if not await is_staff(user_id):
        await message.answer(LEXICON_RU['staff_not_staff'])
        return
    
    # Возвращаем в главное меню
    stats = await get_statistics()
    total_profits_count = stats['total_profits_count'] if stats else 0
    total_profits_amount = stats['total_profits_amount'] if stats else 0
    
    menu_text = LEXICON_RU['main_menu_info'].format(
        total_profits_count=total_profits_count,
        total_profits_amount=total_profits_amount
    )
    await message.answer(menu_text, reply_markup=main_menu_keyboard())

