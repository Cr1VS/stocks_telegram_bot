import asyncio
import logging
import nest_asyncio
from telegram.error import TelegramError
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters


from bot.config import BOT_TOKEN
from bot.handlers import start, handle_message, handle_date_input
from bot.admin_commands import (
    stats_command,
    last_users_command,
    log_command,
    version_command,
)


# Разрешаем повторный запуск event loop (актуально для некоторых окружений, например Jupyter)
nest_asyncio.apply()


# === Настройка логирования ошибок ===
logging.basicConfig(
    filename="logs/error.log",
    level=logging.ERROR,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)


# === Основная функция запуска бота ===
async def main():
    try:
        # Создаём приложение Telegram-бота
        app = ApplicationBuilder().token(BOT_TOKEN).build()

        # Обработчик команды /start
        app.add_handler(CommandHandler("start", start))

        # Обработчик всех текстовых сообщений (не команд)
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))


        # Обработчик команды /stats — выводит общую статистику по боту (всего пользователей и активных)
        app.add_handler(CommandHandler("stats", stats_command))

        # Обработчик команды /last_users — выводит список последних пользователей, которые взаимодействовали с ботом
        app.add_handler(CommandHandler("last_users", last_users_command))

        # Обработчик команды /log — отправляет лог-файл активности пользователей (user_activity.log) прямо в Telegram
        app.add_handler(CommandHandler("log", log_command))

        # Обработчик команды /version — отображает текущую версию бота
        app.add_handler(CommandHandler("version", version_command))
        
        # Обработка ввода даты — если это ДД.ММ формат
        app.add_handler(MessageHandler(filters.Regex(r"^\d{2}\.\d{2}$"), handle_date_input))

        print("🤖 Бот запущен. Ожидает /start и выбор кнопки")

        # Запуск polling
        await app.run_polling()

    except TelegramError as e:
        logging.error(f"Ошибка Telegram API: {e}", exc_info=True)
        print(f"❌ Ошибка Telegram API: {e}")

    except Exception as e:
        logging.error("Непредвиденная ошибка при запуске бота", exc_info=True)
        print(f"⚠️   Непредвиденная ошибка: {e}")


# === Точка входа ===
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановка бота пользователем")
