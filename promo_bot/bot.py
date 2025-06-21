from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import pickle
import os
from config import API_ID, API_HASH, BOT_TOKEN, MAIN_CHANNEL

USERS_FILE = "users.pkl"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "rb") as f:
            return pickle.load(f)
    return set()

def save_users(data):
    with open(USERS_FILE, "wb") as f:
        pickle.dump(data, f)

users = load_users()
app = Client("promo_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

def add_user(user_id):
    if user_id not in users:
        users.add(user_id)
        save_users(users)

def get_invite_link(user_id=None):
    base = f"https://t.me/{MAIN_CHANNEL.lstrip('@')}"
    # С персональным параметром для отслеживания рефералов
    if user_id:
        return f"{base}?start={user_id}"
    return base

@app.on_message(filters.command("start") & filters.private)
def start(client, message: Message):
    user_id = message.from_user.id
    add_user(user_id)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔥 Присоединиться к новостям!", url=get_invite_link())],
        [InlineKeyboardButton("🔁 Получить персональную ссылку", callback_data="get_ref")]
    ])
    message.reply(
        f"👋 Привет! Это официальный промо-бот новостного канала {MAIN_CHANNEL}.\n\n"
        "Хочешь быть в курсе мировых событий без спама и рекламы? Жми «Присоединиться»!\n"
        "Расскажи о нас друзьям — за каждого друга участвуешь в розыгрыше месяца! 👇",
        reply_markup=kb
    )

@app.on_callback_query(filters.regex("get_ref"))
def ref_link(client, callback_query):
    user_id = callback_query.from_user.id
    link = get_invite_link(user_id)
    callback_query.message.reply(
        f"Твоя персональная ссылка для приглашения друзей:\n\n{link}\n\n"
        "За каждого друга — +1 шанс в розыгрыше месяца! Просто перешли ссылку друзьям или размести в соцсетях."
    )
    callback_query.answer("Ссылка сгенерирована!", show_alert=True)

@app.on_message(filters.command("stats") & filters.private)
def stats(client, message: Message):
    count = len(users)
    message.reply(f"Боту уже доверяют {count} человек(а)! Спасибо, что выбираешь нас 🤗")

if __name__ == "__main__":
    print("Промо-бот запущен!")
    app.run()
