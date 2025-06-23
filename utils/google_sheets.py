import os
import json
from dotenv import load_dotenv
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

# === Загрузка .env (если локально запускаешь) ===
load_dotenv()

# === Константы ===
SCOPES = [os.getenv("SCOPES")]                   # Права доступа
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")     # ID таблицы


def get_google_service():
    """
    Создаёт авторизованный объект Google Sheets API,
    используя переменные окружения вместо token.json.
    """
    try:
        token_data = json.loads(os.environ["GOOGLE_TOKEN_JSON"])  # токен
        creds = Credentials.from_authorized_user_info(token_data, SCOPES)
        return build("sheets", "v4", credentials=creds)
    except Exception as e:
        print("❌ Ошибка при создании сервиса Google Sheets:", e)
        return None


def get_sheet_data(sheet_name):
    """
    Получает данные с указанного листа Google Таблицы.
    """
    try:
        service = get_google_service()
        if not service:
            raise RuntimeError("Сервис Google Sheets не инициализирован.")

        range_name = f"'{sheet_name}'"
        result = service.spreadsheets().values().get(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name
        ).execute()

        return result.get("values", [])

    except Exception as e:
        print(f"⚠️ Ошибка при получении данных с листа '{sheet_name}': {e}")
        return []
