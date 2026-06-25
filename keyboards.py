from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Проверка SMS", icon_custom_emoji_id="5891243564309942507"),
            KeyboardButton(text="Шифратор", icon_custom_emoji_id="6019568309417023812"),
        ],
        [
            KeyboardButton(text="Пароли", icon_custom_emoji_id="6005570495603282482"),
            KeyboardButton(text="Домены", icon_custom_emoji_id="6021607757457660145"),
        ],
        [
            KeyboardButton(text="IP", icon_custom_emoji_id="6023778764641540987"),
            KeyboardButton(text="Проверка сайта", icon_custom_emoji_id="6019245310696495518"),
        ],
        [
            KeyboardButton(text="Файлы", icon_custom_emoji_id="6021375494216226506"),
            KeyboardButton(text="Email", icon_custom_emoji_id="6019263620142078168"),
        ],
    ],
    resize_keyboard=True,
)


def get_crypto_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Зашифровать файл",
                    icon_custom_emoji_id="6019568309417023812",
                    callback_data="crypto_encrypt",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Расшифровать файл",
                    icon_custom_emoji_id="6021313238665271979",
                    callback_data="crypto_decrypt",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_crypto_result_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Ещё один файл",
                    callback_data="crypto_menu",
                    style="success",
                ),
            ],
            [
                InlineKeyboardButton(text="Назад", callback_data="back_to_menu"),
            ],
        ],
    )


def get_back_keyboard(answer):
    if answer.startswith("<b><i>Да, это определённо мошенники."):
        button_style = "danger"
    else:
        button_style = "success"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверить ещё",
                    callback_data="check_more",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Вернуться назад",
                    callback_data="back_to_menu",
                    style=button_style,
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_access_check_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Я не бот!",
                    callback_data="access_check",
                    style="primary",
                    icon_custom_emoji_id="6030400221232501136",
                ),
            ],
        ],
    )


def get_access_checked_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверка пройдена",
                    callback_data="access_checked",
                    style="success",
                    icon_custom_emoji_id="5237699328843200968",
                ),
            ],
        ],
    )


def get_scam_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Отправить",
                    callback_data="scam_start",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_password_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Генератор паролей",
                    callback_data="password_generator",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверка пароля",
                    callback_data="password_checker",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_password_length_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="8",
                    callback_data="generate_password_8",
                ),
                InlineKeyboardButton(
                    text="12",
                    callback_data="generate_password_12",
                ),
                InlineKeyboardButton(
                    text="16",
                    callback_data="generate_password_16",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="20",
                    callback_data="generate_password_20",
                ),
                InlineKeyboardButton(
                    text="32",
                    callback_data="generate_password_32",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="passwords_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_password_check_keyboard(style):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверить ещё",
                    callback_data="password_checker",
                    style=style,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="passwords_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_wait_password_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="passwords_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_wait_input_keyboard(back_callback_data):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=back_callback_data,
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_generated_password_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Сгенерировать ещё",
                    callback_data="password_generator",
                    style="success",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="passwords_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_domains_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверка домена",
                    callback_data="domain_check",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Возраст домена",
                    callback_data="domain_age",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверка SSL",
                    callback_data="ssl_check",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_ip_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверка IP",
                    callback_data="ip_check",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_site_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Блокировка РКН",
                    callback_data="site_rkn",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверка на вредоносность",
                    callback_data="site_virus",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_files_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Проверка на вирусы",
                    callback_data="file_virus",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверка размера",
                    callback_data="file_size",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_email_menu_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Наличие в спам-базах",
                    callback_data="email_spam",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Проверка существования",
                    callback_data="email_exists",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="IP по email",
                    callback_data="email_ip",
                    style="primary",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data="back_to_menu",
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_check_again_keyboard(callback_data, back_callback_data, style="primary"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Попробовать ещё раз",
                    callback_data=callback_data,
                    style=style,
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад",
                    callback_data=back_callback_data,
                    icon_custom_emoji_id="5805509901048356965",
                ),
            ],
        ],
    )


def get_understood_keyboard():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Я понял",
                    callback_data="understood",
                    style="primary",
                ),
            ],
        ],
    )


def get_checked_keyboard(text="✅"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=text,
                    callback_data="checked",
                    style="success",
                ),
            ],
        ],
    )
