import os
from dotenv import load_dotenv


# Загружаем переменные окружения из .env файла
load_dotenv()


try:
    # Токен бота Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    if not BOT_TOKEN:
        raise ValueError("❌ Не указан BOT_TOKEN в .env")

    # ID чата (может быть использован как фильтр или для логов)
    CHAT_ID = int(os.getenv("CHAT_ID"))
    
    # ID таблицы Google Sheets
    SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
    if not SPREADSHEET_ID:
        raise ValueError("❌ Не указан SPREADSHEET_ID в .env")

    # Права доступа к Google Sheets API
    SCOPES = [os.getenv("SCOPES")]
    if not SCOPES or not SCOPES[0]:
        raise ValueError("❌ Не указаны SCOPES в .env")

    # Список разрешённых пользователей (через запятую)
    ALLOWED_USERS = list(map(int, os.getenv("ALLOWED_USERS", "").split(",")))

    # Админ ID
    ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
    
    # Ban users
    BLOCKED_USERS = list(map(int, os.getenv("BLOCKED_USERS", "").split(",")))

except ValueError as ve:
    print(ve)
    # При критической ошибке можно вызвать exit(1), чтобы не запускать бота
    exit(1)
except Exception as e:
    print(f"⚠️ Ошибка при загрузке конфигурации: {e}")
    exit(1)
