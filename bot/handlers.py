from telegram.ext import ContextTypes
from telegram import Update, ReplyKeyboardMarkup
from datetime import datetime


# Импорт логики обработки кнопок
from bot.logic import (
    send_sneki_full,
    send_drinks_full,
    send_today_offers,
    send_expired_offers,
    send_long,
    send_combined_blocks,
    send_new_offers_by_date, 
    send_expired_offers_by_date
)
from bot.admin_commands import (
    stats_command,
    last_users_command,
    log_command,
    version_command
)

# Настройки и ограничения доступа
from bot.config import ALLOWED_USERS, ADMIN_ID, BLOCKED_USERS


# Логирование действий пользователей
from utils.stats import update_stats
from utils.logger import log_user_activity


# Формирование сообщений для "Аромок"
from bot.messages import format_aromki_message
from utils.google_sheets import get_sheet_data


# === Команда /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if update.message:
        # Базовые кнопки
        keyboard = [
            ["🥤 Акции Напитки", "🥡 Акции Снеки"],
            ["💧💨 Акции Аромки", "📦 Все акции"],
            ["🆕 Новые акции", "📴 Завершённые акции"]
        ]

        # Только если это админ, добавляем админ-кнопки
        if user_id == ADMIN_ID:
            keyboard.append(["📊 Статистика", "🧾 Последние пользователи"])
            keyboard.append(["📁 Логи", "ℹ️ Версия бота"])

        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text("👋 Привет! Выбери нужную категорию:", reply_markup=reply_markup)



# === Проверка доступа по user_id ===
def is_blocked(user_id):
    """
    Проверяет, заблокирован ли пользователь.
    """
    return int(user_id) in BLOCKED_USERS


# === Обработка ввода даты (например, 20.06) ===
async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()

    # Проверка формата даты (ДД.ММ)
    try:
        datetime.strptime(user_input, "%d.%m")
        context.user_data["chosen_date"] = user_input

        keyboard = [
            ["🆕 Новые акции на дату", "📴 Завершённые акции на дату"],
            ["⬅️ Назад"]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"📅 Вы выбрали дату: {user_input}\nЧто показать?",
            reply_markup=reply_markup
        )
    except ValueError:
        await update.message.reply_text("❌ Введите дату в формате ДД.ММ (например, 20.06)")

# === Обработка всех входящих сообщений от пользователя ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        user_id = user.id
        text = update.message.text.strip()

        # Проверка авторизации
        if is_blocked(user_id):
            await update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
            return

        # Логгируем и обновляем статистику
        update_stats(user.id, user.username, text)
        log_user_activity({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }, text)

        # === Обработка команд ===
        if text == "🥤 Акции Напитки":
            await send_drinks_full(context.bot, update.effective_chat.id)

        elif text == "🥡 Акции Снеки":
            await send_sneki_full(context.bot, update.effective_chat.id)

        elif text == "💧💨 Акции Аромки":
            aromki_rows = get_sheet_data("Акции Аромки")
            msg = format_aromki_message(aromki_rows)
            await send_long(context.bot, update.effective_chat.id, msg)

        elif text == "📦 Все акции":
            aromki_rows = get_sheet_data("Акции Аромки")
            msg = format_aromki_message(aromki_rows)
            await send_long(context.bot, update.effective_chat.id, msg)
            await send_sneki_full(context.bot, update.effective_chat.id)
            await send_drinks_full(context.bot, update.effective_chat.id)

        elif text == "🆕 Новые акции":
            await send_today_offers(context.bot, update.effective_chat.id)

        elif text == "📴 Завершённые акции":
            await send_expired_offers(context.bot, update.effective_chat.id)

        elif text == "🆕 Новые акции на дату":
            date = context.user_data.get("chosen_date")
            if date:
                await send_new_offers_by_date(context.bot, update.effective_chat.id, date)
            else:
                await update.message.reply_text("⚠️ Сначала введите дату в формате ДД.ММ.")

        elif text == "📴 Завершённые акции на дату":
            date = context.user_data.get("chosen_date")
            if date:
                await send_expired_offers_by_date(context.bot, update.effective_chat.id, date)
            else:
                await update.message.reply_text("⚠️ Сначала введите дату в формате ДД.ММ.")
        elif text == "⬅️ Назад":
            await start(update, context)

        elif text == "📊 Статистика":
            await stats_command(update, context)

        elif text == "🧾 Последние пользователи":
            await last_users_command(update, context)

        elif text == "📁 Логи":
            await log_command(update, context)

        elif text == "ℹ️ Версия бота":
            await version_command(update, context)
        elif len(text) == 5 and "." in text:
            await handle_date_input(update, context)
            return
        else:
            await update.message.reply_text("🤖 Неизвестная команда. Пожалуйста, выбери из меню.")
    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")