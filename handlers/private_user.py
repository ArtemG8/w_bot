import datetime

from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext

from lexicon.lexicon_ru import LEXICON_RU
from keyboards.flow_kb import continue_keyboard, experience_keyboard, main_menu_keyboard, profile_inline_keyboard
from states.states import Registration, Profile
from database.db import add_user, get_user, update_user_registration_data, update_user_unique_tag, get_all_requisites, get_personal_requisites_link, get_stopped_cards
from config.config import Config

router = Router()

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
            photo="https://v3b.fal.media/files/b/0a8690dc/QSyhB55qF6iHyZgPpivYl.png",#images/main.png
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

# Заглушки для главного меню и ворк-панели
@router.message(F.text == LEXICON_RU['button_main_menu'])
async def process_main_menu_button(message: Message):
    await message.answer("Вы перешли в Главное меню. (Заглушка)")

@router.message(F.text == LEXICON_RU['button_work_panel'])
async def process_work_panel_button(message: Message):
    await message.answer("Вы перешли в Ворк панель. (Заглушка)")

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

        profile_text = LEXICON_RU['profile_text'].format(
            username=username,
            user_id=user_id,
            unique_tag=unique_tag_display,
            current_date=current_date
        )
        await message.answer(profile_text, reply_markup=profile_inline_keyboard())
    else:
        await message.answer("Произошла ошибка при загрузке вашего профиля. Пожалуйста, попробуйте снова или напишите /start.")

# Заглушка для inline-кнопки "Прямой реквизит"
@router.callback_query(F.data == "direct_requisites")
async def process_direct_requisites_callback(callback: CallbackQuery):
    await callback.answer() # Убираем индикатор загрузки

    requisites = await get_all_requisites()
    personal_link = await get_personal_requisites_link()
    stopped_cards = await get_stopped_cards()

    response_text = LEXICON_RU['direct_requisites_header']

    for req in requisites:
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

    await callback.message.answer(response_text)


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

