import os
import re
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ===========================
# НАСТРОЙКИ
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHAT_ID = -1003671787625       # чат для логов
POSTBACK_CHAT_ID = -1003712583340  # чат с постбеками

# Адрес твоего веб-приложения (меняй на свой домен при необходимости)
BASE_APP_URL = "https://aviatorbot.up.railway.app/"

WEBAPP_PASSWORD = "7300"

# Вытаскиваем ID пользователя из постбека между ==
ID_PATTERN = re.compile(r"==(\d+)==")

# Память состояний пользователей (пока в оперативке)
# Возможные состояния: "new", "registered", "deposited"
user_status = {}

# ===========================
# ЛОГИ
# ===========================

async def send_log(app: Application, text: str):
    try:
        await app.bot.send_message(chat_id=LOG_CHAT_ID, text=f"📡 LOG: {text}")
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# ===========================
# УНИВЕРСАЛЬНОЕ INLINE-МЕНЮ
# ===========================

def menu_keyboard(user_id: int):
    status = user_status.get(user_id, "new")

    buttons = [
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu")],
        [InlineKeyboardButton("ℹ️ Инструкция", callback_data="help")],
    ]

    # Динамическая WebApp-кнопка
    if status == "new":
        url = f"{BASE_APP_URL}?state=waiting_reg"
        label = "🔒 Открыть приложение (ожидаем регистрацию)"
    elif status == "registered":
        url = f"{BASE_APP_URL}?state=waiting_deposit"
        label = "⏳ Открыть приложение (ожидаем депозит)"
    else:  # deposited
        url = f"{BASE_APP_URL}?state=unlocked"
        label = "🚀 Открыть приложение (доступ открыт)"

    buttons.append([
        InlineKeyboardButton(label, web_app=WebAppInfo(url=url))
    ])

    return InlineKeyboardMarkup(buttons)

# ===========================
# /START
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_status.setdefault(user_id, "new")

    await send_log(
        context.application,
        f"Пользователь {user_id} нажал /start (статус: {user_status[user_id]})"
    )

    await update.message.reply_text(
        "👋 Привет! Это главное меню бота.\n"
        "Все действия доступны в кнопках ниже 👇",
        reply_markup=menu_keyboard(user_id),
    )

# ===========================
# ОБРАБОТКА INLINE-КНОПОК (МЕНЮ)
# ===========================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()

    if data == "menu":
        await query.edit_message_text(
            "🏠 Главное меню",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "help":
        await query.edit_message_text(
            "📖 Инструкция:\n\n"
            "1) Зарегистрируйся у партнёра\n"
            "2) Внеси депозит\n"
            "3) Получи пароль от бота\n\n"
            "Выбери действие ниже 👇",
            reply_markup=menu_keyboard(user_id),
        )

# ===========================
# ОБРАБОТКА ПОСТБЕКОВ
# ===========================

async def postback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != POSTBACK_CHAT_ID:
        return

    text = update.message.text or ""
    match = ID_PATTERN.search(text)

    if not match:
        await send_log(context.application, f"⚠️ Постбек без понятного ID: {text}")
        return

    user_id = int(match.group(1))
    user_status.setdefault(user_id, "new")

    text_lower = text.lower()

    # === РЕГИСТРАЦИЯ ===
    if "registration" in text_lower or "reg" in text_lower:
        user_status[user_id] = "registered"

        await send_log(context.application, f"📩 Регистрация для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="✅ Регистрация подтверждена!\n\n"
                     "Теперь внеси депозит, чтобы получить доступ.",
                reply_markup=menu_keyboard(user_id),
            )
        except Exception as e:
            await send_log(
                context.application,
                f"❌ Не смог написать пользователю {user_id}: {e}"
            )

    # === ДЕПОЗИТ ===
    elif "deposit" in text_lower or "amount" in text_lower:
        user_status[user_id] = "deposited"

        await send_log(context.application, f"💰 Депозит получен для {user_id}")

        try:
            # Выдаём пароль
            await context.application.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Депозит подтверждён!\n\n"
                     f"🔑 Твой пароль:\n\n`{WEBAPP_PASSWORD}`",
                parse_mode="Markdown",
                reply_markup=menu_keyboard(user_id),
            )

            # Отдельное сообщение с WebApp
            await context.application.bot.send_message(
                chat_id=user_id,
                text="👇 Теперь можешь открыть приложение:",
                reply_markup=menu_keyboard(user_id),
            )

        except Exception as e:
            await send_log(
                context.application,
                f"❌ Не смог написать пользователю {user_id}: {e}"
            )

# ===========================
# ЗАПУСК БОТА
# ===========================

def main():
    print("🚀 Бот запускается...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))
    app.add_handler(
        MessageHandler(filters.Chat(POSTBACK_CHAT_ID) & filters.TEXT, postback_handler)
    )

    print("✅ Bot started and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
