import os
import re
from telegram import (
    Update,
    KeyboardButton,
    ReplyKeyboardMarkup,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ===========================
# НАСТРОЙКИ
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHAT_ID = -1003671787625       # чат для логов
POSTBACK_CHAT_ID = -1003712583340  # чат с постбеками

# ДВА ПРИЛОЖЕНИЯ
APP_BEFORE_DEPOSIT = "https://example.com"   # временная заглушка
APP_AFTER_DEPOSIT = "https://av2-production.up.railway.app/"

# ТВОЙ СТАТИЧНЫЙ ПАРОЛЬ
WEBAPP_PASSWORD = "AV2-ACCESS-2026"

# ищем ID между ==...==
ID_PATTERN = re.compile(r"==(\d+)==")

# Хранилище статусов пользователей (пока в памяти)
# "new" -> ничего нет
# "registered" -> есть регистрация
# "deposited" -> есть депозит
user_status = {}

# ===========================
# УТИЛИТА ДЛЯ ЛОГОВ
# ===========================

async def send_log(app: Application, text: str):
    try:
        await app.bot.send_message(chat_id=LOG_CHAT_ID, text=f"📡 LOG: {text}")
    except Exception as e:
        print(f"Ошибка логирования: {e}")

# ===========================
# ПОСТОЯННАЯ НИЖНЯЯ КЛАВИАТУРА
# ===========================

def main_keyboard():
    return ReplyKeyboardMarkup(
        [
            [KeyboardButton("📱 Открыть приложение")],
            [KeyboardButton("ℹ️ Инструкция")],
        ],
        resize_keyboard=True,
        persistent=True,
    )

# ===========================
# WEBAPP-КНОПКА (ДИНАМИЧЕСКАЯ)
# ===========================

def webapp_keyboard(user_id: int):
    status = user_status.get(user_id, "new")

    url = APP_AFTER_DEPOSIT if status == "deposited" else APP_BEFORE_DEPOSIT

    keyboard = [
        [InlineKeyboardButton(
            "🚀 Открыть Web App",
            web_app=WebAppInfo(url=url)
        )]
    ]
    return InlineKeyboardMarkup(keyboard)

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

    status = user_status[user_id]

    if status == "new":
        text = (
            "👋 Привет!\n\n"
            "1️⃣ Сначала зарегистрируйся.\n"
            "2️⃣ Затем внеси депозит.\n"
            "3️⃣ После депозита я дам тебе пароль.\n\n"
            "Можешь уже открыть приложение ниже."
        )
    elif status == "registered":
        text = (
            "✅ Регистрация у тебя уже есть.\n\n"
            "👉 Теперь внеси депозит, чтобы получить доступ."
        )
    else:  # deposited
        text = (
            "🎉 У тебя уже есть доступ!\n\n"
            "Используй кнопку ниже, чтобы открыть приложение."
        )

    # Сообщение + постоянные кнопки
    await update.message.reply_text(text, reply_markup=main_keyboard())

    # Отдельное сообщение с WebApp-кнопкой
    await update.message.reply_text(
        "👇 Открой приложение:",
        reply_markup=webapp_keyboard(user_id),
    )

# ===========================
# ОБРАБОТКА НИЖНИХ КНОПОК
# ===========================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "ℹ️ Инструкция":
        status = user_status.get(user_id, "new")

        if status == "new":
            msg = "Сначала зарегистрируйся, затем внеси депозит."
        elif status == "registered":
            msg = "Регистрация есть — внеси депозит."
        else:
            msg = "У тебя уже есть доступ."

        await update.message.reply_text(msg, reply_markup=main_keyboard())

    elif text == "📱 Открыть приложение":
        await update.message.reply_text(
            "👇 Открой приложение:",
            reply_markup=webapp_keyboard(user_id),
        )

# ===========================
# ЧТЕНИЕ ПОСТБЕК-ЧАТА
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

    # ====== РЕГИСТРАЦИЯ ======
    if "registration" in text_lower or "reg" in text_lower:
        user_status[user_id] = "registered"

        await send_log(context.application, f"📩 Регистрация получена для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="✅ Регистрация подтверждена!\n\nТеперь внеси депозит.",
                reply_markup=main_keyboard(),
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

    # ====== ДЕПОЗИТ ======
    elif "deposit" in text_lower or "dep" in text_lower or "amount" in text_lower:
        if user_status.get(user_id) == "deposited":
            await send_log(
                context.application,
                f"ℹ️ Повторный депозит для {user_id}, доступ уже был выдан"
            )
            return

        user_status[user_id] = "deposited"

        await send_log(
            context.application,
            f"💰 Депозит получен для {user_id} — выдаём пароль"
        )

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Депозит подтверждён!\n\n"
                     f"🔑 Твой пароль:\n\n`{WEBAPP_PASSWORD}`\n\n"
                     f"Теперь открой приложение по кнопке ниже 👇",
                parse_mode="Markdown",
                reply_markup=main_keyboard(),
            )

            await context.application.bot.send_message(
                chat_id=user_id,
                text="👇 Открой приложение:",
                reply_markup=webapp_keyboard(user_id),
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

    else:
        await send_log(
            context.application,
            f"ℹ️ Неизвестный постбек для {user_id}: {text}"
        )

# ===========================
# ЗАПУСК
# ===========================

def main():
    print("🚀 Бот запускается...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    # Сначала ловим постбеки (строгий фильтр по чату)
    app.add_handler(
        MessageHandler(filters.Chat(POSTBACK_CHAT_ID) & filters.TEXT, postback_handler)
    )

    # Потом — обычные сообщения пользователей
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("✅ Bot started and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
