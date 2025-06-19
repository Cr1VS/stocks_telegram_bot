import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials


# === Загрузка переменных окружения из .env ===
load_dotenv()


# === Константы из .env ===
SCOPES = [os.getenv("SCOPES")]                   # Права доступа к Google Sheets
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")     # ID таблицы Google Sheets


def get_google_service():
    """
    Создаёт и возвращает авторизованный объект Google Sheets API.
    Использует файл token.json для авторизации.
    """
    try:
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        print("❌ Ошибка при создании сервиса Google Sheets:", e)
        return None


def get_sheet_data(sheet_name):
    """
    Получает данные с указанного листа Google Таблицы.

    :param sheet_name: Название листа (например, 'Акции Снеки')
    :return: Двумерный список строк с данными таблицы или пустой список при ошибке
    """
    try:
        service = get_google_service()
        if not service:
            raise RuntimeError("Сервис Google Sheets не инициализирован.")

        range_name = f"'{sheet_name}'"  # Название листа в кавычках
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()

        return result.get("values", [])

    except Exception as e:
        print(f"⚠️ Ошибка при получении данных с листа '{sheet_name}': {e}")
        return []
