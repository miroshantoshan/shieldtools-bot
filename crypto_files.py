import os
import struct

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


MAGIC = b"SHIELD01"
ALGORITHMS = {
    "aes": (1, "AES-256-GCM", AESGCM),
}
ALGORITHMS_BY_ID = {data[0]: (name, *data[1:]) for name, data in ALGORITHMS.items()}
SALT_SIZE = 16
NONCE_SIZE = 12
MAX_FILENAME_BYTES = 1024


class InvalidEncryptedFile(ValueError):
    pass


class WrongPassword(ValueError):
    pass


def _derive_key(password, salt):
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
        password.encode("utf-8")
    )


def _safe_filename(filename):
    filename = os.path.basename(filename or "file")
    filename = filename.replace("\x00", "").strip()
    return filename or "file"


def _filename_bytes(filename):
    filename_bytes = _safe_filename(filename).encode("utf-8")
    if len(filename_bytes) <= MAX_FILENAME_BYTES:
        return filename_bytes

    filename_bytes = filename_bytes[:MAX_FILENAME_BYTES]
    while True:
        try:
            filename_bytes.decode("utf-8")
            return filename_bytes
        except UnicodeDecodeError as error:
            filename_bytes = filename_bytes[: error.start]


def encrypt_file(file_bytes, filename, password, algorithm):
    if algorithm not in ALGORITHMS:
        raise ValueError("Unsupported algorithm")

    algorithm_id, algorithm_title, cipher_class = ALGORITHMS[algorithm]
    filename_bytes = _filename_bytes(filename)
    salt = os.urandom(SALT_SIZE)
    nonce = os.urandom(NONCE_SIZE)
    header = (
        MAGIC
        + bytes([algorithm_id])
        + salt
        + nonce
        + struct.pack(">H", len(filename_bytes))
        + filename_bytes
    )
    key = _derive_key(password, salt)
    encrypted = cipher_class(key).encrypt(nonce, file_bytes, header)
    return header + encrypted, algorithm_title


def decrypt_file(container, password):
    minimum_size = len(MAGIC) + 1 + SALT_SIZE + NONCE_SIZE + 2 + 16
    if len(container) < minimum_size or not container.startswith(MAGIC):
        raise InvalidEncryptedFile("Not a ShieldTools encrypted file")

    position = len(MAGIC)
    algorithm_id = container[position]
    position += 1

    algorithm_data = ALGORITHMS_BY_ID.get(algorithm_id)
    if algorithm_data is None:
        raise InvalidEncryptedFile("Unknown algorithm")

    _, algorithm_title, cipher_class = algorithm_data
    salt = container[position : position + SALT_SIZE]
    position += SALT_SIZE
    nonce = container[position : position + NONCE_SIZE]
    position += NONCE_SIZE
    filename_size = struct.unpack(">H", container[position : position + 2])[0]
    position += 2

    if filename_size > MAX_FILENAME_BYTES or position + filename_size + 16 > len(container):
        raise InvalidEncryptedFile("Damaged encrypted file")

    filename_bytes = container[position : position + filename_size]
    position += filename_size
    header = container[:position]

    try:
        filename = filename_bytes.decode("utf-8")
    except UnicodeDecodeError as error:
        raise InvalidEncryptedFile("Invalid filename") from error

    key = _derive_key(password, salt)
    try:
        decrypted = cipher_class(key).decrypt(nonce, container[position:], header)
    except InvalidTag as error:
        raise WrongPassword("Wrong password or damaged file") from error

    return decrypted, _safe_filename(filename), algorithm_title
