import os
import asyncio
import nest_asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from telegram import Update, ReplyKeyboardMarkup
from google.oauth2.credentials import Credentials
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()

VERSION = "1.1.1"
send_combined_blocks
# === НАСТРОЙКИ ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = int(os.getenv("CHAT_ID"))
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")
SCOPES = [os.getenv("SCOPES")]

# === Авторизация Google ===
def get_google_service():
    creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    return build("sheets", "v4", credentials=creds)

# === Получение данных с листа ===
def get_sheet_data(sheet_name):
    service = get_google_service()
    range_name = f"'{sheet_name}'"
    result = service.spreadsheets().values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=range_name
    ).execute()
    return result.get("values", [])

# === Отправка по частям, если длинное ===
async def send_long(bot, chat_id, text, parse_mode="HTML"):
    MAX_LENGTH = 4096
    for i in range(0, len(text), MAX_LENGTH):
        await bot.send_message(chat_id=chat_id, text=text[i:i+MAX_LENGTH], parse_mode=parse_mode)

# === Форматирование блока ===
def format_block(block):
    def get(col_index, row):
        return row[col_index].strip() if len(row) > col_index and row[col_index].strip() else "не указано"

    main_row = block[0] if block else []
    text = "————————————————————\n"
    text += f"📅 Дата внесения акции: {get(0, main_row)}\n"
    text += f"📅 Период проведения: {get(1, main_row)}\n"
    text += "————————————————————\n"
    text += f"🛍 ТОВАРЫ: {get(2, main_row)}\n"

    for row in block[1:]:
        if len(row) > 2 and row[2].strip():
            text += row[2].strip() + "\n"

    text += "————————————————————\n"
    text += f"⚙️ МЕХАНИКА/% скидки: {get(3, main_row)}\n"
    text += "————————————————————\n"
    text += f"👥 УЧАСТНИКИ: {get(4, main_row)}\n"
    text += "————————————————————\n"
    text += "Есть\n"
    return text

# === Формирование всех блоков ===
def format_all_blocks(rows, skip_rows=1):
    blocks = []
    current_block = []
    for row in rows[skip_rows:]:  # пропускаем нужное количество строк
        if not any(cell.strip() for cell in row):
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)
    if current_block:
        blocks.append(current_block)

    messages = [format_block(b) for b in blocks]
    return messages

# === Отправка Снеки с логикой объединения ===
async def send_sneki_full(bot, chat_id):
    rows = get_sheet_data("Акции Снеки")
    blocks = format_all_blocks(rows, skip_rows=2)
    await send_combined_blocks(bot, chat_id, blocks, "🧾 Акция: Снеки\n")

# === Отправка Напитки с логикой объединения ===
async def send_drinks_full(bot, chat_id):
    rows = get_sheet_data("Акции Напитки")
    blocks = format_all_blocks(rows, skip_rows=1)
    await send_combined_blocks(bot, chat_id, blocks, "🧾 Акция: Напитки\n")

# === Универсальная отправка блоков ===
async def send_combined_blocks(bot, chat_id, blocks, header):
    combined = header
    messages = []

    for block in blocks:
        if len(combined) + len(block) < 4096:
            combined += block
        else:
            messages.append(combined)
            combined = block

    messages.append(combined)

    await asyncio.sleep(1)
    for i, msg in enumerate(messages):
        await send_long(bot, chat_id, msg if i == 0 else msg.replace(header, ""))

# === Форматирование Аромки ===
def format_aromki_message(rows):
    text = "🧾 Акция: Аромки\n"
    text += "————————————————————\n"
    main_row = rows[2] if len(rows) > 2 else []
    extra_row = rows[3] if len(rows) > 3 else []

    def get(col_index, row=main_row):
        return row[col_index].strip() if len(row) > col_index and row[col_index].strip() else "не указано"

    text += f"📅 Дата внесения акции: {get(0)}\n"
    text += f"📅 Период проведения: {get(1)}\n"
    text += "————————————————————\n"
    text += f"🛍 ТОВАРЫ: {get(2)}\n"
    if len(extra_row) > 2 and extra_row[2].strip():
        text += extra_row[2].strip() + "\n"
    text += "————————————————————\n"
    text += f"⚙️ МЕХАНИКА/% скидки: {get(3)}\n"
    text += "————————————————————\n"
    text += f"👥 УЧАСТНИКИ: {get(4)}\n"
    text += "————————————————————\n"
    text += "Есть"
    return text

# === Обработчики команд и кнопок ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        keyboard = [["🥤 Акции Напитки", "🥡 Акции Снеки"], ["💧💨 Акции Аромки", "📦 Все акции"], ["🆕 Новые акции", "📴 Завершённые акции"]]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Привет! Выбери нужную категорию:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if text == "🥡 Акции Снеки":
        await send_sneki_full(context.bot, update.effective_chat.id)
    elif text == "💧💨 Акции Аромки":
        aromki_rows = get_sheet_data('Акции Аромки')
        msg = format_aromki_message(aromki_rows)
        await send_long(context.bot, update.effective_chat.id, msg)
    elif text == "📦 Все акции":
        aromki_rows = get_sheet_data('Акции Аромки')
        msg = format_aromki_message(aromki_rows)
        await send_long(context.bot, update.effective_chat.id, msg)
        await send_sneki_full(context.bot, update.effective_chat.id)
        await send_drinks_full(context.bot, update.effective_chat.id)
    elif text == "🥤 Акции Напитки":
        await send_drinks_full(context.bot, update.effective_chat.id)
    elif text == "🆕 Новые акции":
        await send_today_offers(context.bot, update.effective_chat.id)
    elif text == "📴 Завершённые акции":
        await send_expired_offers(context.bot, update.effective_chat.id)


# === Новые акции сегодня ===
def filter_today_blocks(rows, skip_rows=1):
    today = datetime.now().strftime('%d.%m')
    blocks = []
    current_block = []

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    period = main_row[1].strip()
                    if '-' in period:
                        start_str = period.split('-')[0].strip()
                        if start_str == today:
                            blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            period = main_row[1].strip()
            if '-' in period:
                start_str = period.split('-')[0].strip()
                if start_str == today:
                    blocks.append(current_block)

    messages = [format_block(b) for b in blocks]
    return messages

async def send_today_offers(bot, chat_id):
    all_blocks = []
    for name, skip in [("Акции Аромки", 2), ("Акции Снеки", 2), ("Акции Напитки", 1)]:
        rows = get_sheet_data(name)
        filtered = filter_today_blocks(rows, skip_rows=skip)
        all_blocks.extend(filtered)

    if not all_blocks:
        await bot.send_message(chat_id=chat_id, text="📭 Новых акций нет на сегодня.")
    else:
        await send_combined_blocks(bot, chat_id, all_blocks, "🆕 Новые акции на сегодня:")

# === Завершённые акции (до вчерашнего дня) ===
def filter_expired_blocks(rows, skip_rows=1):
    today = datetime.now().date()
    blocks = []
    current_block = []

    def parse_date_range(period_str):
        try:
            _, end_str = period_str.split('-')
            end_str = end_str.strip()
            parsed = datetime.strptime(end_str, '%d.%m').date()
            parsed = parsed.replace(year=today.year)
            return parsed
        except:
            return None

    for row in rows[skip_rows:]:
        if not any(cell.strip() for cell in row):
            if current_block:
                main_row = current_block[0]
                if len(main_row) > 1:
                    end_date = parse_date_range(main_row[1])
                    if end_date and end_date == (today - timedelta(days=1)):
                        blocks.append(current_block)
                current_block = []
        else:
            current_block.append(row)

    if current_block:
        main_row = current_block[0]
        if len(main_row) > 1:
            end_date = parse_date_range(main_row[1])
            if end_date and end_date == (today - timedelta(days=1)):
                blocks.append(current_block)

    messages = [format_block(b) for b in blocks]
    return messages

async def send_expired_offers(bot, chat_id):
    categories = [
        ("Акции Аромки", 2, "💧💨 Завершённые акции: Аромки"),
        ("Акции Снеки", 2, "🥡 Завершённые акции: Снеки"),
        ("Акции Напитки", 1, "🥤 Завершённые акции: Напитки")
    ]

    any_found = False

    for sheet_name, skip, header in categories:
        rows = get_sheet_data(sheet_name)
        filtered = filter_expired_blocks(rows, skip_rows=skip)
        if filtered:
            any_found = True
            await send_combined_blocks(bot, chat_id, filtered, header)

    if not any_found:
        await bot.send_message(chat_id=chat_id, text="✅ На сегодня все акции ещё действуют.")

# === Запуск бота ===
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("🤖 Бот запущен. Ожидает /start и выбор кнопки")
    await app.run_polling()

if __name__ == '__main__':
    nest_asyncio.apply()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
