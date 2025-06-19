from pathlib import Path
from telegram import Update
from utils.stats import load_stats
from telegram.ext import ContextTypes
from telegram.constants import ParseMode


from utils.decorators import admin_only


VERSION = "1.1.1"

# === Команда /stats — общая статистика по боту ===
@admin_only
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        stats = load_stats()
        total = stats.get("total_visits", 0)
        recent = len(stats.get("last_users", []))
        msg = (
            "📊 <b>Статистика:</b>\n"
            f"— Всего визитов: <b>{total}</b>\n"
            f"— Последние пользователи: <b>{recent}</b>"
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
