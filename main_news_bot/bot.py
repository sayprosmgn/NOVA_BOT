from pyrogram import Client
from handlers.commands import register_general_handlers
from auto_poster import run_autoposting
from config import API_ID, API_HASH, BOT_TOKEN, CHANNEL_ID
from pyrogram.types import BotCommand
import threading

def setup_commands(client):
    client.set_bot_commands([
        BotCommand("start", "Запустить бота"),
        BotCommand("help", "Справка по функциям"),
        BotCommand("news", "Свежая новость"),
        BotCommand("stats", "Статистика по темам"),
        BotCommand("filter", "Новости по теме (пример: /filter israel)"),
    ])
    print("Меню команд успешно установлено!")

def autopost_thread(app):
    run_autoposting(app, CHANNEL_ID)

if __name__ == "__main__":
    app = Client("main_news_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    register_general_handlers(app)

    app.start()
    setup_commands(app)
    threading.Thread(target=autopost_thread, args=(app,), daemon=True).start()
    print("Бот запущен! Слушает команды, делает автопостинг, собирает реакции.")
    app.stop()  # Завершает работу после тестового запуска

    # Вместо app.idle() — просто используем app.run() в самом конце:
    app.run()
