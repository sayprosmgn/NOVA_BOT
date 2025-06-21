from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import pickle
import os

REACTIONS_FILE = "reactions.pkl"
DEFAULT_REACTIONS = ["🔥", "👍", "🤔", "😂", "😱", "👎"]

def load_reactions():
    if os.path.exists(REACTIONS_FILE):
        with open(REACTIONS_FILE, "rb") as f:
            return pickle.load(f)
    return {}

def save_reactions(data):
    with open(REACTIONS_FILE, "wb") as f:
        pickle.dump(data, f)

def get_reactions_keyboard(post_id, extra_buttons=None):
    buttons = [
        [InlineKeyboardButton(emoji, callback_data=f"react|{post_id}|{emoji}") for emoji in DEFAULT_REACTIONS]
    ]
    if extra_buttons:
        buttons.extend(extra_buttons)
    return InlineKeyboardMarkup(buttons)

# Обработка callback от кнопок реакции
def register_reactions_handlers(app):
    @app.on_callback_query()
    def handle_callback(client, callback_query):
        data = callback_query.data
        if data.startswith("react|"):
            _, post_id, emoji = data.split("|", 2)
            reactions = load_reactions()
            reactions.setdefault(post_id, {})
            reactions[post_id][emoji] = reactions[post_id].get(emoji, 0) + 1
            save_reactions(reactions)
            callback_query.answer(f"Вы поставили реакцию {emoji}!")
        elif data.startswith("subscribe:"):
            callback_query.answer("Функция подписки скоро будет доступна!", show_alert=True)
