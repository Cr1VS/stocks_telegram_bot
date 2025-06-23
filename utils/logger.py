import logging
from pathlib import Path
from datetime import datetime 
from dotenv import load_dotenv
import os
from telegram import Bot

# Загружаем переменные окружения из .env файла
load_dotenv()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))  # из .env
NOTIFY_USER_ID = int(os.getenv("NOTIFY_USER_ID"))  
# === Создание папки logs, если её нет ===
Path("logs").mkdir(parents=True, exist_ok=True)


# === Настройка логгера для записи пользовательской активности ===
logging.basicConfig(
    filename="logs/user_activity.log",  # Файл для логов активности
    level=logging.INFO,                 # Уровень логирования
    format="%(asctime)s | %(message)s", # Формат: время + сообщение
    encoding="utf-8"                    # Кодировка
)


def log_user_activity(user_data: dict, action: str):
    """
    Логирует информацию о пользователе и его действии.

    :param user_data: словарь с данными пользователя Telegram
    :param action: строка, описывающая действие пользователя
    """
    try:
        # Извлечение данных с защитой от отсутствующих ключей
        user_id = user_data.get("id", "unknown")
        username = user_data.get("username", "—")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # Формирование строки лога
        message = (
            f"UserID: {user_id} | "
            f"Username: @{username} | "
            f"Name: {first_name} {last_name} | "
            f"Action: {action}"
        )

        # Запись в лог
        logging.info(message)


    except Exception as e:
        # Логирование ошибок логгера (в отдельный log файл можно настроить при необходимости)
        logging.error(f"Ошибка при логировании активности: {e}")


def log_new_user(user_data: dict):
    """
    Добавляет нового пользователя в список, если он ещё не записан.
    """
    try:
        user_id = str(user_data.get("id", "unknown"))
        username = user_data.get("username", "—")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        # Путь к списку пользователей
        user_list_path = Path("logs/users_list.log")
        user_list_path.touch(exist_ok=True)

        with user_list_path.open("r", encoding="utf-8") as f:
            existing = f.read()

        # Если ID уже есть в списке — не добавляем
        if user_id in existing:
            return

        # Номер по порядку
        count = existing.strip().count("UserID:") + 1

        entry = (
            f"#{count}\n"
            f"UserID: {user_id}\n"
            f"Username: @{username}\n"
            f"Name: {first_name} {last_name}\n"
            f"{'-'*30}\n"
        )

        with user_list_path.open("a", encoding="utf-8") as f:
            f.write(entry)

    except Exception as e:
        logging.error(f"Ошибка при логировании нового пользователя: {e}")


async def log_user_action_to_personal_file(user_data: dict, action: str, bot=None):
    try:
        user_id = int(user_data.get("id", 0))
        username = user_data.get("username", "—")
        first_name = user_data.get("first_name", "")
        last_name = user_data.get("last_name", "")

        log_line = (
            f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
            f"{first_name} {last_name} (@{username}) | {action}"
        )

        # 📁 Сохраняем в персональный лог
        personal_log_path = Path(f"logs/user_{user_id}.log")
        personal_log_path.parent.mkdir(parents=True, exist_ok=True)
        with personal_log_path.open("a", encoding="utf-8") as f:
            f.write(log_line + "\n")

        # ✅ Уведомляем админа, ТОЛЬКО если:
        # - пользователь в списке разрешённых
        # - и это НЕ сам админ
        if bot and user_id != ADMIN_ID and user_id == NOTIFY_USER_ID:
            await bot.send_message(chat_id=ADMIN_ID, text=log_line)

    except Exception as e:
        print(f"⚠️ Ошибка при логировании действий пользователя: {e}")