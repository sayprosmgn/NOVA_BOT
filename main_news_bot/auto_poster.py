import schedule
import time
import feedparser
import pickle
import os
import openai
import requests
from config import OPENAI_KEY, GOOGLE_KEY, YANDEX_KEY, YANDEX_FOLDER_ID
from handlers.reactions import get_reactions_keyboard
import hashlib

POSTED_LINKS_FILE = "posted_links.pkl"

def short_id(link):
    return hashlib.md5(link.encode()).hexdigest()[:16]

def load_posted_links():
    if os.path.exists(POSTED_LINKS_FILE):
        with open(POSTED_LINKS_FILE, "rb") as f:
            return pickle.load(f)
    return set()

def save_posted_links(posted_links):
    with open(POSTED_LINKS_FILE, "wb") as f:
        pickle.dump(posted_links, f)

posted_links = load_posted_links()

# RSS-источники (оставь или дополни)
RSS_FEEDS = [
    "http://feeds.bbci.co.uk/news/world/rss.xml",
    "https://feeds.nbcnews.com/nbcnews/public/news",
    # ... остальные ...
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://www.reutersagency.com/feed/?best-topics=world&post_type=best",
    "https://apnews.com/rss",
]

COUNTRY_TOPICS = {
    'США':      ['usa', 'trump', 'biden', 'white house', 'us ', 'washington', 'america', 'cnn', 'nbc', 'new york'],
    'Великобритания': ['uk', 'britain', 'london', 'bbc', 'sky news', 'guardian'],
    'Израиль':  ['israel', 'jerusalem', 'tel aviv', 'idf', 'gaza', 'hamas', 'jpost', 'haaretz'],
    'Россия':   ['russia', 'moscow', 'kremlin', 'putin', 'rbc', 'lenta', 'tass', 'meduza'],
    'Китай':    ['china', 'beijing', 'xi jinping', 'scmp'],
    'Япония':   ['japan', 'tokyo', 'kyodo'],
    'Индия':    ['india', 'delhi', 'hindustan'],
    'Германия': ['germany', 'berlin', 'dw', 'spiegel'],
    'Франция':  ['france', 'paris', 'france 24'],
    'Ближний Восток': ['iran', 'iraq', 'syria', 'qatar', 'arab', 'al arabiya', 'aljazeera'],
}
EVENT_TOPICS = {
    'Музыка': ['music', 'concert', 'song', 'album', 'duet', 'popstar', 'музыка', 'песня', 'концерт'],
    'Политика': ['politics', 'president', 'minister', 'reform', 'закон', 'политика'],
    'Экономика': ['economy', 'finance', 'bank', 'рынок', 'экономика'],
    'Скандал': ['scandal', 'investigation', 'расследование', 'скандал', 'corruption'],
    'Война': ['war', 'attack', 'army', 'война', 'удар', 'армия'],
    'Технологии': ['tech', 'startup', 'ai', 'robot', 'технологии', 'ai'],
    'Спорт': ['sport', 'match', 'game', 'чемпионат', 'спорт'],
}
EMOJI_TOPICS = {
    'США': '🇺🇸', 'Великобритания': '🇬🇧', 'Израиль': '🇮🇱', 'Россия': '🇷🇺',
    'Китай': '🇨🇳', 'Япония': '🇯🇵', 'Индия': '🇮🇳', 'Германия': '🇩🇪', 'Франция': '🇫🇷', 'Ближний Восток': '🌍',
    'Музыка': '🎵', 'Политика': '🏛️', 'Экономика': '💰', 'Скандал': '💥', 'Война': '💣', 'Технологии': '🤖', 'Спорт': '🏅'
}

def extract_tags(text):
    tags, emojis = [], []
    text_l = text.lower()
    # Страна
    for topic, keys in COUNTRY_TOPICS.items():
        if any(k in text_l for k in keys):
            tags.append(f"#{topic.replace(' ', '')}")
            emojis.append(EMOJI_TOPICS.get(topic, '🌍'))
    # Тип события
    for topic, keys in EVENT_TOPICS.items():
        if any(k in text_l for k in keys):
            tags.append(f"#{topic}")
            emojis.append(EMOJI_TOPICS.get(topic, '✨'))
    # Базовые теги
    tags.append("#НОВА_главное")
    if not emojis:
        emojis.append("🌏")
    return tags, emojis

def google_translate(text, api_key):
    url = "https://translation.googleapis.com/language/translate/v2"
    params = {"q": text, "target": "ru", "format": "text", "key": api_key}
    response = requests.post(url, data=params)
    if response.status_code == 200:
        res = response.json()
        return res["data"]["translations"][0]["translatedText"]
    return None

def yandex_translate(text, api_key, folder_id):
    url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
    headers = {"Content-Type": "application/json", "Authorization": f"Api-Key {api_key}"}
    body = {"targetLanguageCode": "ru", "texts": [text], "folderId": folder_id}
    response = requests.post(url, headers=headers, json=body)
    if response.status_code == 200:
        res = response.json()
        return res["translations"][0]["text"]
    return None

def summarize_and_translate(title, summary, link):
    prompt = (
        f"Вот заголовок и краткое описание новости на английском:\n\n"
        f"Title: {title}\n"
        f"Summary: {summary}\n\n"
        f"1. Сформулируй пост для Telegram на русском языке: коротко, понятно, живо, 2–3 предложения.\n"
        f"2. Пост не должен быть калькой английского, а читаться как настоящая новость для русскоязычных.\n"
        f"3. Не пиши 'заголовок' и 'summary', просто новостной пост.\n"
        f"4. Не добавляй источники в текст, только в ссылке в конце.\n"
        f"5. Не используй больше 350 знаков.\n"
        f"6. Итог: только сам текст новости для Telegram, максимум конкретики и ясности."
    )
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты опытный редактор новостных Telegram-каналов, пиши живо и по-русски."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=256,
            temperature=0.6,
        )
        text = response.choices[0].message.content.strip()
    except Exception:
        text = None
    if not text:
        try:
            text_to_translate = f"{title}\n\n{summary}" if summary else title
            text = google_translate(text_to_translate, GOOGLE_KEY)
        except Exception:
            text = None
    if not text:
        try:
            text_to_translate = f"{title}\n\n{summary}" if summary else title
            text = yandex_translate(text_to_translate, YANDEX_KEY, YANDEX_FOLDER_ID)
        except Exception:
            text = None
    if not text:
        text = f"{title}\n\n{summary}"

    tags, emojis = extract_tags(f"{title} {summary}")
    hashtags = ' '.join(tags)
    emojis = ' '.join(emojis)
    return f"{emojis}\n{text}\n\n{hashtags}\n"

def extract_image(entry):
    # ищет картинку в rss
    if hasattr(entry, 'media_content'):
        for m in entry.media_content:
            if 'url' in m:
                return m['url']
    if hasattr(entry, 'links'):
        for link in entry.links:
            if link.type and 'image' in link.type:
                return link.href
    if hasattr(entry, 'image') and entry.image and 'href' in entry.image:
        return entry.image['href']
    return None

def post_news(app, channel_id, max_news=3, filter_tag=None):
    global posted_links
    count = 0
    for rss_url in RSS_FEEDS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            for entry in feed.entries:
                if entry.link in posted_links:
                    continue
                title = entry.title
                summary = entry.summary if hasattr(entry, "summary") else ""
                link = entry.link
                tags, _ = extract_tags(f"{title} {summary}")
                if filter_tag and filter_tag not in tags:
                    continue
                summary_ru = summarize_and_translate(title, summary, link)
                news_text = f"{summary_ru}\n{link}"

                post_id = short_id(entry.link)
                image_url = extract_image(entry)

                # Красивая кнопка "Подробнее" + подписка на тему
                from pyrogram.types import InlineKeyboardButton
                main_tag = tags[0] if tags else "Мир"
                buttons = [
                    [InlineKeyboardButton("📰 Подробнее", url=link)],
                    [InlineKeyboardButton("🔔 Подписаться на тему", callback_data=f"subscribe:{main_tag}")]
                    
                ]
                reply_markup = get_reactions_keyboard(post_id, extra_buttons=buttons)

                if image_url:
                    app.send_photo(
                        channel_id,
                        photo=image_url,
                        caption=news_text,
                        reply_markup=reply_markup
                    )
                else:
                    app.send_message(
                        channel_id,
                        news_text,
                        reply_markup=reply_markup
                    )

                posted_links.add(link)
                count += 1
                if count >= max_news:
                    save_posted_links(posted_links)
                    print(f"Опубликовано {count} новостей.")
                    return
    save_posted_links(posted_links)
    if count == 0:
        print("Свежих новостей не найдено.")

def run_autoposting(app, channel_id):
    print("Автопостинг с реакциями и апгрейдами запущен!")
    post_news(app, channel_id, max_news=3)
    schedule.every(10).minutes.do(post_news, app, channel_id, max_news=3)
    while True:
        schedule.run_pending()
        time.sleep(1)

def get_stats():
    tag_counts = {}
    for rss_url in RSS_FEEDS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            for entry in feed.entries:
                title = entry.title
                summary = entry.summary if hasattr(entry, "summary") else ""
                tags, _ = extract_tags(f"{title} {summary}")
                for t in tags:
                    tag_counts[t] = tag_counts.get(t, 0) + 1
    stats = "\n".join([f"{k}: {v}" for k, v in sorted(tag_counts.items(), key=lambda x: -x[1])])
    return f"Статистика по темам:\n{stats or 'Недостаточно данных.'}"
# Поиск новостей по тегу
def get_news_by_tag(tag, posted_links, max_news=3):
    results = []
    tag_l = tag.lower()
    for rss_url in RSS_FEEDS:
        feed = feedparser.parse(rss_url)
        if feed.entries:
            for entry in feed.entries:
                if entry.link in posted_links:
                    continue
                title = entry.title
                summary = entry.summary if hasattr(entry, "summary") else ""
                tags, _ = extract_tags(f"{title} {summary}")
                if any(tag_l in t.lower() for t in tags):
                    summary_ru = summarize_and_translate(title, summary, entry.link)
                    news_text = f"{summary_ru}\n\n{entry.link}" if entry.link not in summary_ru else summary_ru
                    results.append((news_text, entry.link))
                    if len(results) >= max_news:
                        return results
    return results
