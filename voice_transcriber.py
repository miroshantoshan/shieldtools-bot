import base64
import json
import os
import urllib.request
import uuid

from dotenv import load_dotenv


load_dotenv()


GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def make_part(name, value, granica, filename=None, content_type=None):
    part = f"--{granica}\r\nContent-Disposition: form-data; name=\"{name}\""
    if filename:
        part += f"; filename=\"{filename}\""
    part += "\r\n"
    if content_type:
        part += f"Content-Type: {content_type}\r\n"
    return part.encode() + b"\r\n" + value + b"\r\n"


def transcribe_groq(data):
    if not GROQ_API_KEY:
        raise ValueError("Groq key is empty")
    granica = "----shield" + uuid.uuid4().hex
    body = b"".join([
        make_part("model", b"whisper-large-v3-turbo", granica),
        make_part("response_format", b"json", granica),
        make_part("file", data, granica, "voice.ogg", "audio/ogg"),
        f"--{granica}--\r\n".encode(),
    ])
    request = urllib.request.Request(
        "https://api.groq.com/openai/v1/audio/transcriptions",
        data=body,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": f"multipart/form-data; boundary={granica}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result.get("text", "").strip()


def transcribe_gemini(data):
    if not GEMINI_API_KEY:
        return ""
    body = {
        "contents": [{
            "parts": [
                {"text": "Распознай речь. Верни только точный текст без пояснений."},
                {"inline_data": {
                    "mime_type": "audio/ogg",
                    "data": base64.b64encode(data).decode("ascii"),
                }},
            ]
        }],
        "generationConfig": {
            "temperature": 0,
            "thinkingConfig": {"thinkingBudget": 0},
        },
    }
    request = urllib.request.Request(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "x-goog-api-key": GEMINI_API_KEY,
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def transcribe_voice(data):
    try:
        return transcribe_groq(data)
    except Exception:
        return transcribe_gemini(data)
