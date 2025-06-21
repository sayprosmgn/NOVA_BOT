import openai
from main_news_bot.config import OPENAI_KEY

openai.api_key = OPENAI_KEY

def summarize_text_auto(text):
    try:
        completion = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Ты новостной редактор. Кратко, интересно перескажи новость на русском языке (2-3 предложения, не повторяя заголовок, не копируя источник)."},
                {"role": "user", "content": text}
            ],
            max_tokens=180,
            temperature=0.7,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        return f"❗ Ошибка AI: {e}"
