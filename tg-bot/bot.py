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

APP_BEFORE_DEPOSIT = "https://example.com"
APP_AFTER_DEPOSIT = "https://av2-production.up.railway.app/"

WEBAPP_PASSWORD = "AV2-ACCESS-2026"

ID_PATTERN = re.compile(r"==(\d+)==")

# память (пока без БД)
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
# ПОСТОЯННАЯ КЛАВИАТУРА (ВАЖНО!)
# ===========================

def main_keyboard():
    keyboard = [
        [KeyboardButton("📱 Открыть приложение")],
        [KeyboardButton("ℹ️ Инструкция")],
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        persistent=True,
        one_time_keyboard=False
    )

# ===========================
# WEBAPP-КНОПКА
# ===========================

def webapp_keyboard(user_id: int):
    status = user_status.get(user_id, "new")
    url = APP_AFTER_DEPOSIT if status == "deposited" else APP_BEFORE_DEPOSIT

    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🚀 Открыть Web App", web_app=WebAppInfo(url=url))]
    ])

# ===========================
# /START
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_status.setdefault(user_id, "new")

    await send_log(
        context.application,
        f"Пользователь {user_id} нажал /start (статус: {user_status[user_id]})"
    )

    text = (
        "👋 Привет!\n\n"
        "Ниже всегда будут кнопки.\n"
        "Нажми **📱 Открыть приложение**, чтобы продолжить."
    )

    # 🔥 ВАЖНО: ВСЕГДА даём клавиатуру
    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=main_keyboard(),
    )

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
        await update.message.reply_text(
            "Инструкция:\n1) Зарегистрируйся\n2) Внеси депозит\n3) Получи пароль",
            reply_markup=main_keyboard(),  # 🔥 ВАЖНО
        )

    elif text == "📱 Открыть приложение":
        await update.message.reply_text(
            "👇 Открой приложение:",
            reply_markup=webapp_keyboard(user_id),
        )
        # И ПОВТОРНО дублируем основную клавиатуру
        await update.message.reply_text(
            "Кнопки остаются внизу 👇",
            reply_markup=main_keyboard(),
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

    # РЕГИСТРАЦИЯ
    if "registration" in text_lower or "reg" in text_lower:
        user_status[user_id] = "registered"
        await send_log(context.application, f"📩 Регистрация для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="✅ Регистрация подтверждена!\n\nТеперь внеси депозит.",
                reply_markup=main_keyboard(),  # 🔥 ВАЖНО
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

    # ДЕПОЗИТ
    elif "deposit" in text_lower or "amount" in text_lower:
        user_status[user_id] = "deposited"

        await send_log(context.application, f"💰 Депозит получен для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text=f"🎉 Депозит подтверждён!\n\n🔑 Твой пароль:\n\n`{WEBAPP_PASSWORD}`",
                parse_mode="Markdown",
                reply_markup=main_keyboard(),  # 🔥 ВАЖНО
            )

            await context.application.bot.send_message(
                chat_id=user_id,
                text="👇 Открой приложение:",
                reply_markup=webapp_keyboard(user_id),
            )

        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

# ===========================
# ЗАПУСК
# ===========================

def main():
    print("🚀 Бот запускается...")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    app.add_handler(
        MessageHandler(filters.Chat(POSTBACK_CHAT_ID) & filters.TEXT, postback_handler)
    )

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler)
    )

    print("✅ Bot started and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
