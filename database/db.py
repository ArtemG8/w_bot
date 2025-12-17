from asyncpg import Record
from database.connection import Database
from config.config import Config

# --- User related functions ---

async def add_user(user_id: int, username: str | None, first_name: str | None) -> None:
    query = '''
    INSERT INTO users (user_id, username, first_name)
    VALUES ($1, $2, $3)
    ON CONFLICT (user_id) DO NOTHING;
    '''
    await Database.execute(query, user_id, username, first_name)

async def get_user(user_id: int) -> Record | None:
    query = '''
    SELECT * FROM users WHERE user_id = $1;
    '''
    return await Database.fetchrow(query, user_id)

async def update_user_registration_status(user_id: int, status: bool) -> None:
    query = '''
    UPDATE users SET registration_complete = $1 WHERE user_id = $2;
    '''
    await Database.execute(query, status, user_id)

async def update_user_registration_data(
    user_id: int,
    experience: str,
    time_commitment: str,
    source: str
) -> None:
    query = '''
    UPDATE users
    SET experience = $1, time_commitment = $2, source = $3, registration_complete = TRUE
    WHERE user_id = $4;
    '''
    await Database.execute(query, experience, time_commitment, source, user_id)

async def update_user_unique_tag(user_id: int, unique_tag: str | None) -> None:
    query = '''
    UPDATE users SET unique_tag = $1 WHERE user_id = $2;
    '''
    await Database.execute(query, unique_tag, user_id)


# --- Admin related functions ---

async def get_admin_password() -> str:
    query = '''
    SELECT admin_password FROM admin_settings WHERE id = 1;
    '''
    password = await Database.fetchval(query)
    if not password:
        # Если почему-то нет записи, вставляем дефолтную
        await Database.execute(
            '''INSERT INTO admin_settings (id, admin_password, personal_requisites_link) VALUES (1, $1, NULL) ON CONFLICT (id) DO NOTHING;''',
            Config.DEFAULT_ADMIN_PASSWORD
        )
        return Config.DEFAULT_ADMIN_PASSWORD
    return password

async def update_admin_password(new_password: str) -> None:
    query = '''
    UPDATE admin_settings SET admin_password = $1 WHERE id = 1;
    '''
    await Database.execute(query, new_password)

async def get_personal_requisites_link() -> str | None:
    query = '''
    SELECT personal_requisites_link FROM admin_settings WHERE id = 1;
    '''
    return await Database.fetchval(query)

async def update_personal_requisites_link(link: str | None) -> None:
    query = '''
    UPDATE admin_settings SET personal_requisites_link = $1 WHERE id = 1;
    '''
    await Database.execute(query, link)

# --- Requisites related functions ---

async def get_all_requisites() -> list[Record]:
    query = '''
    SELECT * FROM requisites ORDER BY card_order;
    '''
    return await Database.fetch(query)

async def get_requisite_by_order(card_order: int) -> Record | None:
    query = '''
    SELECT * FROM requisites WHERE card_order = $1;
    '''
    return await Database.fetchrow(query, card_order)

async def get_card_order_by_number(card_number: str) -> int | None:
    query = '''
    SELECT card_order FROM requisites WHERE card_number = $1;
    '''
    return await Database.fetchval(query, card_number)

async def update_requisite(
    card_order: int,
    card_number: str,
    card_name: str,
    bank_name: str,
    min_amount: int,
    max_amount: int,
    percentage: int
) -> None:
    query = '''
    UPDATE requisites
    SET card_number = $2, card_name = $3, bank_name = $4, min_amount = $5, max_amount = $6, percentage = $7
    WHERE card_order = $1;
    '''
    await Database.execute(query, card_order, card_number, card_name, bank_name, min_amount, max_amount, percentage)

# --- Stopped Cards related functions ---

async def get_stopped_cards() -> list[Record]:
    query = '''
    SELECT card_number FROM stopped_cards ORDER BY added_at DESC;
    '''
    return await Database.fetch(query)

async def add_stopped_card(card_number: str) -> None:
    query = '''
    INSERT INTO stopped_cards (card_number)
    VALUES ($1)
    ON CONFLICT (card_number) DO NOTHING;
    '''
    await Database.execute(query, card_number)

async def remove_stopped_card(card_number: str) -> None:
    query = '''
    DELETE FROM stopped_cards WHERE card_number = $1;
    '''
    await Database.execute(query, card_number)

