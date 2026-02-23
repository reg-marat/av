import os
import re
import json
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

# Память состояний пользователей (теперь сохраняем в файл)
# Возможные состояния: "new", "registered", "deposited"
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
        [InlineKeyboardButton("📖 Istruzioni per la connessione e l’utilizzo", callback_data="instruction")],
        [InlineKeyboardButton("🤖 Collega il bot", callback_data="connect")],
        [InlineKeyboardButton("💸 Prezzo", callback_data="price")],
        [InlineKeyboardButton(
            "🆘 Assistenza",
            url="https://t.me/Dante_Valdes?text=Ciao!%20Ho%20una%20domanda%20sul%20bot"
        )],
    ]

    if status == "new":
        url = f"{BASE_APP_URL}?screen=noreg"
        label = "🔒 Apri l’app (in attesa della registrazione)"
    elif status == "registered":
        url = f"{BASE_APP_URL}?screen=nodep"
        label = "⏳ Apri l’app (in attesa del deposito)"
    else:
        url = BASE_APP_URL
        label = "🚀 Apri l’app (accesso attivo)"

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
        "👋 Ciao! Questo è il menu principale del bot.\n"
        "Tutte le funzioni sono disponibili nei pulsanti qui sotto 👇",
        reply_markup=menu_keyboard(user_id),
    )

# ===========================
# ОБРАБОТКА INLINE-КНОПОК
# ===========================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    await query.answer()
    status = user_status.get(user_id, "new")

    # ЛОГ ЛЮБОГО НАЖАТИЯ INLINE-КНОПКИ
    await send_log(
        context.application,
        f"Пользователь {user_id} нажал inline-кнопку '{data}' (статус: {status})"
    )

    if data == "instruction":
        await query.edit_message_text(
            "1 - Connessione del bot:\n"
            "Devi creare un nuovo account e attendere circa 1 minuto finché il bot lo rileva. "
            "Poi effettua un deposito e attendi altri 2 minuti per la sincronizzazione. "
            "Il bot sarà collegato e pronto all’uso.\n\n"
            "2 - Utilizzo del bot:\n"
            "Quando inizia il round, premi il pulsante Mostra. "
            "Riceverai il coefficiente a cui l’aereo volerà via in QUESTO round.",
            reply_markup=menu_keyboard(user_id),
        )

    elif data == "connect":
        if status == "new":
            text = (
                "Crea un account. Non è necessario effettuare un deposito.\n"
                "Dopo la creazione, il bot ti dirà cosa fare.\n"
                "--- [CREA ACCOUNT](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )
        elif status == "registered":
            text = (
                "✅ Account rilevato dal bot. Ora effettua un deposito per la connessione. "
                "Bastano solo 20 euro affinché il bot possa collegarsi e iniziare la sincronizzazione. "
                "Dopo il deposito, il bot ti dirà cosa fare.\n"
                "--- [CONTINUA](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )
        else:
            text = (
                "✅ Il bot è collegato al sito — apri il bot, piazza le puntate e guadagna!\n"
                "--- [APRI IL GIOCO](https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}) ---"
            )

        text = text.format(user_id=user_id)

        await query.edit_message_text(
            text,
            reply_markup=menu_keyboard(user_id),
            parse_mode="Markdown"
        )

    elif data == "price":
        await query.edit_message_text(
            "Il bot è completamente gratuito. Lo sviluppatore crede nella bontà e nell’onestà delle persone. "
            "Se vorrai condividere una parte delle tue vincite — scrivimi e ti invierò i dati per il trasferimento.",
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
        save_users()

        await send_log(context.application, f"📩 Регистрация для {user_id}")

        try:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton(
                    "CONTINUA",
                    url=f"https://gembl.pro/click?o=705&a=1933&sub_id2={user_id}"
                )]
            ])

            await context.application.bot.send_message(
                chat_id=user_id,
                text=(
                    "✅ Account rilevato dal bot. Ora effettua un deposito per la connessione. "
                    "Bastano solo 20 euro affinché il bot possa collegarsi e iniziare la sincronizzazione. "
                    "Dopo il deposito, il bot ti dirà cosa fare."
                ),
                reply_markup=keyboard,
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

    # === ДЕПОЗИТ ===
    elif "deposit" in text_lower or "amount" in text_lower:
        user_status[user_id] = "deposited"
        save_users()

        await send_log(context.application, f"💰 Депозит получен для {user_id}")

        try:
            await context.application.bot.send_message(
                chat_id=user_id,
                text="🎉 Congratulazioni! Il bot è stato collegato con successo al tuo account! "
                     "Apri l’app e inizia a guadagnare!",
                reply_markup=menu_keyboard(user_id),
            )
        except Exception as e:
            await send_log(context.application, f"❌ Не смог написать пользователю {user_id}: {e}")

# ===========================
# ЗАПУСК БОТА
# ===========================

def main():
    print("🚀 Бот запускается...")

    load_users()

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
