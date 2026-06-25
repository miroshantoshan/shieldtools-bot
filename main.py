import asyncio
import html
import io
import ipaddress
import json
import os
import re
import secrets
import socket
import ssl
import string
import urllib.error
import urllib.parse
import urllib.request

from aiogram import Bot, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand, BufferedInputFile, CallbackQuery, FSInputFile, InputMediaPhoto, Message, ReplyKeyboardRemove
from dotenv import load_dotenv

from ai_services import analyze_message
from crypto_files import InvalidEncryptedFile, WrongPassword, decrypt_file, encrypt_file
from keyboards import (
    get_access_check_keyboard,
    get_access_checked_keyboard,
    get_back_keyboard,
    get_check_again_keyboard,
    get_crypto_menu_keyboard,
    get_crypto_result_keyboard,
    get_domains_menu_keyboard,
    get_email_menu_keyboard,
    get_files_menu_keyboard,
    get_generated_password_keyboard,
    get_ip_menu_keyboard,
    get_password_check_keyboard,
    get_password_length_keyboard,
    get_password_menu_keyboard,
    get_scam_menu_keyboard,
    get_checked_keyboard,
    get_site_menu_keyboard,
    get_understood_keyboard,
    get_wait_input_keyboard,
    get_wait_password_keyboard,
    menu,
)


load_dotenv()


tg_bot_token = os.getenv("TG_BOT_TOKEN", "")
dp = Dispatcher(storage=MemoryStorage())
EASTER_CLICKS = {}

SCAM_BUTTONS = ["Проверка SMS", "Проверка SMS", "🛡 Проверка SMS"]
PASSWORD_BUTTONS = ["Пароли", "🔐 Пароли"]
DOMAIN_BUTTONS = ["Домены", "🖥 Домены"]
IP_BUTTONS = ["IP", "📡 IP"]
SITE_BUTTONS = ["Проверка сайта", "🧭 Проверка сайта"]
FILE_BUTTONS = ["Файлы", "📁 Файлы"]
EMAIL_BUTTONS = ["Email", "📧 Email"]
CRYPTO_BUTTONS = ["Шифратор", "🔐 Шифратор"]
SCAM_CHECK_TEXT = '''<tg-emoji emoji-id="5219805369806629055">🛡</tg-emoji> Проверка на Скам

<tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте подозрительное сообщение, которое нужно проверить.

<tg-emoji emoji-id="6021451978993834164">🔎</tg-emoji> ShieldTools проанализирует его и покажет возможные признаки угрозы.'''

SCAM_WAIT_TEXT = '''<tg-emoji emoji-id="5877396173135811032">⌨</tg-emoji> <b>Введите подозрительное сообщение</b>

<i>Я проверю его и покажу возможные признаки угрозы.</i>'''

MAIN_IMAGE = "./images/main.png"
SCAM_IMAGE = "./images/scam.png"
ACCESS_IMAGE = "./images/access.png"
PASSWORD_IMAGE = "./images/passwords.png"
DOMAIN_IMAGE = "./images/domains.png"
IP_IMAGE = "./images/ip.png"
SITE_IMAGE = "./images/site.png"
FILE_IMAGE = "./images/files.png"
EMAIL_IMAGE = "./images/email.png"
CRYPTO_IMAGE = "./images/crypto.png"
TWO_IP_API_TOKEN = os.getenv("TWO_IP_API_TOKEN", "")
GOOGLE_SAFE_BROWSING_API_KEY = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY", "")
KASPERSKY_OPENTIP_API_KEY = os.getenv("KASPERSKY_OPENTIP_API_KEY", "")


class States(StatesGroup):
    waiting_scam_message = State()
    waiting_password = State()
    waiting_domain_check = State()
    waiting_domain_age = State()
    waiting_ssl_check = State()
    waiting_ip_check = State()
    waiting_site_rkn = State()
    waiting_site_virus = State()
    waiting_file_virus = State()
    waiting_file_size = State()
    waiting_email_spam = State()
    waiting_email_exists = State()
    waiting_email_ip = State()
    waiting_crypto_password = State()
    waiting_crypto_file = State()


def get_main_menu_text(user):
    return f'''<tg-emoji emoji-id="6023985511482268644">👋</tg-emoji> Привет, <b>{user.first_name}</b>

<tg-emoji emoji-id="6019328362479097179">🛡</tg-emoji> Добро пожаловать в <b><u>ShieldTools</u></b> - бота, в котором собраны основные инструменты для проверки данных.

<tg-emoji emoji-id="6023622161543993632">🧭</tg-emoji> <b>Выберите нужный раздел в меню ниже, чтобы начать работу.</b>'''

async def send_main_photo(message, text, reply_markup=None):
    try:
        await message.answer_photo(
            FSInputFile(MAIN_IMAGE),
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
    except Exception:
        try:
            await message.answer_photo(FSInputFile(MAIN_IMAGE))
        except Exception:
            pass

        await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )


async def send_section_photo(message, image, text, reply_markup=None):
    try:
        sent_message = await message.answer_photo(
            FSInputFile(image),
            caption=text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        return sent_message.message_id
    except Exception:
        sent_message = await message.answer(
            text,
            parse_mode="HTML",
            reply_markup=reply_markup,
        )
        return sent_message.message_id


async def edit_section_photo(message, image, text, reply_markup=None):
    try:
        await message.edit_media(
            InputMediaPhoto(
                media=FSInputFile(image),
                caption=text,
                parse_mode="HTML",
            ),
            reply_markup=reply_markup,
        )
        return message.message_id
    except Exception:
        try:
            await message.edit_caption(
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            return message.message_id
        except Exception:
            sent_message = await message.answer_photo(
                FSInputFile(image),
                caption=text,
                parse_mode="HTML",
                reply_markup=reply_markup,
            )
            return sent_message.message_id


def get_file_analysis_text(dots):
    return f'''<tg-emoji emoji-id="5334885140147479028">🔍</tg-emoji>  <b>Анализирую{dots}</b>'''


async def file_analysis_animation(message, stop_event):
    dots_list = ["", ".", "..", "...", "..", "."]
    number = 0

    while not stop_event.is_set():
        try:
            await message.edit_text(
                text=get_file_analysis_text(dots_list[number]),
                parse_mode="HTML",
            )
        except Exception:
            pass

        number += 1

        if number >= len(dots_list):
            number = 0

        await asyncio.sleep(0.35)


def get_crypto_progress_text(action, dots):
    if action == "encrypt":
        text = "Шифровка"
    else:
        text = "Расшифровка"

    return f'''<tg-emoji emoji-id="5334885140147479028">🔍</tg-emoji>  <b>{text}{dots}</b>'''


async def crypto_progress_animation(message, stop_event, action):
    dots_list = ["", ".", "..", "...", "..", "."]
    number = 0

    while not stop_event.is_set():
        try:
            await message.edit_text(
                text=get_crypto_progress_text(action, dots_list[number]),
                parse_mode="HTML",
            )
        except Exception:
            pass

        number = (number + 1) % len(dots_list)
        await asyncio.sleep(0.35)


async def save_wait_message(state, message, message_id):
    await state.update_data(
        chat_id=message.chat.id,
        message_id=message_id,
    )


@dp.message(F.text == "/start")
async def start(message: Message, state: FSMContext):
    await state.clear()

    remove_keyboard_message = await message.answer(
        "⁠",
        reply_markup=ReplyKeyboardRemove(),
    )

    try:
        await remove_keyboard_message.delete()
    except Exception:
        pass

    await send_section_photo(
        message,
        ACCESS_IMAGE,
        '''<b>Пройдите проверку</b>

<i>Чтобы открыть главное меню, нажмите кнопку ниже.</i>''',
        get_access_check_keyboard(),
    )


@dp.callback_query(F.data == "access_check")
async def access_check(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=get_access_checked_keyboard())
    await send_main_photo(
        callback.message,
        get_main_menu_text(callback.from_user),
        menu,
    )
    await callback.answer()


@dp.callback_query(F.data == "access_checked")
async def access_checked(callback: CallbackQuery):
    await callback.answer()


async def set_commands_menu(bot):
    bot_commands = [
        BotCommand(command="/start", description="Запуск бота"),
    ]
    await bot.set_my_commands(bot_commands)


@dp.message(F.text.in_(SCAM_BUTTONS))
async def scam_check(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        SCAM_IMAGE,
        SCAM_CHECK_TEXT,
        get_scam_menu_keyboard(),
    )


@dp.callback_query(F.data == "scam_start")
async def scam_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_scam_message)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        SCAM_IMAGE,
        SCAM_WAIT_TEXT,
        get_wait_input_keyboard("back_to_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.message(F.text.in_(PASSWORD_BUTTONS))
async def passwords(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        PASSWORD_IMAGE,
        '''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Раздел паролей</b>

<tg-emoji emoji-id="6023566962624306038">👇</tg-emoji> <i>Выберите действие ниже:</i>

<b>Генератор</b> создаст новый надёжный пароль.
<b>Проверка</b> оценит ваш пароль и даст рекомендации.''',
        get_password_menu_keyboard(),
    )


@dp.message(F.text.in_(DOMAIN_BUTTONS))
async def domains(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        DOMAIN_IMAGE,
        '''<b><tg-emoji emoji-id="6019462434178211398">🌐</tg-emoji> Домены</b>

<i>Выберите нужную проверку домена.</i>

<b>Домен</b> можно проверить на существование.
<b>Возраст</b> покажет дату регистрации, если она доступна.
<b>SSL</b> проверит сертификат сайта.''',
        get_domains_menu_keyboard(),
    )


@dp.message(F.text.in_(IP_BUTTONS))
async def ip_menu(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        IP_IMAGE,
        '''<b><tg-emoji emoji-id="6023778764641540987">📡</tg-emoji> IP</b>

<i>Здесь можно проверить IP-адрес.</i>

<i>Будет показано, корректный ли адрес и доступные о нём данные.</i>''',
        get_ip_menu_keyboard(),
    )


@dp.message(F.text.in_(SITE_BUTTONS))
async def site_menu(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        SITE_IMAGE,
        '''<b><tg-emoji emoji-id="6019098624678435283">🧭</tg-emoji> Проверка сайта</b>

<i>Выберите, что нужно проверить.</i>

<b>Блокировка РКН</b> проверит домен по реестру.
<b>Проверка на вредоносность</b> посмотрит подозрительные признаки ссылки.''',
        get_site_menu_keyboard(),
    )


@dp.message(F.text.in_(FILE_BUTTONS))
async def files_menu(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        FILE_IMAGE,
        '''<b><tg-emoji emoji-id="6021859047404214713">📁</tg-emoji> Файлы</b>

<i>Выберите проверку файла.</i>

<b>Вирусы</b> оценит файл по расширению и размеру.
<b>Размер</b> покажет вес файла.''',
        get_files_menu_keyboard(),
    )


@dp.message(F.text.in_(EMAIL_BUTTONS))
async def email_menu(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        EMAIL_IMAGE,
        '''<b><tg-emoji emoji-id="6019263620142078168">📧</tg-emoji> Email</b>

<i>Выберите проверку email.</i>

<b>Спам-базы</b> проверит адрес на наличие в базах.
<b>Существование</b> проверит формат и домен.
<b>IP по email</b> покажет IP-адреса домена почты.''',
        get_email_menu_keyboard(),
    )


@dp.message(F.text.in_(CRYPTO_BUTTONS))
async def crypto_menu_message(message: Message, state: FSMContext):
    await state.clear()
    await send_section_photo(
        message,
        CRYPTO_IMAGE,
        '''<b><tg-emoji emoji-id="6021738534916854774">🔐</tg-emoji> Шифратор файлов</b>

<i>Зашифруйте файл паролем или расшифруйте файл <code>.shield</code>.</i>

<b>Алгоритм:</b> AES-256-GCM.''',
        get_crypto_menu_keyboard(),
    )


@dp.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await send_main_photo(
        callback.message,
        get_main_menu_text(callback.from_user),
        menu,
    )
    await callback.answer()


@dp.callback_query(F.data == "passwords_menu")
async def passwords_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        PASSWORD_IMAGE,
        '''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Раздел паролей</b>

<tg-emoji emoji-id="6023566962624306038">👇</tg-emoji> <i>Выберите действие ниже:</i>

<b>Генератор</b> создаст надёжный пароль.
<b>Проверка</b> оценит ваш пароль и даст рекомендации.''',
        get_password_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "domains_menu")
async def domains_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        DOMAIN_IMAGE,
        '''<b><tg-emoji emoji-id="6019462434178211398">📱</tg-emoji> Домены</b>

<i>Выберите нужную проверку домена.</i>

<b>Домен</b> можно проверить на существование.
<b>Возраст</b> покажет дату регистрации, если она доступна.
<b>SSL</b> проверит сертификат сайта.''',
        get_domains_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "ip_menu")
async def ip_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        IP_IMAGE,
        '''<b><tg-emoji emoji-id="6023778764641540987">📡</tg-emoji> IP</b>

<i>Здесь можно проверить IP-адрес.</i>

<i>Я покажу, корректный ли адрес и какой у него тип.</i>''',
        get_ip_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "site_menu")
async def site_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        SITE_IMAGE,
        '''<b><tg-emoji emoji-id="6019098624678435283">🧭</tg-emoji> Проверка сайта</b>

<i>Выберите, что нужно проверить.</i>

<b>Блокировка РКН</b> проверит домен по реестру.
<b>Проверка на вредоносность</b> посмотрит подозрительные признаки ссылки.''',
        get_site_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "files_menu")
async def files_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        FILE_IMAGE,
        '''<b><tg-emoji emoji-id="6021375494216226506">📁</tg-emoji> Файлы</b>

<i>Выберите проверку файла.</i>

<b>Вирусы</b> оценит файл по расширению и размеру.
<b>Размер</b> покажет вес файла.''',
        get_files_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "email_menu")
async def email_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        EMAIL_IMAGE,
        '''<b><tg-emoji emoji-id="6019263620142078168">📧</tg-emoji> Email</b>

<i>Выберите проверку email.</i>

<b>Спам-базы</b> проверит адрес на наличие в базах.
<b>Существование</b> проверит формат и домен.
<b>IP по email</b> покажет IP-адреса домена почты.''',
        get_email_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "crypto_menu")
async def crypto_menu_callback(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        CRYPTO_IMAGE,
        '''<b><tg-emoji emoji-id="6021738534916854774">🔐</tg-emoji> Шифратор файлов</b>

<i>Выберите нужное действие.</i>''',
        get_crypto_menu_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "crypto_encrypt")
async def crypto_encrypt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_crypto_password)
    await state.update_data(crypto_mode="encrypt", crypto_algorithm="aes")
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        CRYPTO_IMAGE,
        '''<b><tg-emoji emoji-id="6019290828759898301">🔑</tg-emoji> Придумайте пароль</b>

<i>Отправьте пароль длиной от 8 до 128 символов.</i>

<b>Важно:</b> без этого пароля файл нельзя будет восстановить.''',
        get_wait_input_keyboard("crypto_menu"),
    )
    await callback.answer()


@dp.callback_query(F.data == "crypto_decrypt")
async def crypto_decrypt(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_crypto_password)
    await state.update_data(crypto_mode="decrypt")
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        CRYPTO_IMAGE,
        '''<b><tg-emoji emoji-id="6019290828759898301">🔑</tg-emoji> Пароль для расшифровки</b>

<i>Отправьте пароль, которым был защищён файл.</i>''',
        get_wait_input_keyboard("crypto_menu"),
    )
    await callback.answer()


@dp.callback_query(F.data == "domain_check")
async def domain_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_domain_check)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        DOMAIN_IMAGE,
        '''<b><tg-emoji emoji-id="6021607757457660145">🖥</tg-emoji> Проверка домена</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте домен без лишнего текста.</i>

<b>Например:</b> <code>example.com</code>''',
        get_wait_input_keyboard("domains_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "domain_age")
async def domain_age(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_domain_age)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        DOMAIN_IMAGE,
        '''<b><tg-emoji emoji-id="6023880246128810031">📅</tg-emoji> Возраст домена</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте домен, возраст которого нужно проверить.</i>

<b>Например:</b> <code>example.com</code>''',
        get_wait_input_keyboard("domains_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "ssl_check")
async def ssl_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_ssl_check)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        DOMAIN_IMAGE,
        '''<b><tg-emoji emoji-id="6021738534916854774">🔐</tg-emoji> Проверка SSL</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте домен сайта.</i>

<b>Например:</b> <code>example.com</code>''',
        get_wait_input_keyboard("domains_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "ip_check")
async def ip_check(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_ip_check)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        IP_IMAGE,
        '''<b><tg-emoji emoji-id="6023778764641540987">📡</tg-emoji> Проверка IP</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте IP-адрес.</i>

<b>Например:</b> <code>8.8.8.8</code>''',
        get_wait_input_keyboard("ip_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "site_rkn")
async def site_rkn(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_site_rkn)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        SITE_IMAGE,
        '''<b><tg-emoji emoji-id="6030789912205204974">🚫</tg-emoji> Проверка РКН</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте домен сайта.</i>

<b>Например:</b> <code>example.com</code>''',
        get_wait_input_keyboard("site_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "site_virus")
async def site_virus(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_site_virus)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        SITE_IMAGE,
        '''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка сайта на вредоносность</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте ссылку на сайт.</i>

<i>Я проверю подозрительные признаки.</i>''',
        get_wait_input_keyboard("site_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "file_virus")
async def file_virus(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_file_virus)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        FILE_IMAGE,
        '''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте файл документом.</i>

<i>Я отправлю файл на проверку и покажу результат.</i>''',
        get_wait_input_keyboard("files_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "file_size")
async def file_size(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_file_size)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        FILE_IMAGE,
        '''<b><tg-emoji emoji-id="6024106569430472546">📦</tg-emoji> Проверка размера файла</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте файл документом.</i>

<i>Я покажу его размер.</i>''',
        get_wait_input_keyboard("files_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "email_spam")
async def email_spam(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_email_spam)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        EMAIL_IMAGE,
        '''<b><tg-emoji emoji-id="6021413766669801212">🗑</tg-emoji> Проверка email в спам-базах</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте email-адрес.</i>

<b>Например:</b> <code>test@example.com</code>''',
        get_wait_input_keyboard("email_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "email_exists")
async def email_exists(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_email_exists)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        EMAIL_IMAGE,
        '''<b><tg-emoji emoji-id="6019175208240289774">✅</tg-emoji> Проверка существования email</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте email-адрес.</i>

<i>Я проверю формат и домен почты.</i>''',
        get_wait_input_keyboard("email_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "email_ip")
async def email_ip(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_email_ip)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        EMAIL_IMAGE,
        '''<b><tg-emoji emoji-id="6019175208240289774">📡</tg-emoji> IP по email</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте email-адрес.</i>

<i>Я найду IP-адреса домена после @.</i>''',
        get_wait_input_keyboard("email_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "password_generator")
async def password_generator(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        PASSWORD_IMAGE,
        '''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Генератор паролей</b>

<i>Выберите длину будущего пароля.</i>

<b>Совет:</b> лучше выбирать <u>12 символов или больше</u>.''',
        get_password_length_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("generate_password_"))
async def generate_password(callback: CallbackQuery):
    length = int(callback.data.replace("generate_password_", ""))
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    password = "".join(secrets.choice(alphabet) for _ in range(length))

    await callback.message.edit_reply_markup(reply_markup=None)
    await edit_section_photo(
        callback.message,
        PASSWORD_IMAGE,
        f'''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Пароль готов</b>

<i>Его можно сразу скопировать.</i>

<code>{password}</code>''',
        get_generated_password_keyboard(),
    )
    await callback.answer()


@dp.callback_query(F.data == "password_checker")
async def password_checker(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_password)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        PASSWORD_IMAGE,
        '''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Проверка пароля</b>

<i>Введите пароль, который нужно проверить.</i>

<i>Я оценю его по нескольким признакам.</i>''',
        get_wait_password_keyboard(),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()
 

@dp.callback_query(F.data == "check_more")
async def check_more(callback: CallbackQuery, state: FSMContext):
    await state.set_state(States.waiting_scam_message)
    await callback.message.edit_reply_markup(reply_markup=None)
    message_id = await edit_section_photo(
        callback.message,
        SCAM_IMAGE,
        SCAM_WAIT_TEXT,
        get_wait_input_keyboard("back_to_menu"),
    )
    await save_wait_message(state, callback.message, message_id)
    await callback.answer()


@dp.callback_query(F.data == "understood")
async def understood(callback: CallbackQuery):
    key = str(callback.message.chat.id) + ":" + str(callback.from_user.id)
    EASTER_CLICKS[key] = 0
    await callback.message.edit_reply_markup(reply_markup=get_checked_keyboard())
    await callback.answer()


@dp.callback_query(F.data == "checked")
async def checked(callback: CallbackQuery):
    key = str(callback.message.chat.id) + ":" + str(callback.from_user.id)
    count = EASTER_CLICKS.get(key, 0) + 1
    EASTER_CLICKS[key] = count

    text = "✅ " + str(count)
    alert_text = ""

    if count >= 21:
        text = str(count)
    elif count >= 20:
        text = "Я устал("
        alert_text = "Я устал("
    elif count >= 15:
        text = "ХВАТИТ!!!!"
        alert_text = "ХВАТИТ!!!!"
    elif count >= 10:
        text = "Зачем?"
        alert_text = "Зачем?"
    elif count >= 5:
        text = "Что ты делаешь?"
        alert_text = "Что ты делаешь?"
    elif count >= 3:
        text = "Хватит!"
        alert_text = "Хватит!"

    if count == 67:
        for number in range(10):
            await callback.message.answer("67")

    try:
        await callback.message.edit_reply_markup(reply_markup=get_checked_keyboard(text))
    except Exception:
        pass

    await callback.answer(alert_text)


def check_password(password):
    checks = {
        "Нужно сделать пароль длиннее 12 символов": len(password) >= 12,
        "Нужно добавить маленькие буквы": any(symbol.islower() for symbol in password),
        "Нужно добавить большие буквы": any(symbol.isupper() for symbol in password),
        "Нужно добавить цифры": any(symbol.isdigit() for symbol in password),
        "Нужно добавить специальные символы": any(symbol in "!@#$%^&*()-_=+[]{};:,.<>?/" for symbol in password),
        "Нужно убрать простые слова и последовательности": not any(
            word in password.lower()
            for word in ["1234", "1111", "0000", "qwerty", "password", "пароль"]
        ),
    }

    score = sum(checks.values())
    bad_parts = [name for name, result in checks.items() if not result]

    if score <= 3:
        level = "Лёгкий"
        style = "danger"
    elif score <= 5:
        level = "Средний"
        style = "primary"
    else:
        level = "Сложный"
        style = "success"

    return level, style, bad_parts


def make_password_answer(password):
    level, style, bad_parts = check_password(password)

    if level == "Сложный":
        text = '''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Вердикт:</b> <b>сложный пароль</b>

<i>Пароль надёжный.</i>

<i>Его можно использовать.</i>'''
    else:
        text = f'''<tg-emoji emoji-id="6005570495603282482">🔑</tg-emoji> <b>Вердикт:</b> <b>{level.lower()} пароль</b>

<i>Что нужно сделать:</i>
'''
        for part in bad_parts:
            text += f'''- {part}
'''

    return text, style


def clean_domain(text):
    text = text.strip().lower()
    if "://" not in text:
        text = "http://" + text

    parsed = urllib.parse.urlparse(text)
    domain = parsed.netloc or parsed.path
    domain = domain.split("@")[-1]
    domain = domain.split(":")[0]
    domain = domain.replace("www.", "", 1)
    return domain.strip("/")


def is_domain(text):
    return re.match(r"^[a-zа-яё0-9-]+(\.[a-zа-яё0-9-]+)+$", text.strip().lower()) is not None


def clean_url(text):
    text = text.strip()
    if "://" not in text:
        text = "https://" + text
    return text


def is_email(text):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", text.strip()) is not None


def format_size(size):
    if size is None:
        return "неизвестно"

    size = int(size)
    if size < 1024:
        return f"{size} Б"
    if size < 1024 * 1024:
        return f"{round(size / 1024, 2)} КБ"
    if size < 1024 * 1024 * 1024:
        return f"{round(size / 1024 / 1024, 2)} МБ"
    return f"{round(size / 1024 / 1024 / 1024, 2)} ГБ"


def safe_text(text):
    return html.escape(str(text))


def get_json_url(url, timeout=15):
    request = urllib.request.Request(url, headers={"User-Agent": "SafeShield"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def get_dns_records(domain, record_type):
    url = (
        "https://dns.google/resolve?name="
        + urllib.parse.quote(domain)
        + "&type="
        + urllib.parse.quote(record_type)
    )
    data = get_json_url(url)
    records = []

    for answer in data.get("Answer", []):
        records.append(answer.get("data", ""))

    return records


def check_2ip_rkn(domain):
    if not TWO_IP_API_TOKEN:
        return None

    try:
        url = (
            "https://api.2ip.io/abuses/"
            + urllib.parse.quote(domain)
            + "?token="
            + urllib.parse.quote(TWO_IP_API_TOKEN)
        )
        try:
            data = get_json_url(url, 10)
        except urllib.error.HTTPError as error:
            data = json.loads(error.read().decode("utf-8"))

        if data.get("error"):
            error_text = str(data.get("error", "")).lower()
            message_text = str(data.get("message", "")).lower()

            if error_text == "no data":
                return f'''<b><tg-emoji emoji-id="6021451978993834164">🚫</tg-emoji> Домен не найден в реестре</b>

<b>Домен:</b> <code>{safe_text(domain)}</code>

<i>Запись для этого домена не найдена.</i>'''

            if "too many requests" in message_text:
                return f'''<b><tg-emoji emoji-id="6030789912205204974">🚫</tg-emoji> Проверка РКН</b>

<b>Домен:</b> <code>{safe_text(domain)}</code>

<i>Сейчас не получилось выполнить проверку. Попробуйте немного позже.</i>'''

            return f'''<b><tg-emoji emoji-id="6030789912205204974">🚫</tg-emoji> Проверка РКН</b>

<b>Домен:</b> <code>{safe_text(domain)}</code>

<i>Не получилось проверить домен.</i>'''

        abuses = data.get("abuses")

        if isinstance(abuses, dict):
            abuses = [abuses]

        if not isinstance(abuses, list):
            abuses = []

        for item in abuses:
            description = str(item.get("description", "")).lower()
            comment = str(item.get("comment", "")).lower()
            author = str(item.get("author", "")).lower()

            if (
                "rkn" in description
                or "rkn" in comment
                or "rkn" in author
                or "roskomnadzor" in author
                or "роскомнадзор" in author
            ):
                date = safe_text(item.get("date", "неизвестно"))
                item_comment = safe_text(item.get("comment", "не указано"))

                return f'''<b><tg-emoji emoji-id="5276240711795107620">🚫</tg-emoji> Домен найден в реестре</b>

<b>Домен:</b> <code>{safe_text(domain)}</code>
<b>Комментарий:</b> <code>{item_comment}</code>
<b>Дата обновления:</b> <code>{date}</code>

<i>Совпадение найдено.</i>'''

        return f'''<b><tg-emoji emoji-id="6021451978993834164">🚫</tg-emoji> Домен не найден в реестре</b>

<b>Домен:</b> <code>{safe_text(domain)}</code>

<i>Запись для этого домена не найдена.</i>'''
    except Exception:
        return None


def check_rkn_domain_info(text):
    domain = clean_domain(text)
    domain_html = safe_text(domain)

    if not is_domain(domain):
        return f'''<b><tg-emoji emoji-id="5276240711795107620">🚫</tg-emoji> Это не домен</b>

<b>Вы отправили:</b> <code>{domain_html}</code>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте домен сайта без лишнего текста.</i>

<b>Пример:</b> <code>example.com</code>'''

    answer_2ip = check_2ip_rkn(domain)

    if answer_2ip is not None:
        return answer_2ip

    return f'''<b><tg-emoji emoji-id="6030789912205204974">🚫</tg-emoji> Проверка РКН</b>

<b>Домен:</b> <code>{domain_html}</code>

<i>Не получилось проверить домен.</i>'''


def check_domain_info(text):
    domain = clean_domain(text)
    domain_html = safe_text(domain)

    try:
        addresses = get_dns_records(domain, "A")
        ipv6_addresses = get_dns_records(domain, "AAAA")
        ns_records = get_dns_records(domain, "NS")

        if not addresses:
            addresses = socket.gethostbyname_ex(domain)[2]

        ips = safe_text(", ".join(addresses[:5]))
        ipv6 = safe_text(", ".join(ipv6_addresses[:3])) if ipv6_addresses else "не найдено"
        ns = safe_text(", ".join(ns_records[:4])) if ns_records else "не найдено"
        return f'''<b><tg-emoji emoji-id="6019175208240289774">🌐</tg-emoji> Домен найден</b>

<b>Домен:</b> <code>{domain_html}</code>
<b>IPv4:</b> <code>{ips}</code>
<b>IPv6:</b> <code>{ipv6}</code>
<b>NS:</b> <code>{ns}</code>

<i>Домен отвечает в DNS.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="5276240711795107620">🌐</tg-emoji> Домен не найден</b>

<b>Домен:</b> <code>{domain_html}</code>

<i>Не получилось найти IP-адреса домена.</i>'''


def check_domain_age_info(text):
    domain = clean_domain(text)
    domain_html = safe_text(domain)

    try:
        url = "https://rdap.org/domain/" + urllib.parse.quote(domain)
        data = get_json_url(url)

        created = "не найдено"
        changed = "не найдено"
        registrar = data.get("registrar", {}).get("name", "не найдено")

        for event in data.get("events", []):
            action = event.get("eventAction")
            date = event.get("eventDate", "")
            if action == "registration":
                created = date[:10]
            if action == "last changed":
                changed = date[:10]

        return f'''<b><tg-emoji emoji-id="6021607757457660145">📅</tg-emoji> Возраст домена</b>

<b>Домен:</b> <code>{domain_html}</code>
<b>Дата регистрации:</b> <code>{created}</code>
<b>Последнее изменение:</b> <code>{changed}</code>
<b>Регистратор:</b> <code>{safe_text(registrar)}</code>

<i>Данные о домене найдены.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="6021607757457660145">📅</tg-emoji> Возраст домена</b>

<b>Домен:</b> <code>{domain_html}</code>

<i>Не получилось получить данные о возрасте домена.</i>'''


def check_ssl_info(text):
    domain = clean_domain(text)
    domain_html = safe_text(domain)

    try:
        context = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as secure_sock:
                cert = secure_sock.getpeercert()

        subject = dict(x[0] for x in cert.get("subject", []))
        issuer = dict(x[0] for x in cert.get("issuer", []))
        common_name = subject.get("commonName", "не найдено")
        issuer_name = issuer.get("commonName", "не найдено")
        not_after = cert.get("notAfter", "не найдено")

        return f'''<b><tg-emoji emoji-id="6021738534916854774">🔒</tg-emoji> SSL работает</b>

<b>Домен:</b> <code>{domain_html}</code>
<b>Сертификат:</b> <code>{safe_text(common_name)}</code>
<b>Кем выдан:</b> <code>{safe_text(issuer_name)}</code>
<b>Действует до:</b> <code>{safe_text(not_after)}</code>

<i>Соединение по HTTPS успешно.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="6021738534916854774">🔒</tg-emoji> SSL не проверен</b>

<b>Домен:</b> <code>{domain_html}</code>

<i>Не удалось подключиться к сайту по HTTPS.</i>'''


def check_ip_info(text):
    ip_text = text.strip()
    ip_html = safe_text(ip_text)

    try:
        ip = ipaddress.ip_address(ip_text)

        if ip.is_private:
            ip_type = "приватный"
        elif ip.is_loopback:
            ip_type = "локальный"
        elif ip.is_multicast:
            ip_type = "multicast"
        else:
            ip_type = "публичный"

        try:
            url = "https://ipwho.is/" + urllib.parse.quote(ip_text)
            data = get_json_url(url)
            country = safe_text(data.get("country", "не найдено"))
            city = safe_text(data.get("city", "не найдено"))
            region = safe_text(data.get("region", "не найдено"))
            isp = safe_text(data.get("connection", {}).get("isp", "не найдено"))
            org = safe_text(data.get("connection", {}).get("org", "не найдено"))
            as_info = safe_text(data.get("connection", {}).get("asn", "не найдено"))
            timezone = safe_text(data.get("timezone", {}).get("id", "не найдено"))
        except Exception:
            country = "не найдено"
            city = "не найдено"
            region = "не найдено"
            isp = "не найдено"
            org = "не найдено"
            as_info = "не найдено"
            timezone = "не найдено"

        return f'''<b><tg-emoji emoji-id="6023778764641540987">📡</tg-emoji> IP корректный</b>

<b>IP:</b> <code>{safe_text(ip)}</code>
<b>Версия:</b> <code>IPv{ip.version}</code>
<b>Тип:</b> <code>{ip_type}</code>
<b>Страна:</b> <code>{country}</code>
<b>Регион:</b> <code>{region}</code>
<b>Город:</b> <code>{city}</code>
<b>Провайдер:</b> <code>{isp}</code>
<b>Организация:</b> <code>{org}</code>
<b>ASN:</b> <code>{as_info}</code>
<b>Часовой пояс:</b> <code>{timezone}</code>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="5276240711795107620">📡</tg-emoji> IP некорректный</b>

<b>Ввод:</b> <code>{ip_html}</code>

<i>Это не похоже на правильный IP-адрес.</i>'''


def check_google_safe_browsing(url):
    api_url = (
        "https://safebrowsing.googleapis.com/v4/threatMatches:find?key="
        + urllib.parse.quote(GOOGLE_SAFE_BROWSING_API_KEY)
    )
    data = {
        "client": {
            "clientId": "safeshield",
            "clientVersion": "1.0",
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION",
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}],
        },
    }

    request = urllib.request.Request(
        api_url,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "SafeShield",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=15) as response:
        result = json.loads(response.read().decode("utf-8"))

    return result.get("matches", [])


def check_site_virus_info(text):
    url = clean_url(text)
    url_html = safe_text(url)

    try:
        matches = check_google_safe_browsing(url)
    except Exception:
        return f'''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка сайта на вредоносность</b>

<b>Сайт:</b> <code>{url_html}</code>

<i>Не получилось проверить сайт.</i>'''

    if matches:
        text_answer = f'''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Сайт выглядит подозрительно</b>

<b>Сайт:</b> <code>{url_html}</code>

<i>Что найдено:</i>
'''
        for match in matches:
            part = safe_text(match.get("threatType", "угроза"))
            text_answer += f'''- {part}
'''
        return text_answer

    return f'''<b><tg-emoji emoji-id="6021451978993834164">🦠</tg-emoji> Явных угроз не найдено</b>

<b>Сайт:</b> <code>{url_html}</code>

<i>В базе угроз совпадений нет.</i>'''


def get_kaspersky_zone_text(zone):
    if zone == "Red":
        return "опасный файл"
    if zone == "Yellow":
        return "подозрительный файл"
    if zone == "Green":
        return "угроз не найдено"
    if zone == "Grey":
        return "мало данных"
    return "статус неизвестен"


def get_kaspersky_title(zone):
    if zone == "Red":
        return '''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Файл опасный</b>'''
    if zone == "Yellow":
        return '''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Файл подозрительный</b>'''
    if zone == "Green":
        return '''<b><tg-emoji emoji-id="6021451978993834164">🦠</tg-emoji> Явных угроз не найдено</b>'''
    return '''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>'''


def scan_file_kaspersky(file_name, file_bytes):
    url = (
        "https://opentip.kaspersky.com/api/v1/scan/file?filename="
        + urllib.parse.quote(file_name)
    )
    request = urllib.request.Request(
        url,
        data=file_bytes,
        headers={
            "x-api-key": KASPERSKY_OPENTIP_API_KEY,
            "Content-Type": "application/octet-stream",
            "User-Agent": "ShieldTools",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def check_file_virus_info(document, file_bytes):
    file_name = document.file_name or "без названия"
    file_name_html = safe_text(file_name)
    size = document.file_size

    if not KASPERSKY_OPENTIP_API_KEY:
        return f'''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>

<i>Не получилось проверить файл.</i>'''

    try:
        data = scan_file_kaspersky(file_name, file_bytes)
    except urllib.error.HTTPError as error:
        if error.code == 401 or error.code == 403:
            return f'''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Проверка файла на вирусы</b>

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>

<i>Не получилось проверить файл.</i>'''

        return f'''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>

<i>Не получилось проверить файл.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>

<i>Не получилось проверить файл.</i>'''

    zone = data.get("Zone", "")
    status = data.get("Status", "")
    file_info = data.get("FileGeneralInfo", {})

    if not isinstance(file_info, dict):
        file_info = {}

    file_status = file_info.get("FileStatus") or data.get("FileStatus") or "не найдено"
    sha256 = file_info.get("Sha256") or data.get("Sha256") or "не найдено"
    md5 = file_info.get("Md5") or data.get("Md5") or "не найдено"
    zone_text = get_kaspersky_zone_text(zone)
    title = get_kaspersky_title(zone)

    text_answer = f'''{title}

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>
<b>Вердикт:</b> <code>{safe_text(zone_text)}</code>
<b>Статус:</b> <code>{safe_text(file_status)}</code>'''

    if status:
        text_answer += f'''
<b>Анализ:</b> <code>{safe_text(status)}</code>'''

    text_answer += f'''
<b>SHA256:</b> <code>{safe_text(sha256)}</code>
<b>MD5:</b> <code>{safe_text(md5)}</code>'''

    if zone == "Grey" or status == "in progress":
        text_answer += '''

<i>Полный анализ может занять несколько минут.</i>'''
    elif zone == "Green":
        text_answer += '''

<i>По результату проверки явных угроз нет.</i>'''
    else:
        text_answer += '''

<i>К этому файлу лучше относиться осторожно.</i>'''

    return text_answer


def check_file_size_info(document):
    file_name = document.file_name or "без названия"
    file_name_html = safe_text(file_name)
    size = document.file_size

    return f'''<b><tg-emoji emoji-id="6024106569430472546">📦</tg-emoji> Размер файла</b>

<b>Файл:</b> <code>{file_name_html}</code>
<b>Размер:</b> <code>{format_size(size)}</code>'''


def check_email_exists_info(text):
    email = text.strip().lower()
    email_html = safe_text(email)

    if not is_email(email):
        return f'''<b><tg-emoji emoji-id="5276240711795107620">✅</tg-emoji> Email некорректный</b>

<b>Ввод:</b> <code>{email_html}</code>

<i>Адрес написан в неправильном формате.</i>'''

    domain = email.split("@")[1]
    domain_html = safe_text(domain)

    try:
        mx_records = get_dns_records(domain, "MX")

        if mx_records:
            mx_text = safe_text(", ".join(mx_records[:5]))
        else:
            mx_text = "не найдено"

        addresses = get_dns_records(domain, "A")
        ips = safe_text(", ".join(addresses[:5])) if addresses else "не найдено"

        if not mx_records and not addresses:
            raise ValueError("DNS records not found")

        return f'''<b><tg-emoji emoji-id="6019175208240289774">✅</tg-emoji> Email выглядит существующим</b>

<b>Email:</b> <code>{email_html}</code>
<b>Домен:</b> <code>{domain_html}</code>
<b>MX:</b> <code>{mx_text}</code>
<b>IP домена:</b> <code>{ips}</code>

<i>Домен почты найден в DNS.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="5276240711795107620">✅</tg-emoji> Email не подтверждён</b>

<b>Email:</b> <code>{email_html}</code>
<b>Домен:</b> <code>{domain_html}</code>

<i>Домен почты не найден в DNS.</i>'''


def check_email_ip_info(text):
    email = text.strip().lower()
    email_html = safe_text(email)

    if not is_email(email):
        return f'''<b><tg-emoji emoji-id="5276240711795107620">📡</tg-emoji> IP по email</b>

<b>Ввод:</b> <code>{email_html}</code>

<i>Это не похоже на email.</i>'''

    domain = email.split("@")[1]
    domain_html = safe_text(domain)

    try:
        addresses = get_dns_records(domain, "A")

        if not addresses:
            addresses = socket.gethostbyname_ex(domain)[2]

        ips = safe_text(", ".join(addresses[:8]))
        return f'''<b><tg-emoji emoji-id="6023778764641540987">📡</tg-emoji> IP по email</b>

<b>Email:</b> <code>{email_html}</code>
<b>Домен:</b> <code>{domain_html}</code>
<b>IP:</b> <code>{ips}</code>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="5276240711795107620">📡</tg-emoji> IP не найден</b>

<b>Email:</b> <code>{email_html}</code>
<b>Домен:</b> <code>{domain_html}</code>

<i>Не получилось найти IP домена.</i>'''


def check_email_spam_info(text):
    email = text.strip().lower()
    email_html = safe_text(email)

    if not is_email(email):
        return f'''<b><tg-emoji emoji-id="5276240711795107620">🗑</tg-emoji> Спам-базы</b>

<b>Ввод:</b> <code>{email_html}</code>

<i>Это не похоже на email.</i>'''

    try:
        url = "https://api.stopforumspam.org/api?email=" + urllib.parse.quote(email) + "&json"
        data = get_json_url(url)
        email_data = data.get("email", {})
        appears = email_data.get("appears") in [1, True]
        frequency = safe_text(email_data.get("frequency", "не найдено"))
        lastseen = safe_text(email_data.get("lastseen", "не найдено"))

        if appears:
            return f'''<b><tg-emoji emoji-id="5276240711795107620">🗑</tg-emoji> Email найден в спам-базе</b>

<b>Email:</b> <code>{email_html}</code>
<b>Частота:</b> <code>{frequency}</code>
<b>Последний раз:</b> <code>{lastseen}</code>

<i>Лучше относиться к этому адресу осторожно.</i>'''

        return f'''<b><tg-emoji emoji-id="6021451978993834164">🗑</tg-emoji> Email не найден в спам-базе</b>

<b>Email:</b> <code>{email_html}</code>

<i>Совпадений нет.</i>'''
    except Exception:
        return f'''<b><tg-emoji emoji-id="6019263620142078168">🗑</tg-emoji> Спам-базы</b>

<b>Email:</b> <code>{email_html}</code>

<i>Не получилось выполнить проверку.</i>'''


@dp.message(States.waiting_password)
async def check_password_message(message: Message, state: FSMContext):
    await state.clear()
    answer, style = make_password_answer(message.text)
    await send_section_photo(
        message,
        PASSWORD_IMAGE,
        answer,
        get_password_check_keyboard(style),
    )


@dp.message(States.waiting_domain_check)
async def check_domain_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_domain_info, message.text or "")
    await send_section_photo(
        message,
        DOMAIN_IMAGE,
        answer,
        get_check_again_keyboard("domain_check", "domains_menu"),
    )


@dp.message(States.waiting_domain_age)
async def check_domain_age_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_domain_age_info, message.text or "")
    await send_section_photo(
        message,
        DOMAIN_IMAGE,
        answer,
        get_check_again_keyboard("domain_age", "domains_menu"),
    )


@dp.message(States.waiting_ssl_check)
async def check_ssl_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_ssl_info, message.text or "")
    await send_section_photo(
        message,
        DOMAIN_IMAGE,
        answer,
        get_check_again_keyboard("ssl_check", "domains_menu"),
    )


@dp.message(States.waiting_ip_check)
async def check_ip_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_ip_info, message.text or "")
    await send_section_photo(
        message,
        IP_IMAGE,
        answer,
        get_check_again_keyboard("ip_check", "ip_menu"),
    )


@dp.message(States.waiting_site_rkn)
async def check_site_rkn_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_rkn_domain_info, message.text or "")
    style = "success"

    if (
        "Это не домен" in answer
        or "Домен найден" in answer
        or "Не получилось" in answer
    ):
        style = "danger"

    await send_section_photo(
        message,
        SITE_IMAGE,
        answer,
        get_check_again_keyboard("site_rkn", "site_menu", style),
    )


@dp.message(States.waiting_site_virus)
async def check_site_virus_message(message: Message, state: FSMContext):
    await state.clear()
    answer = await asyncio.to_thread(check_site_virus_info, message.text or "")
    await send_section_photo(
        message,
        SITE_IMAGE,
        answer,
        get_check_again_keyboard("site_virus", "site_menu"),
    )


@dp.message(States.waiting_file_virus)
async def check_file_virus_message(message: Message, state: FSMContext):
    await state.clear()

    if not message.document:
        answer = '''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Это не файл</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте файл именно документом, а не текст или фото.</i>'''
        keyboard = get_check_again_keyboard("file_virus", "files_menu", "danger")
    else:
        document = message.document
        max_size = 20 * 1024 * 1024

        if document.file_size and document.file_size > max_size:
            answer = f'''<b><tg-emoji emoji-id="5276240711795107620">🦠</tg-emoji> Файл слишком большой</b>

<b>Файл:</b> <code>{safe_text(document.file_name or "без названия")}</code>
<b>Размер:</b> <code>{format_size(document.file_size)}</code>

<i>Отправьте файл размером до 20 МБ.</i>'''
            keyboard = get_check_again_keyboard("file_virus", "files_menu", "danger")
        else:
            loading_message = None
            animation_stop = asyncio.Event()
            animation_task = None

            try:
                loading_message = await message.answer(
                    get_file_analysis_text(""),
                    parse_mode="HTML",
                )
                animation_task = asyncio.create_task(
                    file_analysis_animation(loading_message, animation_stop)
                )

                file_buffer = io.BytesIO()
                await message.bot.download(document, destination=file_buffer)
                file_bytes = file_buffer.getvalue()
                answer = await asyncio.to_thread(check_file_virus_info, document, file_bytes)

                if "Файл опасный" in answer or "Файл подозрительный" in answer:
                    keyboard = get_check_again_keyboard("file_virus", "files_menu", "danger")
                else:
                    keyboard = get_check_again_keyboard("file_virus", "files_menu")
            except Exception:
                answer = f'''<b><tg-emoji emoji-id="6023632319141648759">🦠</tg-emoji> Проверка файла на вирусы</b>

<b>Файл:</b> <code>{safe_text(document.file_name or "без названия")}</code>
<b>Размер:</b> <code>{format_size(document.file_size)}</code>

<i>Не получилось скачать или проверить файл.</i>'''
                keyboard = get_check_again_keyboard("file_virus", "files_menu", "danger")
            finally:
                animation_stop.set()

                if animation_task:
                    try:
                        await animation_task
                    except Exception:
                        pass

            if loading_message:
                try:
                    await loading_message.delete()
                except Exception:
                    pass

                await send_section_photo(
                    message,
                    FILE_IMAGE,
                    answer,
                    keyboard,
                )
                return

    await send_section_photo(
        message,
        FILE_IMAGE,
        answer,
        keyboard,
    )


@dp.message(States.waiting_file_size)
async def check_file_size_message(message: Message, state: FSMContext):
    await state.clear()

    if not message.document:
        answer = '''<b><tg-emoji emoji-id="5276240711795107620">📦</tg-emoji> Это не файл</b>

<i><tg-emoji emoji-id="6021741116192201252">📩</tg-emoji> Отправьте файл именно документом, а не текст или фото.</i>'''
        keyboard = get_check_again_keyboard("file_size", "files_menu", "danger")
    else:
        answer = check_file_size_info(message.document)
        keyboard = get_check_again_keyboard("file_size", "files_menu")

    await send_section_photo(
        message,
        FILE_IMAGE,
        answer,
        keyboard,
    )


@dp.message(States.waiting_email_spam)
async def check_email_spam_message(message: Message, state: FSMContext):
    await state.clear()
    email = message.text or ""

    if not is_email(email):
        answer = f'''<b><tg-emoji emoji-id="5276240711795107620">🗑</tg-emoji> Это не email</b>

<b>Ввод:</b> <code>{safe_text(email)}</code>

<i>Введите именно почту, например:</i> <code>test@example.com</code>'''
        keyboard = get_check_again_keyboard("email_spam", "email_menu", "danger")
    else:
        answer = await asyncio.to_thread(check_email_spam_info, email)
        keyboard = get_check_again_keyboard("email_spam", "email_menu")

    await send_section_photo(
        message,
        EMAIL_IMAGE,
        answer,
        keyboard,
    )


@dp.message(States.waiting_email_exists)
async def check_email_exists_message(message: Message, state: FSMContext):
    await state.clear()
    email = message.text or ""

    if not is_email(email):
        answer = f'''<b><tg-emoji emoji-id="5276240711795107620">✅</tg-emoji> Это не email</b>

<b>Ввод:</b> <code>{safe_text(email)}</code>

<i>Введите именно почту, например:</i> <code>test@example.com</code>'''
        keyboard = get_check_again_keyboard("email_exists", "email_menu", "danger")
    else:
        answer = await asyncio.to_thread(check_email_exists_info, email)
        keyboard = get_check_again_keyboard("email_exists", "email_menu")

    await send_section_photo(
        message,
        EMAIL_IMAGE,
        answer,
        keyboard,
    )


@dp.message(States.waiting_email_ip)
async def check_email_ip_message(message: Message, state: FSMContext):
    await state.clear()
    email = message.text or ""

    if not is_email(email):
        answer = f'''<b><tg-emoji emoji-id="5276240711795107620">📡</tg-emoji> Это не email</b>

<b>Ввод:</b> <code>{safe_text(email)}</code>

<i>Введите именно почту, например:</i> <code>test@example.com</code>'''
        keyboard = get_check_again_keyboard("email_ip", "email_menu", "danger")
    else:
        answer = await asyncio.to_thread(check_email_ip_info, email)
        keyboard = get_check_again_keyboard("email_ip", "email_menu")

    await send_section_photo(
        message,
        EMAIL_IMAGE,
        answer,
        keyboard,
    )


@dp.message(States.waiting_crypto_password)
async def crypto_password_message(message: Message, state: FSMContext):
    password = message.text or ""

    if len(password) < 8 or len(password) > 128:
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            '''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Пароль не подходит</b>

<i>Нужен текстовый пароль длиной от 8 до 128 символов. Попробуйте ещё раз.</i>''',
            get_wait_input_keyboard("crypto_menu"),
        )
        return

    try:
        await message.delete()
    except Exception:
        pass

    await state.update_data(crypto_password=password)
    await state.set_state(States.waiting_crypto_file)
    data = await state.get_data()
    mode = data.get("crypto_mode")

    if mode == "encrypt":
        action = "зашифровать"
        extra = ""
    else:
        action = "расшифровать"
        extra = "\n\n<i>Файл должен иметь формат <code>.shield</code>.</i>"

    await send_section_photo(
        message,
        CRYPTO_IMAGE,
        f'''<b><tg-emoji emoji-id="6021375494216226506">📄</tg-emoji> Отправьте файл</b>

<i>Отправьте документ, который нужно {action}. Максимальный размер - 19 МБ.</i>{extra}''',
        get_wait_input_keyboard("crypto_menu"),
    )


@dp.message(States.waiting_crypto_file)
async def crypto_file_message(message: Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("crypto_mode")
    password = data.get("crypto_password", "")

    if not message.document:
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Это не файл</b>

<i>Отправьте файл именно документом, а не текстом, фото, видео или стикером.</i>''',
            get_wait_input_keyboard("crypto_menu"),
        )
        return

    document = message.document
    max_size = 19 * 1024 * 1024
    if document.file_size and document.file_size > max_size:
        await state.clear()
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Файл слишком большой</b>

<b>Файл:</b> <code>{safe_text(document.file_name or "без названия")}</code>
<b>Размер:</b> <code>{format_size(document.file_size)}</code>

<i>Отправьте файл размером до 19 МБ.</i>''',
            get_crypto_result_keyboard(),
        )
        return

    if mode == "decrypt" and not (document.file_name or "").lower().endswith(".shield"):
        await state.clear()
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Неверный формат</b>

<i>Для расшифровки нужен файл <code>.shield</code>, созданный ShieldTools.</i>''',
            get_check_again_keyboard("crypto_decrypt", "crypto_menu", "danger"),
        )
        return

    loading_message = await message.answer(
        get_crypto_progress_text(mode, ""),
        parse_mode="HTML",
    )
    animation_stop = asyncio.Event()
    animation_task = asyncio.create_task(
        crypto_progress_animation(loading_message, animation_stop, mode)
    )

    try:
        file_buffer = io.BytesIO()
        await message.bot.download(document, destination=file_buffer)
        file_bytes = file_buffer.getvalue()

        if mode == "encrypt":
            result_bytes, algorithm_title = await asyncio.to_thread(
                encrypt_file,
                file_bytes,
                document.file_name or "file",
                password,
                data.get("crypto_algorithm"),
            )
            result_name = (document.file_name or "file") + ".shield"
            caption = f'''<b><tg-emoji emoji-id="5237699328843200968">✅</tg-emoji> Файл зашифрован</b>

<b>Алгоритм:</b> <code>{algorithm_title}</code>
<b>Размер:</b> <code>{format_size(len(result_bytes))}</code>

<i>Сохраните пароль: без него расшифровка невозможна.</i>'''
        else:
            result_bytes, result_name, algorithm_title = await asyncio.to_thread(
                decrypt_file, file_bytes, password
            )
            caption = f'''<b><tg-emoji emoji-id="5237699328843200968">✅</tg-emoji> Файл расшифрован</b>

<b>Алгоритм:</b> <code>{algorithm_title}</code>
<b>Файл:</b> <code>{safe_text(result_name)}</code>'''

        await state.clear()
        await message.answer_document(
            BufferedInputFile(result_bytes, filename=result_name),
            caption=caption,
            parse_mode="HTML",
            reply_markup=get_crypto_result_keyboard(),
        )
    except InvalidEncryptedFile:
        await state.clear()
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Это не зашифрованный файл ShieldTools</b>

<i>Расширения <code>.shield</code> недостаточно: внутренняя сигнатура файла не прошла проверку.</i>''',
            get_check_again_keyboard("crypto_decrypt", "crypto_menu", "danger"),
        )
    except WrongPassword:
        await state.clear()
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Неверный пароль или файл повреждён</b>

<i>Проверьте пароль и попробуйте снова.</i>''',
            get_check_again_keyboard("crypto_decrypt", "crypto_menu", "danger"),
        )
    except Exception:
        await state.clear()
        await send_section_photo(
            message,
            CRYPTO_IMAGE,
            f'''<b><tg-emoji emoji-id="5276240711795107620">❌</tg-emoji> Не получилось обработать файл</b>

<i>Попробуйте ещё раз или выберите другой файл.</i>''',
            get_crypto_result_keyboard(),
        )
    finally:
        animation_stop.set()
        try:
            await animation_task
        except Exception:
            pass
        try:
            await loading_message.delete()
        except Exception:
            pass


@dp.message(States.waiting_scam_message)
async def check_message(message: Message, state: FSMContext):
    await state.clear()
    analyze_task = asyncio.create_task(asyncio.to_thread(analyze_message, message.text))
    answer = await analyze_task
    await send_section_photo(
        message,
        SCAM_IMAGE,
        answer,
        get_back_keyboard(answer),
    )


@dp.message()
async def choose_mode_message(message: Message):
    await message.answer(
        '''<b>Я ещё не знаю таких команд.</b>

<i>Сначала нажмите нужную кнопку, а потом отправляйте данные для проверки.</i>''',
        parse_mode="HTML",
        reply_markup=get_understood_keyboard(),
    )


async def main():
    bot = Bot(token=tg_bot_token)
    await set_commands_menu(bot)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
