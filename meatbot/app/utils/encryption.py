"""
Утилиты для шифрования чувствительных данных
"""

import base64
import hashlib
import secrets
from typing import Any, Dict, Optional

import structlog
from cryptography.fernet import Fernet

logger = structlog.get_logger()


class EncryptionService:
    """Сервис для шифрования и дешифрования данных"""

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or self._generate_key()
        self.fernet = self._create_fernet()

    def _generate_key(self) -> str:
        """Генерирует случайный ключ шифрования"""
        return Fernet.generate_key().decode()

    def _create_fernet(self) -> Fernet:
        """Создает объект Fernet для шифрования"""
        # Преобразуем строковый ключ в байты
        if isinstance(self.secret_key, str):
            key_bytes = self.secret_key.encode()
        else:
            key_bytes = self.secret_key

        # SECURITY FIX (P2-ENC-01): Использовать PBKDF2 вместо padding
        # Если ключ короткий, растягиваем его криптографически безопасным способом
        if len(key_bytes) < 32:
            # Используем PBKDF2 для key derivation
            key_bytes = hashlib.pbkdf2_hmac(
                'sha256',
                key_bytes,
                b'meatbot_encryption_salt_v1',  # Salt
                100000,  # Итерации
                dklen=32  # Длина ключа
            )
        else:
            # Обрезаем до 32 байт если ключ длиннее
            key_bytes = key_bytes[:32]

        # Кодируем в base64
        key_b64 = base64.urlsafe_b64encode(key_bytes)

        return Fernet(key_b64)

    def encrypt(self, data: str) -> str:
        """Шифрует строковые данные"""
        try:
            if not isinstance(data, str):
                data = str(data)

            encrypted_data = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("encryption_failed", error=str(e))
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Дешифрует строковые данные"""
        try:
            # Декодируем из base64
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())

            # Дешифруем
            decrypted_data = self.fernet.decrypt(encrypted_bytes)
            return decrypted_data.decode()
        except Exception as e:
            logger.error("decryption_failed", error=str(e))
            raise

    def encrypt_dict(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Шифрует словарь данных"""
        encrypted_dict = {}

        for key, value in data.items():
            if isinstance(value, str):
                encrypted_dict[key] = self.encrypt(value)
            else:
                encrypted_dict[key] = self.encrypt(str(value))

        return encrypted_dict

    def decrypt_dict(self, encrypted_data: Dict[str, str]) -> Dict[str, str]:
        """Дешифрует словарь данных"""
        decrypted_dict = {}

        for key, value in encrypted_data.items():
            decrypted_dict[key] = self.decrypt(value)

        return decrypted_dict


class HashService:
    """Сервис для хеширования данных"""

    @staticmethod
    def hash_password(
        password: str, salt: Optional[str] = None
    ) -> tuple[str, str]:
        """Хеширует пароль с солью"""
        if salt is None:
            salt = secrets.token_hex(16)

        # Создаем хеш пароля
        password_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000,  # Количество итераций
        )

        return password_hash.hex(), salt

    @staticmethod
    def verify_password(password: str, password_hash: str, salt: str) -> bool:
        """Проверяет пароль"""
        try:
            computed_hash, _ = HashService.hash_password(password, salt)
            return computed_hash == password_hash
        except Exception as e:
            logger.error("password_verification_failed", error=str(e))
            return False

    @staticmethod
    def hash_data(data: str, algorithm: str = "sha256") -> str:
        """Хеширует данные"""
        # SECURITY FIX (P2-ENC-02): Removed MD5 support (cryptographically broken)
        if algorithm == "sha256":
            return hashlib.sha256(data.encode()).hexdigest()
        elif algorithm == "sha512":
            return hashlib.sha512(data.encode()).hexdigest()
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}. Use 'sha256' or 'sha512'")

    @staticmethod
    def generate_token(length: int = 32) -> str:
        """Генерирует случайный токен"""
        return secrets.token_urlsafe(length)


class DataProtectionService:
    """Сервис для защиты чувствительных данных"""

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service
        self.sensitive_fields = {
            "phone",
            "email",
            "address",
            "payment_info",
            "personal_data",
            "credit_card",
            "bank_account",
        }

    def protect_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Защищает чувствительные данные в словаре"""
        protected_data = {}

        for key, value in data.items():
            if key.lower() in self.sensitive_fields and isinstance(value, str):
                # Шифруем чувствительные поля
                protected_data[key] = self.encryption.encrypt(value)
            else:
                protected_data[key] = value

        return protected_data

    def unprotect_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Восстанавливает защищенные данные"""
        unprotected_data = {}

        for key, value in data.items():
            if key.lower() in self.sensitive_fields and isinstance(value, str):
                try:
                    # Дешифруем чувствительные поля
                    unprotected_data[key] = self.encryption.decrypt(value)
                except Exception as e:
                    logger.warning(
                        "decryption_failed_for_field", field=key, error=str(e)
                    )
                    unprotected_data[key] = value
            else:
                unprotected_data[key] = value

        return unprotected_data

    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Маскирует чувствительные данные для логирования"""
        masked_data = {}

        for key, value in data.items():
            if key.lower() in self.sensitive_fields and isinstance(value, str):
                # Маскируем чувствительные поля
                if len(value) > 4:
                    masked_data[key] = (
                        value[:2] + "*" * (len(value) - 4) + value[-2:]
                    )
                else:
                    masked_data[key] = "*" * len(value)
            else:
                masked_data[key] = value

        return masked_data


class SecureStorage:
    """Безопасное хранилище для чувствительных данных"""

    def __init__(self, encryption_service: EncryptionService):
        self.encryption = encryption_service
        self.storage: Dict[str, str] = {}

    def store(self, key: str, value: Any) -> None:
        """Сохраняет зашифрованные данные"""
        if not isinstance(value, str):
            value = str(value)

        encrypted_value = self.encryption.encrypt(value)
        self.storage[key] = encrypted_value

        logger.info("secure_data_stored", key=key)

    def retrieve(self, key: str) -> Optional[str]:
        """Извлекает и дешифрует данные"""
        if key not in self.storage:
            return None

        try:
            encrypted_value = self.storage[key]
            decrypted_value = self.encryption.decrypt(encrypted_value)
            return decrypted_value
        except Exception as e:
            logger.error("secure_data_retrieval_failed", key=key, error=str(e))
            return None

    def delete(self, key: str) -> bool:
        """Удаляет данные из хранилища"""
        if key in self.storage:
            del self.storage[key]
            logger.info("secure_data_deleted", key=key)
            return True
        return False

    def list_keys(self) -> list[str]:
        """Возвращает список всех ключей"""
        return list(self.storage.keys())


# Глобальные экземпляры сервисов
_encryption_service: Optional[EncryptionService] = None
_hash_service: Optional[HashService] = None
_data_protection_service: Optional[DataProtectionService] = None
_secure_storage: Optional[SecureStorage] = None


def init_security_services(secret_key: Optional[str] = None) -> None:
    """Инициализирует сервисы безопасности"""
    global _encryption_service, _hash_service, _data_protection_service, _secure_storage

    _encryption_service = EncryptionService(secret_key)
    _hash_service = HashService()
    _data_protection_service = DataProtectionService(_encryption_service)
    _secure_storage = SecureStorage(_encryption_service)

    logger.info("security_services_initialized")


def get_encryption_service() -> EncryptionService:
    """Получает сервис шифрования"""
    if _encryption_service is None:
        raise RuntimeError("Security services not initialized")
    return _encryption_service


def get_hash_service() -> HashService:
    """Получает сервис хеширования"""
    if _hash_service is None:
        raise RuntimeError("Security services not initialized")
    return _hash_service


def get_data_protection_service() -> DataProtectionService:
    """Получает сервис защиты данных"""
    if _data_protection_service is None:
        raise RuntimeError("Security services not initialized")
    return _data_protection_service


def get_secure_storage() -> SecureStorage:
    """Получает безопасное хранилище"""
    if _secure_storage is None:
        raise RuntimeError("Security services not initialized")
    return _secure_storage
