import json
import os
import re
import urllib.request

from dotenv import load_dotenv

from prompts import LOCAL_KEYWORDS, REASONS, RECOMMENDATIONS, SYSTEM_PROMPT


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


def make_ai_data(text, model):
    return {
        "model": model,
        "temperature": 0,
        "response_format": {"type": "json_object"},
        "messages": [
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": f'''Проверь это сообщение на скам:
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


def ask_openrouter(text):
    check_api_key(OPENROUTER_API_KEY)
    data = make_ai_data(text, "meta-llama/llama-3.3-70b-instruct:free")

    return send_ai_request(
        "https://openrouter.ai/api/v1/chat/completions",
        OPENROUTER_API_KEY,
        data,
        {
            "HTTP-Referer": "http://localhost",
            "X-Title": "IB Telegram Bot",
        },
    )


def ask_gemini(text):
    check_api_key(GEMINI_API_KEY)
    prompt = f'''{SYSTEM_PROMPT}

Проверь это сообщение на скам:
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


def ask_mistral(text):
    check_api_key(MISTRAL_API_KEY)
    data = make_ai_data(text, "mistral-small-latest")
    return send_ai_request(
        "https://api.mistral.ai/v1/chat/completions",
        MISTRAL_API_KEY,
        data,
    )


def ask_huggingface(text):
    check_api_key(HUGGINGFACE_API_KEY)
    data = make_ai_data(text, "Qwen/Qwen2.5-7B-Instruct")
    return send_ai_request(
        "https://router.huggingface.co/v1/chat/completions",
        HUGGINGFACE_API_KEY,
        data,
    )


def ask_groq(text):
    check_api_key(GROQ_API_KEY)
    data = make_ai_data(text, "llama-3.1-8b-instant")
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
