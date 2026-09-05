import html
import json
import os
import re
import urllib.parse
import urllib.request

from dotenv import load_dotenv

from prompts import (
    FILE_REASONS,
    FILE_RECOMMENDATIONS,
    FILE_SYSTEM_PROMPT,
    LOCAL_KEYWORDS,
    REASONS,
    RECOMMENDATIONS,
    SITE_REASONS,
    SITE_RECOMMENDATIONS,
    SITE_SYSTEM_PROMPT,
    SYSTEM_PROMPT,
)


load_dotenv()


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY", "")


def make_answer(data):
    verdict = data.get("verdict")
    reason_codes = data.get("reason_codes", [])

    if not isinstance(reason_codes, list):
        reason_codes = ["no_clear_signs"]

    reason_codes = [code for code in reason_codes if code in REASONS]

    if not reason_codes:
        reason_codes = ["no_clear_signs"]

    if verdict != "scam":
        verdict = "not_scam"
        reason_codes = ["no_clear_signs"]

    if verdict == "scam":
        first_line = "<b><i>Да, это определённо мошенники.</i></b>"
    else:
        first_line = "<b><i>Нет, это не похоже на мошенников.</i></b>"

    answer = f'''{first_line}

<b>Почему:</b>
'''
    for code in reason_codes[:4]:
        answer += f'''- {REASONS[code]}
'''

    answer += '''
<b>Рекомендации:</b>
'''
    for code in reason_codes[:4]:
        answer += f'''- {RECOMMENDATIONS[code]}
'''

    answer += '''
<u><i>Этот ответ был дан ИИ, она может ошибаться.</i></u>'''
    return answer


def get_json_from_text(text):
    text = text.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{.*\}", text, re.DOTALL)

    if match:
        text = match.group(0)

    return json.loads(text)


def check_api_key(api_key):
    if not api_key:
        raise ValueError("API key is empty")


def make_ai_data(text, model, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": f'''{task}
{text}''',
            },
        ],
    }


def send_ai_request(url, api_key, data, extra_headers=None):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    if extra_headers:
        headers.update(extra_headers)

    request = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    model_text = result["choices"][0]["message"]["content"]
    return get_json_from_text(model_text)


def ask_openrouter(text, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    check_api_key(OPENROUTER_API_KEY)
    data = make_ai_data(text, "openrouter/free", system_prompt, task)

    return send_ai_request(
        "https://openrouter.ai/api/v1/chat/completions",
        OPENROUTER_API_KEY,
        data,
        {
            "HTTP-Referer": "http://localhost",
            "X-Title": "IB Telegram Bot",
        },
    )


def ask_gemini(text, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    check_api_key(GEMINI_API_KEY)
    prompt = f'''{system_prompt}

{task}
{text}'''
    data = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                ],
            },
        ],
        "generationConfig": {
            "temperature": 0,
            "response_mime_type": "application/json",
        },
    }

    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        result = json.loads(response.read().decode("utf-8"))

    model_text = result["candidates"][0]["content"]["parts"][0]["text"]
    return get_json_from_text(model_text)


def ask_mistral(text, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    check_api_key(MISTRAL_API_KEY)
    data = make_ai_data(text, "mistral-small-latest", system_prompt, task)
    return send_ai_request(
        "https://api.mistral.ai/v1/chat/completions",
        MISTRAL_API_KEY,
        data,
    )


def ask_huggingface(text, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    check_api_key(HUGGINGFACE_API_KEY)
    data = make_ai_data(text, "Qwen/Qwen2.5-7B-Instruct", system_prompt, task)
    return send_ai_request(
        "https://router.huggingface.co/v1/chat/completions",
        HUGGINGFACE_API_KEY,
        data,
    )


def ask_groq(text, system_prompt=SYSTEM_PROMPT, task="Проверь это сообщение на скам:"):
    check_api_key(GROQ_API_KEY)
    data = make_ai_data(text, "llama-3.1-8b-instant", system_prompt, task)
    return send_ai_request(
        "https://api.groq.com/openai/v1/chat/completions",
        GROQ_API_KEY,
        data,
    )


def check_local(text):
    text = text.lower()
    reason_codes = []

    for code, keywords in LOCAL_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            reason_codes.append(code)

    if reason_codes:
        return {"verdict": "scam", "reason_codes": reason_codes}

    return {"verdict": "not_scam", "reason_codes": ["no_clear_signs"]}


def analyze_message(text):
    providers = [
        ("OpenRouter", ask_openrouter),
        ("Gemini", ask_gemini),
        ("Mistral", ask_mistral),
        ("Hugging Face", ask_huggingface),
        ("Groq", ask_groq),
    ]

    for name, function in providers:
        try:
            data = function(text)
            return make_answer(data)
        except Exception:
            pass

    return make_answer(check_local(text))


def check_site_local(url, reputation_status="unknown"):
    if reputation_status == "dangerous":
        return {"verdict": "dangerous", "reason_codes": ["known_threat"]}

    domain = urllib.parse.urlparse(url).hostname or ""
    reason_codes = []
    suspicious_words = ["login", "verify", "bonus", "gift", "secure", "account", "bank"]
    short_domains = ["bit.ly", "tinyurl.com", "t.co", "goo.gl", "clck.ru"]

    if domain in short_domains:
        reason_codes.append("short_link")
    if any(word in domain.lower() for word in suspicious_words):
        reason_codes.append("suspicious_words")
    if domain.startswith("xn--") or domain.count("-") >= 3:
        reason_codes.append("strange_domain")

    if reason_codes:
        return {"verdict": "dangerous", "reason_codes": reason_codes}

    if reputation_status == "safe":
        return {"verdict": "safe", "reason_codes": ["no_clear_signs"]}

    return {"verdict": "unknown", "reason_codes": ["check_failed"]}


def make_site_answer(data, url, reputation_status="unknown", source="локальная проверка"):
    verdict = data.get("verdict")
    reason_codes = data.get("reason_codes", [])

    if not isinstance(reason_codes, list):
        reason_codes = []

    reason_codes = [code for code in reason_codes if code in SITE_REASONS]

    if reputation_status == "dangerous":
        verdict = "dangerous"
        reason_codes = ["known_threat"]
    elif verdict == "safe":
        verdict = "safe"
        reason_codes = ["no_clear_signs"]
    elif verdict == "dangerous" and not reason_codes:
        reason_codes = ["strange_domain"]
    elif verdict != "dangerous":
        verdict = "unknown"
        reason_codes = ["check_failed"]

    if verdict == "dangerous":
        first_line = "<b><i>Сайт выглядит опасно.</i></b>"
        style = "danger"
    elif verdict == "safe":
        first_line = "<b><i>Явных угроз не найдено.</i></b>"
        style = "success"
    else:
        first_line = "<b><i>Безопасность сайта не подтверждена.</i></b>"
        style = "danger"

    answer = f'''{first_line}

<b>Сайт:</b> <code>{html.escape(url)}</code>
<b>Источник:</b> <code>{html.escape(source)}</code>

<b>Почему:</b>
'''
    for code in reason_codes[:3]:
        answer += f'''- {SITE_REASONS[code]}
'''

    answer += '''
<b>Рекомендации:</b>
'''
    for code in reason_codes[:3]:
        answer += f'''- {SITE_RECOMMENDATIONS[code]}
'''

    if source.startswith("ИИ"):
        answer += '''
<u><i>Этот ответ был дан ИИ, он может ошибаться.</i></u>'''
    else:
        answer += '''
<u><i>Результат получен без ИИ.</i></u>'''
    return answer, style


def analyze_site(url, reputation_status="unknown", reputation_text="Базы угроз недоступны"):
    text = f'''Ссылка: {url}
Результат репутационных баз: {reputation_text}.'''
    task = "Проверь ссылку и домен на вредоносность:"
    providers = [
        ("OpenRouter", ask_openrouter),
        ("Gemini", ask_gemini),
        ("Mistral", ask_mistral),
        ("Hugging Face", ask_huggingface),
        ("Groq", ask_groq),
    ]

    for name, function in providers:
        try:
            data = function(text, SITE_SYSTEM_PROMPT, task)
            source = f"ИИ ({name}); {reputation_text}"
            return make_site_answer(data, url, reputation_status, source)
        except Exception:
            pass

    data = check_site_local(url, reputation_status)
    source = f"локальная проверка; {reputation_text}"
    return make_site_answer(data, url, reputation_status, source)


def check_file_local(reputation_status):
    if reputation_status == "dangerous":
        return {"verdict": "dangerous", "reason_codes": ["known_malware"]}
    if reputation_status == "safe":
        return {"verdict": "safe", "reason_codes": ["clean_scan"]}
    return {"verdict": "unknown", "reason_codes": ["analysis_pending"]}


def make_file_answer(data, file_data, reputation_status, source):
    verdict = data.get("verdict")
    reason_codes = data.get("reason_codes", [])
    zone = file_data.get("zone", "")
    status = file_data.get("status", "")
    kaspersky_error = file_data.get("kaspersky_error", "")

    if not isinstance(reason_codes, list):
        reason_codes = []

    reason_codes = [code for code in reason_codes if code in FILE_REASONS]

    if reputation_status == "dangerous":
        verdict = "dangerous"
        if zone == "Red":
            reason_codes = ["known_malware"]
        else:
            reason_codes = ["suspicious_result"]
    elif reputation_status == "safe":
        verdict = "safe"
        reason_codes = ["clean_scan"]
    else:
        verdict = "unknown"
        if zone == "Grey" or status == "in progress":
            reason_codes = ["analysis_pending"]
        else:
            reason_codes = ["check_failed"]

    if verdict == "dangerous":
        first_line = "<b><i>Файл выглядит опасно.</i></b>"
        style = "danger"
    elif verdict == "safe":
        first_line = "<b><i>Явных угроз в файле не найдено.</i></b>"
        style = "success"
    else:
        first_line = "<b><i>Безопасность файла не подтверждена.</i></b>"
        style = "danger"

    if kaspersky_error:
        kaspersky_text = kaspersky_error
    elif status == "in progress" or zone == "Grey":
        kaspersky_text = "Grey - анализ ещё выполняется"
    else:
        kaspersky_text = zone or "нет ответа"

    answer = f'''{first_line}

<b>Файл:</b> <code>{html.escape(str(file_data.get("file_name", "без названия")))}</code>
<b>Размер:</b> <code>{html.escape(str(file_data.get("size", "не найдено")))}</code>
<b>Тип:</b> <code>{html.escape(str(file_data.get("mime_type", "не найдено")))}</code>
<b>Kaspersky:</b> <code>{html.escape(kaspersky_text)}</code>
<b>Источник:</b> <code>{html.escape(source)}</code>

<b>Почему:</b>
'''
    for code in reason_codes[:3]:
        answer += f'''- {FILE_REASONS[code]}
'''

    answer += '''
<b>Рекомендации:</b>
'''
    for code in reason_codes[:3]:
        answer += f'''- {FILE_RECOMMENDATIONS[code]}
'''

    sha256 = file_data.get("sha256", "")
    if sha256 and sha256 != "не найдено":
        answer += f'''
<b>SHA256:</b> <code>{html.escape(str(sha256))}</code>'''

    if source.startswith("ИИ"):
        answer += '''

<u><i>ИИ объяснил отчёт антивируса и может ошибаться.</i></u>'''
    else:
        answer += '''

<u><i>Результат получен без ИИ.</i></u>'''

    return answer, style


def analyze_file(file_data, reputation_status="unknown"):
    report_text = f'''Имя: {file_data.get("file_name", "не найдено")}
Размер: {file_data.get("size", "не найдено")}
MIME-тип: {file_data.get("mime_type", "не найдено")}
Зона Kaspersky: {file_data.get("zone", "нет ответа")}
Статус Kaspersky: {file_data.get("status", "не найдено")}
Статус файла: {file_data.get("file_status", "не найдено")}'''
    task = "Объясни результат антивирусной проверки файла:"
    providers = [
        ("OpenRouter", ask_openrouter),
        ("Gemini", ask_gemini),
        ("Mistral", ask_mistral),
        ("Hugging Face", ask_huggingface),
        ("Groq", ask_groq),
    ]

    for name, function in providers:
        try:
            data = function(report_text, FILE_SYSTEM_PROMPT, task)
            return make_file_answer(data, file_data, reputation_status, f"ИИ ({name}) + Kaspersky OpenTIP")
        except Exception:
            pass

    data = check_file_local(reputation_status)
    return make_file_answer(data, file_data, reputation_status, "Kaspersky OpenTIP + локальная проверка")
