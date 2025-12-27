import asyncpg
from asyncpg import Connection
from aiogram import Bot

from config.config import Config

class Database:
    _pool: asyncpg.Pool = None

    @classmethod
    async def connect(cls):
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                dsn=Config.DATABASE_URL
            )
        return cls._pool

    @classmethod
    async def close(cls):
        if cls._pool:
            await cls._pool.close()
            cls._pool = None

    @classmethod
    async def execute(cls, query: str, *args):
        async with cls._pool.acquire() as connection:
            connection: Connection
            await connection.execute(query, *args)

    @classmethod
    async def fetchrow(cls, query: str, *args):
        async with cls._pool.acquire() as connection:
            connection: Connection
            return await connection.fetchrow(query, *args)

    @classmethod
    async def fetchval(cls, query: str, *args):
        async with cls._pool.acquire() as connection:
            connection: Connection
            return await connection.fetchval(query, *args)

    @classmethod
    async def fetch(cls, query: str, *args):
        async with cls._pool.acquire() as connection:
            connection: Connection
            return await connection.fetch(query, *args)

async def init_db():
    await Database.connect()
    create_users_table_query = '''
    CREATE TABLE IF NOT EXISTS users (
        user_id BIGINT PRIMARY KEY,
        username VARCHAR(255),
        first_name VARCHAR(255),
        registration_complete BOOLEAN DEFAULT FALSE,
        experience VARCHAR(10) DEFAULT NULL,
        time_commitment VARCHAR(255) DEFAULT NULL,
        source VARCHAR(255) DEFAULT NULL,
        unique_tag VARCHAR(255) DEFAULT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    await Database.execute(create_users_table_query)

    add_unique_tag_column_query = '''
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'unique_tag') THEN
            ALTER TABLE users ADD COLUMN unique_tag VARCHAR(255) DEFAULT NULL;
        END IF;
    END
    $$;
    '''
    await Database.execute(add_unique_tag_column_query)

    # Новые таблицы для админки и реквизитов
    create_admin_settings_table_query = '''
    CREATE TABLE IF NOT EXISTS admin_settings (
        id SERIAL PRIMARY KEY,
        admin_password VARCHAR(255) NOT NULL,
        personal_requisites_link TEXT
    );
    '''
    await Database.execute(create_admin_settings_table_query)

    # Вставляем пароль по умолчанию, если таблица пуста
    insert_default_admin_settings_query = f'''
    INSERT INTO admin_settings (admin_password, personal_requisites_link)
    SELECT '{Config.DEFAULT_ADMIN_PASSWORD}', NULL
    WHERE NOT EXISTS (SELECT 1 FROM admin_settings);
    '''
    await Database.execute(insert_default_admin_settings_query)

    create_requisites_table_query = '''
    CREATE TABLE IF NOT EXISTS requisites (
        id SERIAL PRIMARY KEY,
        card_order INTEGER UNIQUE NOT NULL,
        card_number VARCHAR(255),
        card_name VARCHAR(255),
        bank_name VARCHAR(255),
        min_amount INTEGER DEFAULT 0,
        max_amount INTEGER DEFAULT 0,
        percentage INTEGER DEFAULT 75
    );
    '''
    await Database.execute(create_requisites_table_query)

    # Добавляем 3 записи по умолчанию, если их нет
    for i in range(1, 4):
        insert_default_requisite_query = f'''
        INSERT INTO requisites (card_order, card_number, card_name, bank_name, min_amount, max_amount, percentage)
        SELECT {i}, '-', '-', '-', 0, 0, 75
        WHERE NOT EXISTS (SELECT 1 FROM requisites WHERE card_order = {i});
        '''
        await Database.execute(insert_default_requisite_query)


    create_stopped_cards_table_query = '''
    CREATE TABLE IF NOT EXISTS stopped_cards (
        id SERIAL PRIMARY KEY,
        card_number VARCHAR(255) UNIQUE NOT NULL,
        added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    '''
    await Database.execute(create_stopped_cards_table_query)

    # Таблица для заявок на проверку чека
    create_profit_checks_table_query = '''
    CREATE TABLE IF NOT EXISTS profit_checks (
        id SERIAL PRIMARY KEY,
        user_id BIGINT NOT NULL,
        amount INTEGER NOT NULL,
        photo_file_id VARCHAR(255),
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        processed_at TIMESTAMP DEFAULT NULL
    );
    '''
    await Database.execute(create_profit_checks_table_query)

    # Таблица для статистики
    create_statistics_table_query = '''
    CREATE TABLE IF NOT EXISTS statistics (
        id INTEGER PRIMARY KEY DEFAULT 1,
        total_profits_count INTEGER DEFAULT 0,
        total_profits_amount INTEGER DEFAULT 0
    );
    '''
    await Database.execute(create_statistics_table_query)

    # Инициализируем статистику, если её нет
    insert_default_statistics_query = '''
    INSERT INTO statistics (id, total_profits_count, total_profits_amount)
    SELECT 1, 0, 0
    WHERE NOT EXISTS (SELECT 1 FROM statistics WHERE id = 1);
    '''
    await Database.execute(insert_default_statistics_query)

    create_curators_table_query = '''
    CREATE TABLE IF NOT EXISTS curators (
        id SERIAL PRIMARY KEY,
        user_id BIGINT UNIQUE NOT NULL,
        username VARCHAR(255) UNIQUE NOT NULL
    );
    '''
    await Database.execute(create_curators_table_query)

    add_curator_column_to_users_query = '''
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'curator_id') THEN
            ALTER TABLE users ADD COLUMN curator_id BIGINT DEFAULT NULL;
            ALTER TABLE users ADD CONSTRAINT fk_curator
                FOREIGN KEY (curator_id)
                REFERENCES curators(user_id)
                ON DELETE SET NULL;
        END IF;
    END
    $$;
    '''
    await Database.execute(add_curator_column_to_users_query)

    # Добавляем поля для staff
    add_staff_columns_query = '''
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'role') THEN
            ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'position') THEN
            ALTER TABLE users ADD COLUMN position VARCHAR(255) DEFAULT NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'is_on_shift') THEN
            ALTER TABLE users ADD COLUMN is_on_shift BOOLEAN DEFAULT FALSE;
        END IF;
    END
    $$;
    '''
    await Database.execute(add_staff_columns_query)

    # Добавляем поле для бана
    add_banned_column_query = '''
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_attribute WHERE attrelid = 'users'::regclass AND attname = 'is_banned') THEN
            ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT FALSE;
        END IF;
    END
    $$;
    '''
    await Database.execute(add_banned_column_query)

    print("Database tables initialized and checked.")

