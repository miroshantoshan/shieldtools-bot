# ShieldTools

![Language](https://img.shields.io/badge/language-Russian%20only-blue)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![Telegram](https://img.shields.io/badge/platform-Telegram-26A5E4)
![Status](https://img.shields.io/badge/status-active-success)

ShieldTools - это Telegram-бот с набором инструментов для базовой проверки цифровой безопасности. Бот умеет анализировать подозрительные сообщения, проверять сайты, домены, IP-адреса, email и файлы, а также генерировать пароли и шифровать документы.

## Возможности

- анализ SMS и сообщений на признаки мошенничества с помощью ИИ;
- локальная проверка сообщений по ключевым признакам, если ИИ-сервисы недоступны;
- генерация и оценка надёжности паролей;
- получение DNS-записей, возраста домена и данных SSL-сертификата;
- определение типа, местоположения, провайдера и ASN IP-адреса;
- проверка сайта по Google Safe Browsing;
- проверка домена по реестру блокировок;
- антивирусная проверка файлов через Kaspersky OpenTIP;
- просмотр размера файла;
- проверка email по DNS и спам-базе;
- получение IP-адресов почтового домена;
- шифрование и расшифровка файлов с помощью AES-256-GCM.

## Стек

- Python 3.10+
- aiogram 3
- python-dotenv
- cryptography
- Telegram Bot API

Для внешних проверок используются Google DNS, RDAP, ipwho.is, Google Safe Browsing, 2IP, Kaspersky OpenTIP и Stop Forum Spam. Анализ сообщений поддерживает OpenRouter, Gemini, Mistral, Hugging Face и Groq.

## Установка

1. Клонируйте репозиторий и перейдите в папку проекта:

   ```bash
   git clone <URL-репозитория>
   cd <папка-проекта>
   ```

2. Создайте и активируйте виртуальное окружение:

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

   Для Windows:

   ```powershell
   .venv\Scripts\activate
   ```

3. Установите зависимости:

   ```bash
   pip install -r requirements.txt
   ```

4. Создайте файл `.env` на основе примера:

   ```bash
   cp .env.example .env
   ```

5. Укажите токен Telegram-бота и необходимые API-ключи:

   ```env
   TG_BOT_TOKEN=

   GOOGLE_SAFE_BROWSING_API_KEY=
   TWO_IP_API_TOKEN=
   KASPERSKY_OPENTIP_API_KEY=

   OPENROUTER_API_KEY=
   GROQ_API_KEY=
   GEMINI_API_KEY=
   MISTRAL_API_KEY=
   HUGGINGFACE_API_KEY=
   ```

`TG_BOT_TOKEN` обязателен для запуска. Остальные ключи нужны только для соответствующих функций. Для ИИ-анализа достаточно указать ключ хотя бы одного провайдера; если все провайдеры недоступны, бот использует локальную проверку.

## Запуск

```bash
python main.py
```

После запуска откройте бота в Telegram и отправьте команду `/start`.

## Структура проекта

```text
.
├── main.py          # обработчики Telegram и инструменты проверок, основной файл
├── ai_services.py   # подключение ИИ
├── prompts.py       # промпты и правила анализа сообщений
├── keyboards.py     # клавиатуры и кнопки бота
├── crypto_files.py  # шифрование и расшифровка файлов
├── images/          # изображения разделов интерфейса
├── requirements.txt # необходимые зависимости
└── .env.example.    # пример создания env документа
```

## Шифрование файлов

Для файлов используется алгоритм AES-256-GCM. Ключ создаётся из пароля с помощью Scrypt, а зашифрованный файл получает расширение `.shield`.

Пароль нигде не хранится и не восстанавливается. Если пароль потерян, расшифровать файл невозможно.

## Важно

Результаты автоматических проверок и ответы ИИ могут содержать ошибки. ShieldTools является вспомогательным инструментом и не гарантирует полную безопасность сайта, файла, сообщения или email-адреса.

