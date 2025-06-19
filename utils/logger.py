import logging
from pathlib import Path


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
