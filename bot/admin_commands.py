from pathlib import Path
from telegram import Update
from utils.stats import load_stats
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
import json
from utils.decorators import admin_only
from utils.stats import load_stats
from datetime import datetime
import re



VERSION = "1.1.1"
STATS_FILE = Path("stats.json")


# === Команда /stats — общая статистика по боту ===
@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:

        stats = load_stats()

        # === 1. Уникальные пользователи всего из users_list.log ===
        users_log_path = Path("logs/users_list.log")
        all_user_ids = set()
        if users_log_path.exists():
            with open(users_log_path, "r", encoding="utf-8") as f:
                for line in f:
                    match = re.search(r"UserID:\s*(\d+)", line)
                    if match:
                        all_user_ids.add(match.group(1))

        total_unique_users = len(all_user_ids)

        # === 2. Уникальные пользователи за сегодня ===
        today = datetime.now().date()
        today_users = set()
        uses_today = 0

        for record in stats.get("last_users", []):
            time_str = record.get("time")
            try:
                record_date = datetime.fromisoformat(time_str).date()
                if record_date == today:
                    today_users.add(record.get("user_id"))
                    uses_today += 1
            except Exception:
                continue

        msg = (
            "📊 <b>Статистика:</b>\n"
            f"— Уникальных пользователей всего: <b>{total_unique_users}</b>\n"
            f"— Уникальных пользователей за сегодня: <b>{len(today_users)}</b>\n"
            f"— Использований за сегодня: <b>{uses_today}</b>"
        )

        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)

    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при получении статистики: {e}")

# === Команда /last_users — последние пользователи ===
@admin_only
async def last_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = load_stats()
        users = stats.get("last_users", [])
        if not users:
            await update.message.reply_text("Пока нет данных.")
            return

        msg = "<b>Последние пользователи:</b>\n"
        for u in users:
            name = f"@{u['username']}" if u['username'] else f"ID {u['user_id']}"
            msg += f"• {name} — {u['action']} ({u['time'][:19]})\n"

        await update.message.reply_text(msg, parse_mode=ParseMode.HTML)
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при выводе последних пользователей: {e}")

# === Команда /log — отправка лог-файла ===
@admin_only
async def log_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        log_path = Path("logs/user_activity.log")
        if log_path.exists():
            await update.message.reply_document(document=log_path.open("rb"))
        else:
            await update.message.reply_text("📭 Лог-файл не найден.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при отправке лога: {e}")

# === Команда /version — вывод версии бота ===
@admin_only
async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(f"🛠 Версия бота: {VERSION}")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Ошибка при выводе версии: {e}")
