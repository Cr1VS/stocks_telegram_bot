from telegram.ext import ContextTypes
from telegram import Update, ReplyKeyboardMarkup, Bot
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
    send_expired_offers_by_date,
    send_formatted_new_offers,
    send_formatted_expired_offers,
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
from utils.logger import log_user_activity, log_new_user, log_user_action_to_personal_file


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
            ["🆕 Новые акции", "📴 Завершённые акции"],
            ["🟢 Новые акции для отправки", "🔴 Завершённые акции для отправки"]
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
from datetime import datetime

async def handle_date_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text.strip()
    today_year = datetime.now().year

    # Попробуем разобрать дату в разных форматах
    parsed_date = None
    formats = [
        ("%d.%m", lambda dt: dt.replace(year=today_year)),
        ("%d-%m", lambda dt: dt.replace(year=today_year)),
        ("%d.%m.%y", lambda dt: dt),
        ("%d-%m-%y", lambda dt: dt),
        ("%d.%m.%Y", lambda dt: dt),
        ("%d-%m-%Y", lambda dt: dt),
    ]

    for fmt, adjust_func in formats:
        try:
            dt = datetime.strptime(user_input, fmt)
            dt = adjust_func(dt)
            parsed_date = dt
            break
        except ValueError:
            continue

    if parsed_date:
        context.user_data["chosen_date"] = parsed_date.strftime("%d.%m.%Y")

        keyboard = [
            ["🆕 Новые акции на дату", "📴 Завершённые акции на дату"],
            ["🟢 Новые акции для отправки", "🔴 Завершённые акции для отправки"],
            ["⬅️ Назад"]
    ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            f"📅 Вы выбрали дату: {parsed_date.strftime('%d.%m.%Y')}\nЧто показать?",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("❌ Введите дату в формате ДД.ММ, ДД-ММ или ДД-ММ-ГГ(ГГ)")



# === Обработка всех входящих сообщений ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        user_id = user.id
        text = update.message.text.strip()

        # Логгируем нового пользователя и обновляем статистику
        log_new_user({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        })
        update_stats(user.id, user.username, text)

        # Логгируем действия
        log_user_activity({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }, text)

        # Логгируем в персональный лог
        await log_user_action_to_personal_file({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name
        }, text)

        # Блокировка
        if is_blocked(user_id):
            await update.message.reply_text("⛔️ У вас нет доступа к этому боту.")
            return

        # === Обработка команд ===
        if text == "🥤 Акции Напитки":
            await send_drinks_full(context.bot, update.effective_chat.id)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "🥡 Акции Снеки":
            await send_sneki_full(context.bot, update.effective_chat.id)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "💧💨 Акции Аромки":
            aromki_rows = get_sheet_data("Акции Аромки")
            msg = format_aromki_message(aromki_rows)
            await send_long(context.bot, update.effective_chat.id, msg)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "📦 Все акции":
            aromki_rows = get_sheet_data("Акции Аромки")
            msg = format_aromki_message(aromki_rows)
            await send_long(context.bot, update.effective_chat.id, msg)
            await send_sneki_full(context.bot, update.effective_chat.id)
            await send_drinks_full(context.bot, update.effective_chat.id)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )
        elif text == "🟢 Новые акции для отправки":
            await send_formatted_new_offers(context.bot, update.effective_chat.id, context)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "🔴 Завершённые акции для отправки":
            await send_formatted_expired_offers(context.bot, update.effective_chat.id, context)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "🆕 Новые акции":
            await send_today_offers(context.bot, update.effective_chat.id)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "📴 Завершённые акции":
            await send_expired_offers(context.bot, update.effective_chat.id)
            await log_user_action_to_personal_file(
                user_data=update.effective_user.to_dict(),
                action=update.message.text,
                bot=context.bot  # ✅ берём bot из context
            )

        elif text == "🆕 Новые акции на дату":
            date = context.user_data.get("chosen_date")
            if date:
                await send_new_offers_by_date(context.bot, update.effective_chat.id, date)
                await log_user_action_to_personal_file(
                    user_data=update.effective_user.to_dict(),
                    action=update.message.text,
                    bot=context.bot  # ✅ берём bot из context
                )
            else:
                await update.message.reply_text("⚠️ Сначала введите дату в формате ДД.ММ.")

        elif text == "📴 Завершённые акции на дату":
            date = context.user_data.get("chosen_date")
            if date:
                await send_expired_offers_by_date(context.bot, update.effective_chat.id, date)
                await log_user_action_to_personal_file(
                    user_data=update.effective_user.to_dict(),
                    action=update.message.text,
                    bot=context.bot  # ✅ берём bot из context
                )
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

        elif any(sep in text for sep in [".", "-"]) and any(char.isdigit() for char in text):
            await handle_date_input(update, context)

        else:
            await update.message.reply_text("🤖 Неизвестная команда. Пожалуйста, выбери из меню.")

    except Exception as e:
        await update.message.reply_text(f"⚠️ Произошла ошибка: {e}")


