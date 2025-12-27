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

async def get_user_by_username(username: str) -> Record | None:
    query = '''
    SELECT * FROM users WHERE username = $1;
    '''
    return await Database.fetchrow(query, username)

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

# --- Profit Checks related functions ---

async def create_profit_check(user_id: int, amount: int, photo_file_id: str) -> int:
    query = '''
    INSERT INTO profit_checks (user_id, amount, photo_file_id, status)
    VALUES ($1, $2, $3, 'pending')
    RETURNING id;
    '''
    return await Database.fetchval(query, user_id, amount, photo_file_id)

async def get_profit_check(check_id: int) -> Record | None:
    query = '''
    SELECT * FROM profit_checks WHERE id = $1;
    '''
    return await Database.fetchrow(query, check_id)

async def approve_profit_check(check_id: int) -> Record | None:
    query = '''
    UPDATE profit_checks
    SET status = 'approved', processed_at = CURRENT_TIMESTAMP
    WHERE id = $1
    RETURNING *;
    '''
    return await Database.fetchrow(query, check_id)

async def reject_profit_check(check_id: int) -> None:
    query = '''
    UPDATE profit_checks
    SET status = 'rejected', processed_at = CURRENT_TIMESTAMP
    WHERE id = $1;
    '''
    await Database.execute(query, check_id)

# --- Statistics related functions ---

async def get_statistics() -> Record | None:
    query = '''
    SELECT * FROM statistics WHERE id = 1;
    '''
    return await Database.fetchrow(query)

async def update_statistics(amount: int) -> None:
    query = '''
    UPDATE statistics
    SET total_profits_count = total_profits_count + 1,
        total_profits_amount = total_profits_amount + $1
    WHERE id = 1;
    '''
    await Database.execute(query, amount)

async def get_user_profit_statistics(user_id: int) -> dict:
    query = '''
    SELECT 
        COUNT(*) as total_profits_count,
        COALESCE(SUM(amount), 0) as total_profits_amount
    FROM profit_checks
    WHERE user_id = $1 AND status = 'approved';
    '''
    result = await Database.fetchrow(query, user_id)
    return {
        'total_profits_count': result['total_profits_count'] if result else 0,
        'total_profits_amount': result['total_profits_amount'] if result else 0
    }

# --- Curators related functions ---

async def add_curator(user_id: int, username: str) -> None:
    query = '''
    INSERT INTO curators (user_id, username)
    VALUES ($1, $2)
    ON CONFLICT (user_id) DO UPDATE SET username = $2;
    '''
    await Database.execute(query, user_id, username)

async def remove_curator(username: str) -> None:
    query = '''
    DELETE FROM curators WHERE username = $1;
    '''
    await Database.execute(query, username)

async def get_curators() -> list[Record]:
    query = '''
    SELECT user_id, username FROM curators ORDER BY username;
    '''
    return await Database.fetch(query)

async def is_curator(user_id: int) -> bool:
    query = '''
    SELECT EXISTS(SELECT 1 FROM curators WHERE user_id = $1);
    '''
    return await Database.fetchval(query, user_id)

async def set_user_curator(user_id: int, curator_id: int | None) -> None:
    query = '''
    UPDATE users SET curator_id = $1 WHERE user_id = $2;
    '''
    await Database.execute(query, curator_id, user_id)

async def get_user_curator(user_id: int) -> Record | None:
    query = '''
    SELECT c.username
    FROM users u
    JOIN curators c ON u.curator_id = c.user_id
    WHERE u.user_id = $1;
    '''
    return await Database.fetchrow(query, user_id)

async def get_all_curator_students() -> list[Record]:
    """Получает все связи куратор-ученик"""
    query = '''
    SELECT 
        c.user_id as curator_id,
        c.username as curator_username,
        u.user_id as student_id,
        u.username as student_username,
        u.first_name as student_first_name
    FROM curators c
    LEFT JOIN users u ON u.curator_id = c.user_id
    WHERE u.curator_id IS NOT NULL
    ORDER BY c.username, u.username;
    '''
    return await Database.fetch(query)

async def get_curator_students(curator_id: int) -> list[Record]:
    """Получает всех учеников конкретного куратора"""
    query = '''
    SELECT 
        u.user_id,
        u.username,
        u.first_name
    FROM users u
    WHERE u.curator_id = $1
    ORDER BY u.username;
    '''
    return await Database.fetch(query, curator_id)

async def unlink_user_from_curator(user_id: int) -> None:
    """Отключает пользователя от куратора"""
    query = '''
    UPDATE users SET curator_id = NULL WHERE user_id = $1;
    '''
    await Database.execute(query, user_id)

# --- Staff related functions ---

async def add_staff(user_id: int, username: str, position: str) -> None:
    query = '''
    UPDATE users
    SET role = 'staff', position = $1
    WHERE user_id = $2;
    '''
    await Database.execute(query, position, user_id)

async def remove_staff(user_id: int) -> None:
    query = '''
    UPDATE users
    SET role = NULL, position = NULL, is_on_shift = FALSE
    WHERE user_id = $1;
    '''
    await Database.execute(query, user_id)

async def get_staff() -> list[Record]:
    query = '''
    SELECT user_id, username, first_name, position, is_on_shift
    FROM users
    WHERE role = 'staff'
    ORDER BY username;
    '''
    return await Database.fetch(query)

async def is_staff(user_id: int) -> bool:
    query = '''
    SELECT EXISTS(SELECT 1 FROM users WHERE user_id = $1 AND role = 'staff');
    '''
    return await Database.fetchval(query, user_id)

async def get_staff_by_username(username: str) -> Record | None:
    query = '''
    SELECT * FROM users WHERE username = $1 AND role = 'staff';
    '''
    return await Database.fetchrow(query, username)

async def toggle_shift_status(user_id: int) -> bool:
    """Переключает статус смены и возвращает новый статус"""
    query = '''
    UPDATE users
    SET is_on_shift = NOT is_on_shift
    WHERE user_id = $1
    RETURNING is_on_shift;
    '''
    return await Database.fetchval(query, user_id)

async def get_staff_shift_status(user_id: int) -> bool:
    """Возвращает текущий статус смены сотрудника"""
    query = '''
    SELECT is_on_shift FROM users WHERE user_id = $1;
    '''
    result = await Database.fetchval(query, user_id)
    return result if result is not None else False

# --- Ban related functions ---

async def ban_user(user_id: int) -> None:
    """Блокирует пользователя"""
    query = '''
    UPDATE users SET is_banned = TRUE WHERE user_id = $1;
    '''
    await Database.execute(query, user_id)

async def unban_user(user_id: int) -> None:
    """Разблокирует пользователя"""
    query = '''
    UPDATE users SET is_banned = FALSE WHERE user_id = $1;
    '''
    await Database.execute(query, user_id)

async def is_banned(user_id: int) -> bool:
    """Проверяет, заблокирован ли пользователь"""
    query = '''
    SELECT is_banned FROM users WHERE user_id = $1;
    '''
    result = await Database.fetchval(query, user_id)
    return result if result is not None else False

async def get_banned_users() -> list[Record]:
    """Возвращает список всех заблокированных пользователей"""
    query = '''
    SELECT user_id, username, first_name, created_at
    FROM users
    WHERE is_banned = TRUE
    ORDER BY created_at DESC;
    '''
    return await Database.fetch(query)