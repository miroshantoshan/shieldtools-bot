import base64
import json
import os
import subprocess
import urllib.request
import uuid

import numpy as np
import onnxruntime as ort
from dotenv import load_dotenv


load_dotenv()


MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "aasist-l.onnx")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
SESSION = None


def get_session():
    global SESSION
    if SESSION is None:
        SESSION = ort.InferenceSession(MODEL_PATH, providers=["CPUExecutionProvider"])
    return SESSION


def get_wav(data):
    result = subprocess.run(
        [
            "ffmpeg", "-loglevel", "error", "-i", "pipe:0", "-f", "f32le",
            "-acodec", "pcm_f32le", "-ac", "1", "-ar", "16000", "pipe:1",
        ],
        input=data,
        capture_output=True,
        timeout=20,
    )
    if result.returncode or not result.stdout:
        raise ValueError("Не удалось прочитать голосовое")
    wav = np.frombuffer(result.stdout, dtype=np.float32)
    if len(wav) < 1600:
        raise ValueError("Голосовое слишком короткое")
    if len(wav) < 64600:
        wav = np.tile(wav, 64600 // len(wav) + 1)
    return wav[:64600].reshape(1, 64600)


def check_voice(data):
    wav = get_wav(data)
    logits = get_session().run(None, {"wav": wav})[0][0]
    chances = np.exp(logits - np.max(logits))
    fake = float(chances[0] / chances.sum())
    risk = "high" if fake >= 0.85 else "medium" if fake >= 0.65 else "low"
    return {"fake": round(fake * 100), "risk": risk}


def make_part(name, value, boundary, filename=None, content_type=None):
    part = f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\""
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
    with urllib.request.urlopen(request, timeout=25) as response:
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
        "generationConfig": {"temperature": 0},
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
    with urllib.request.urlopen(request, timeout=25) as response:
        result = json.loads(response.read().decode("utf-8"))
    return result["candidates"][0]["content"]["parts"][0]["text"].strip()


def transcribe_voice(data):
    try:
        return transcribe_groq(data)
    except Exception:
        return transcribe_gemini(data)
