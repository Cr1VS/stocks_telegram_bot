from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes


from bot.config import ADMIN_ID


def admin_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("⛔️ У вас нет доступа к этой команде.")
            return
        return await func(update, context, *args, **kwargs)
    return wrapper