import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")  # ID чата, куда будут приходить заявки
    TEAM_CHAT_ID = os.getenv("TEAM_CHAT_ID") # ID чата команды для уведомлений о смене реквизитов
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "your_database_name")
    DB_USER = os.getenv("DB_USER", "your_db_user")
    DB_PASS = os.getenv("DB_PASS", "your_db_password") # <-- Исправлено здесь!

    DATABASE_URL = (
        f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    DEFAULT_ADMIN_PASSWORD = "123" # Пароль по умолчанию для админ-панели

