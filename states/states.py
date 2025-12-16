from aiogram.fsm.state import StatesGroup, State

class Registration(StatesGroup):
    waiting_for_experience = State()
    waiting_for_time_commitment = State()
    waiting_for_source = State()

class Profile(StatesGroup):
    waiting_for_unique_tag = State()

class Admin(StatesGroup):
    waiting_for_admin_password = State()
    admin_main_menu = State()

    # Change password
    waiting_for_new_password = State()

    # Edit personal requisites link
    waiting_for_personal_requisites_link = State()

    # Edit card requisites
    choosing_card_to_edit = State()
    waiting_for_card_number = State()
    waiting_for_card_name = State()
    waiting_for_bank_name = State()
    waiting_for_min_amount = State()
    waiting_for_max_amount = State()
    waiting_for_percentage = State()

    # Manage stopped cards
    manage_stopped_cards_menu = State()
    waiting_for_stopped_card_to_add = State()
    waiting_for_stopped_card_to_remove = State()
