from pyrogram.types import Message
from auto_poster import (
    RSS_FEEDS, posted_links, summarize_and_translate, extract_tags,
    get_stats, get_news_by_tag
)
import feedparser

def register_general_handlers(app):
    @app.on_message()
    def handle_message(client, message: Message):
        if not message.text:
            return

        text = message.text.strip().lower()

        if text == "/start":
            message.reply(
                "Привет! Я умный новостной бот.\n"
                "Команды:\n"
                "/новость — свежий дайджест\n"
                "/тег <название> — новости по теме\n"
                "/стат — топ темы\n"
                "/теги — примеры тегов\n"
                "/help — помощь"
            )
        elif text in ["/help", "/помощь"]:
            message.reply(
                "Доступные команды:\n"
                "/start — начать\n"
                "/новость — получить свежую новость\n"
                "/тег <название> — новости по теме\n"
                "/стат — топ темы\n"
                "/теги — примеры тегов\n"
                "/help — помощь"
            )
        elif text.startswith("/новость"):
            for rss_url in RSS_FEEDS:
                feed = feedparser.parse(rss_url)
                if feed.entries:
                    for entry in feed.entries:
                        if entry.link in posted_links:
                            continue
                        title = entry.title
                        summary = entry.summary if hasattr(entry, "summary") else ""
                        link = entry.link
                        summary_ru = summarize_and_translate(title, summary, link)
                        news_text = f"{summary_ru}\n\n{link}" if link not in summary_ru else summary_ru
                        message.reply(news_text)
                        posted_links.add(link)
                        return
            message.reply("Свежих новостей не найдено. Попробуйте позже!")
        elif text.startswith("/тег "):
            tag = message.text[5:].strip()
            result = get_news_by_tag(tag, posted_links)
            if result:
                for news_text, link in result:
                    message.reply(f"{news_text}\n\n{link}")
            else:
                message.reply("По такому тегу пока нет свежих новостей.")
        elif text == "/стат":
            stats = get_stats()
            message.reply(stats)
        elif text == "/теги":
            tags, _ = extract_tags("usa britain israel russia china india france germany")
            message.reply("Примеры тегов для поиска:\n" + " ".join(tags))
        else:
            message.reply("Я понимаю только команды: /start, /help, /новость, /стат, /теги, /тег <название>")
