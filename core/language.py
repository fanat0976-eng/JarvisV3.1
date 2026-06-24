"""
Language detection and multilingual support for Jarvis V3.1.
Detects language of user query, provides multilingual system prompts.
"""
import re
from typing import Optional


# Language patterns for detection
_LANG_PATTERNS = {
    "ru": {
        "chars": re.compile(r'[а-яА-ЯёЁ]'),
        "words": {"привет", "как", "что", "где", "когда", "почему", "покажи", "сделай",
                  "найди", "объясни", "расскажи", "пожалуйста", "спасибо", "да", "нет",
                  "я", "ты", "мы", "он", "она", "вы", "мне", "тебе", "ему", "ей",
                  "этот", "этого", "этой", "весь", "вся", "всё", "мой", "твой", "наш"},
    },
    "en": {
        "chars": re.compile(r'[a-zA-Z]'),
        "words": {"hello", "how", "what", "where", "when", "why", "please", "thank",
                  "yes", "no", "the", "is", "are", "was", "were", "have", "has",
                  "can", "could", "would", "should", "will", "shall", "do", "does",
                  "this", "that", "these", "those", "my", "your", "his", "her", "our"},
    },
    "kz": {
        "chars": re.compile(r'[әғүұқңөіҺәғүұқңөі]'),
        "words": {"сәлем", "қалай", "не", "қайда", "қашан", "неліктен", "көрсет",
                  "жаса", "тап", "айт", "өтінемін", "рақмет", "иә", "жоқ",
                  "мен", "сен", "ол", "біз", "сіз", "олар", "бұл", "сол",
                  "әкем", "әпкем", "досым", "үй", "мектеп", "жұмыс"},
    },
}

# System prompts per language
SYSTEM_PROMPTS = {
    "ru": """Ты Jarvis — персональный AI-ассистент и мыслящий помощник.

ПРАВИЛА ОБЩЕНИЯ:
- Отвечай кратко, по делу, без воды
- Используй язык пользователя
- Если не уверен — скажи прямо, не придумывай
- Не предлагай лишнего, жди явного запроса
- После выполнения задачи — краткий итог
- При ошибках — объясни причину и предложи решение

ФОРМАТ ОТВЕТОВ:
- Обычные вопросы: 1-3 предложения
- Технические задачи: код + краткое объяснение
- Анализ: структурированный ответ с пунктами""",

    "en": """You are Jarvis — a personal AI assistant and thinking helper.

COMMUNICATION RULES:
- Be concise, on point, no fluff
- Use the user's language
- If unsure — say so directly, don't make things up
- Don't offer extra, wait for explicit requests
- After completing a task — brief summary
- On errors — explain the cause and suggest a solution

RESPONSE FORMAT:
- Regular questions: 1-3 sentences
- Technical tasks: code + brief explanation
- Analysis: structured response with bullet points""",

    "kz": """Сен Jarvis — жеке көмекші AI және ойлаушы көмекшісің.

СӨЙЛЕСУ ЕРЕЖЕЛЕРІ:
- Қысқа, нақты, артық сөзсіз
- Қолданушының тілін қолдан
- Сенімсіз болсаң — тіке айт, ойлап таппа
- Артық ұсынба, нақты сұрау күт
- Тапсырманы орындағаннан кейін — қысқа қорытынды
- Қателерде — себебін түсіндіріп, шешім ұсын

ЖАУАП ФОРМАТЫ:
- Қарапайым сұрақтар: 1-3 сөйлем
- Техникалық тапсырмалар: код + қысқа түсіндірме
- Талдау: нүктелермен құрылымдалған жауап""",
}

# Greeting responses per language
GREETINGS = {
    "ru": "Привет! Я Jarvis. Чем могу помочь?",
    "en": "Hello! I'm Jarvis. How can I help you?",
    "kz": "Сәлем! Мен Jarvis. Қалай көмектесе аламын?",
}

# Language names
LANG_NAMES = {
    "ru": "Русский",
    "en": "English",
    "kz": "Қазақ тілі",
}


def detect_language(text: str) -> str:
    """Detect the language of a text string.
    
    Returns: 'ru', 'en', 'kz', or 'en' as default.
    """
    if not text or not text.strip():
        return "en"

    text_lower = text.lower()
    words = set(re.findall(r'\w+', text_lower))

    scores = {}
    for lang, patterns in _LANG_PATTERNS.items():
        score = 0
        # Character match
        char_matches = len(patterns["chars"].findall(text))
        score += char_matches * 2

        # Word match
        word_matches = len(words & patterns["words"])
        score += word_matches * 5

        scores[lang] = score

    if not scores:
        return "en"

    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "en"

    return best


def get_system_prompt(language: Optional[str] = None, query: str = "") -> str:
    """Get system prompt for the detected or specified language.
    
    If language is not specified, detects from query.
    """
    if not language:
        language = detect_language(query)

    return SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])


def get_greeting(language: Optional[str] = None) -> str:
    """Get a greeting in the specified language."""
    return GREETINGS.get(language or "en", GREETINGS["en"])


def get_supported_languages() -> list[dict]:
    """Get list of supported languages."""
    return [
        {"code": code, "name": name}
        for code, name in LANG_NAMES.items()
    ]
