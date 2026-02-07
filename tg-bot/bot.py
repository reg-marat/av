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

# Адрес твоего веб-приложения
BASE_APP_URL = "https://aviatorbot.up.railway.app/"

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

    # Стандартное меню, без лишних кнопок внизу
    buttons = [
        [InlineKeyboardButton("📖 Инструкция к подключению и работе", callback_data="instruction")],
        [InlineKeyboardButton("🤖 Подключить бота", callback_data="connect")],
        [InlineKeyboardButton("💸 Стоимость", callback_data="price")],
        [InlineKeyboardButton("🆘 Помощь", callback_data="help")],
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

    buttons.append([InlineKeyboardButton(label, web_app=WebAppInfo(url=url))])

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
    status = user_status.get(user_id, "new")

    if data == "instruction":
        await query.edit_message_text(
            "1 - Подключение бота:\n"
            "Тебе нужно создать новый аккаунт и подождать около 1 минуты пока бот его обнаружит, "
            "потом внеси депозит и ожидай еще 2 минуты синхронизации бота. "
            "Бот подключен и готов к работе.\n\n"
            "2 - Использование бота:\n"
            "Как только начинается раунд - нажимай кнопку Мостра. "
            "Ты получишь коэффициент на котором самолет улетит в ЭТОМ раунде",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "connect":
        if status == "new":
            # Текст с гиперссылкой в конце
            text = (
                "Создай аккаунт. Депозит вносить не нужно.\n"
                "После создания бот напишет тебе что делать дальше.\n"
                "--- [СОЗДАТЬ АККАУНТ](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )
        elif status == "registered":
            text = (
                "✅ Аккаунт найден ботом. Теперь внеси депозит для подключения. "
                "Достаточно всего 20 евро, чтобы бот смог подключиться к аккаунту и начать синхронизацию. "
                "После внесения депозита бот напишет тебе что делать дальше.\n"
                "--- [ПРОДОЛЖИТЬ](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )
        else:  # deposited
            text = (
                "✅ Бот подключен к сайту - открывай бота, делай ставки и зарабатывай!\n"
                "--- [ОТКРЫТЬ ИГРУ](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )

        # Подставляем реальный ID пользователя
        text = text.format(user_id=user_id)

        await query.edit_message_text(
            text,
            reply_markup=menu_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif data == "price":
        await query.edit_message_text(
            "Бот полностью бесплатный. Разработчик верит в добро и честность людей. "
            "Если ты захочешь поделиться частью своего выигрыша - напиши мне и я пришлю реквизиты для перевода",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "help":
        await query.edit_message_text(
            "Если возникли вопросы - напиши мне и я сразу же тебе отвечу и помогу настроить бота.",
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
                text="✅ Аккаунт найден ботом. Теперь внеси депозит для подключения. "
                     "Достаточно всего 20 евро, чтобы бот смог подключиться к аккаунту и начать синхронизацию. "
                     "После внесения депозита бот напишет тебе что делать дальше.",
                reply_markup=menu_keyboard(user_id),
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

    # === ДЕПОЗИТ ===
    elif "deposit" in text_lower or "amount" in text_lower:
        user_status[user_id] = "deposited"

        await send_log(context.application, f"💰 Депозит получен для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="🎉 Поздравляю! Бот успешно подключен к аккаунту! Открывай приложение и зарабатывай!",
                reply_markup=menu_keyboard(user_id),
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

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
