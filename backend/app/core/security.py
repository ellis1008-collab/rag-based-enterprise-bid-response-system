import base64
import hashlib
from itertools import cycle

from app.core.config import get_settings


class ApiKeyCipher:
    def __init__(self, secret: str) -> None:
        self._key = hashlib.sha256(secret.encode("utf-8")).digest()

    def encrypt(self, value: str | None) -> str | None:
        if not value:
            return None
        encrypted = bytes(char ^ key for char, key in zip(value.encode("utf-8"), cycle(self._key)))
        return base64.urlsafe_b64encode(encrypted).decode("ascii")

    def decrypt(self, encrypted_value: str | None) -> str | None:
        if not encrypted_value:
            return None
        encrypted = base64.urlsafe_b64decode(encrypted_value.encode("ascii"))
        decrypted = bytes(char ^ key for char, key in zip(encrypted, cycle(self._key)))
        return decrypted.decode("utf-8")


def get_api_key_cipher() -> ApiKeyCipher:
    settings = get_settings()
    return ApiKeyCipher(settings.model_config_secret_key)


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "****"
    prefix = "sk-" if api_key.startswith("sk-") else api_key[:3]
    return f"{prefix}****{api_key[-4:]}"
