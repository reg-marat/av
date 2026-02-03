import os
import asyncio
from telethon import TelegramClient, events, Button

# Берём токен из Railway
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Нам нужен только бот, без api_id/api_hash
client = TelegramClient("bot", api_id=0, api_hash="", bot_token=BOT_TOKEN)

# === /start ===
@client.on(events.NewMessage(pattern="/start"))
async def start(event):
    buttons = [
        [Button.text("▶️ Начать настройку")],
        [Button.url("🌐 Открыть Web App", "https://YOUR_WEB_APP_URL")]
    ]

    await event.reply(
        "Привет! Я помогу тебе настроить доступ.\n\nВыбери действие:",
        buttons=buttons
    )

# === Обработчик кнопки "Начать настройку" ===
@client.on(events.NewMessage)
async def handle_text(event):
    if event.text == "▶️ Начать настройку":
        await event.reply(
            "Шаг 1: Зарегистрируйтесь по вашей ссылке.\n"
            "После регистрации я сообщу, что делать дальше."
        )

if __name__ == "__main__":
    client.start()
    print("Bot is running...")
    client.run_until_disconnected()
