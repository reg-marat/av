import os
import re
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===========================
# НАСТРОЙКИ
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHAT_ID = -1003671787625       # твой лог-чат
POSTBACK_CHAT_ID = -1003712583340  # чат с постбеками

# ищем ID между ==...==
ID_PATTERN = re.compile(r"==(\d+)==")

# ===========================
# УТИЛИТА ДЛЯ ЛОГОВ
# ===========================

async def send_log(app: Application, text: str):
    try:
        await app.bot.send_message(chat_id=LOG_CHAT_ID, text=f"📡 LOG: {text}")
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# ===========================
# /START
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await send_log(context.application, f"Пользователь {user_id} нажал /start")

    keyboard = [
        [InlineKeyboardButton("📱 Открыть Web App", callback_data="open_webapp")],
        [InlineKeyboardButton("ℹ️ Инструкция", callback_data="help")],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "👋 Привет! Я твой основной бот.\n\n"
        "Я помогу тебе пройти регистрацию и получить доступ к веб-приложению.\n\n"
        "Выбери действие:",
        reply_markup=reply_markup,
    )

# ===========================
# ОБРАБОТКА КНОПОК
# ===========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await send_log(context.application, f"Пользователь {user_id} нажал кнопку: {data}")

    if data == "help":
        await query.answer(
            "Сначала зарегистрируйся, затем внеси депозит. "
            "После депозита я выдам тебе пароль.",
            show_alert=True,
        )

    elif data == "open_webapp":
        await query.answer(
            "Кнопку Web App добавим на следующем шаге.",
            show_alert=True,
        )

# ===========================
# ЧТЕНИЕ ПОСТБЕК-ЧАТА
# ===========================

async def postback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # реагируем ТОЛЬКО на нужный чат
    if update.effective_chat.id != POSTBACK_CHAT_ID:
        return

    text = update.message.text or ""

    match = ID_PATTERN.search(text)
    if not match:
        await send_log(context.application, f"⚠️ Постбек без понятного ID: {text}")
        return

    user_id = int(match.group(1))

    await send_log(
        context.application,
        f"📩 Получен постбек для пользователя: {user_id}"
    )

    # сюда дальше добавим логику:
    # - регистрация → попросить депозит
    # - депозит → выдать пароль

# ===========================
# ЗАПУСК БОТА
# ===========================

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, postback_handler))

    print("✅ Bot started and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
