"""
Unit тесты для сервисов безопасности
"""

import sys
from unittest.mock import MagicMock, Mock, patch

import pytest

from meatbot.app.middlewares.auth import AuthMiddleware, RateLimitMiddleware
from meatbot.app.utils.encryption import (
    DataProtectionService,
    EncryptionService,
    HashService,
    SecureStorage,
)
from meatbot.app.utils.file_validation import (
    FileSecurityScanner,
    FileValidator,
)

# Мокаем magic модуль для Windows
sys.modules["magic"] = MagicMock()

# Импорты должны быть после мока


class TestEncryptionService:
    """Тесты для EncryptionService"""

    def test_encrypt_decrypt_string(self):
        """Тест шифрования и дешифрования строки"""
        service = EncryptionService()

        original_text = "Test secret data"
        encrypted = service.encrypt(original_text)
        decrypted = service.decrypt(encrypted)

        assert encrypted != original_text
        assert decrypted == original_text

    def test_encrypt_decrypt_dict(self):
        """Тест шифрования и дешифрования словаря"""
        service = EncryptionService()

        original_data = {
            "username": "testuser",
            "password": "secret123",
            "email": "test@example.com",
        }

        encrypted_dict = service.encrypt_dict(original_data)
        decrypted_dict = service.decrypt_dict(encrypted_dict)

        assert encrypted_dict != original_data
        assert decrypted_dict == original_data

    def test_encrypt_non_string(self):
        """Тест шифрования не-строковых данных"""
        service = EncryptionService()

        original_data = 12345
        encrypted = service.encrypt(original_data)
        decrypted = service.decrypt(encrypted)

        assert decrypted == "12345"

    def test_encrypt_empty_string(self):
        """Тест шифрования пустой строки"""
        service = EncryptionService()

        encrypted = service.encrypt("")
        decrypted = service.decrypt(encrypted)

        assert decrypted == ""

    def test_decrypt_invalid_data(self):
        """Тест дешифрования некорректных данных"""
        service = EncryptionService()

        with pytest.raises(Exception):
            service.decrypt("invalid_encrypted_data")


class TestHashService:
    """Тесты для HashService"""

    def test_hash_password(self):
        """Тест хеширования пароля"""
        password = "testpassword123"
        password_hash, salt = HashService.hash_password(password)

        assert password_hash is not None
        assert salt is not None
        assert password_hash != password
        assert len(salt) > 0

    def test_verify_password_correct(self):
        """Тест проверки правильного пароля"""
        password = "testpassword123"
        password_hash, salt = HashService.hash_password(password)

        is_valid = HashService.verify_password(password, password_hash, salt)
        assert is_valid is True

    def test_verify_password_incorrect(self):
        """Тест проверки неправильного пароля"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        password_hash, salt = HashService.hash_password(password)

        is_valid = HashService.verify_password(
            wrong_password, password_hash, salt
        )
        assert is_valid is False

    def test_hash_data_sha256(self):
        """Тест хеширования данных SHA256"""
        data = "test data"
        hash_result = HashService.hash_data(data, "sha256")

        assert hash_result is not None
        # SHA256 produces 64 character hex string
        assert len(hash_result) == 64

    def test_hash_data_md5(self):
        """Тест хеширования данных MD5"""
        data = "test data"
        hash_result = HashService.hash_data(data, "md5")

        assert hash_result is not None
        assert len(hash_result) == 32  # MD5 produces 32 character hex string

    def test_generate_token(self):
        """Тест генерации токена"""
        token = HashService.generate_token(32)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_generate_token_different_lengths(self):
        """Тест генерации токенов разной длины"""
        token16 = HashService.generate_token(16)
        token32 = HashService.generate_token(32)
        token64 = HashService.generate_token(64)

        assert len(token16) != len(token32)
        assert len(token32) != len(token64)
        assert token16 != token32 != token64


class TestDataProtectionService:
    """Тесты для DataProtectionService"""

    @pytest.fixture
    def encryption_service(self):
        """Фикстура для EncryptionService"""
        return EncryptionService()

    @pytest.fixture
    def data_protection_service(self, encryption_service):
        """Фикстура для DataProtectionService"""
        return DataProtectionService(encryption_service)

    def test_protect_sensitive_data(self, data_protection_service):
        """Тест защиты чувствительных данных"""
        data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "test@example.com",
            "address": "123 Main St",
            "normal_field": "not_sensitive",
        }

        protected_data = data_protection_service.protect_data(data)

        # Чувствительные поля должны быть зашифрованы
        assert protected_data["phone"] != data["phone"]
        assert protected_data["email"] != data["email"]
        assert protected_data["address"] != data["address"]

        # Обычные поля должны остаться без изменений
        assert protected_data["username"] == data["username"]
        assert protected_data["normal_field"] == data["normal_field"]

    def test_unprotect_sensitive_data(self, data_protection_service):
        """Тест восстановления защищенных данных"""
        data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "test@example.com",
        }

        protected_data = data_protection_service.protect_data(data)
        unprotected_data = data_protection_service.unprotect_data(
            protected_data
        )

        assert unprotected_data == data

    def test_mask_sensitive_data(self, data_protection_service):
        """Тест маскировки чувствительных данных"""
        data = {
            "username": "testuser",
            "phone": "+1234567890",
            "email": "test@example.com",
            "normal_field": "not_sensitive",
        }

        masked_data = data_protection_service.mask_sensitive_data(data)

        # Чувствительные поля должны быть замаскированы
        assert masked_data["phone"] != data["phone"]
        assert "*" in masked_data["phone"]
        assert masked_data["email"] != data["email"]
        assert "*" in masked_data["email"]

        # Обычные поля должны остаться без изменений
        assert masked_data["username"] == data["username"]
        assert masked_data["normal_field"] == data["normal_field"]


class TestSecureStorage:
    """Тесты для SecureStorage"""

    @pytest.fixture
    def encryption_service(self):
        """Фикстура для EncryptionService"""
        return EncryptionService()

    @pytest.fixture
    def secure_storage(self, encryption_service):
        """Фикстура для SecureStorage"""
        return SecureStorage(encryption_service)

    def test_store_and_retrieve(self, secure_storage):
        """Тест сохранения и извлечения данных"""
        key = "test_key"
        value = "test_value"

        secure_storage.store(key, value)
        retrieved_value = secure_storage.retrieve(key)

        assert retrieved_value == value

    def test_store_and_retrieve_nonexistent_key(self, secure_storage):
        """Тест извлечения несуществующего ключа"""
        retrieved_value = secure_storage.retrieve("nonexistent_key")
        assert retrieved_value is None

    def test_delete_key(self, secure_storage):
        """Тест удаления ключа"""
        key = "test_key"
        value = "test_value"

        secure_storage.store(key, value)
        assert secure_storage.retrieve(key) == value

        deleted = secure_storage.delete(key)
        assert deleted is True
        assert secure_storage.retrieve(key) is None

    def test_delete_nonexistent_key(self, secure_storage):
        """Тест удаления несуществующего ключа"""
        deleted = secure_storage.delete("nonexistent_key")
        assert deleted is False

    def test_list_keys(self, secure_storage):
        """Тест получения списка ключей"""
        secure_storage.store("key1", "value1")
        secure_storage.store("key2", "value2")

        keys = secure_storage.list_keys()
        assert "key1" in keys
        assert "key2" in keys
        assert len(keys) == 2


class TestFileValidator:
    """Тесты для FileValidator"""

    @pytest.fixture
    def file_validator(self):
        """Фикстура для FileValidator"""
        return FileValidator(
            allowed_extensions=[".jpg", ".png"],
            allowed_mime_types=["image/jpeg", "image/png"],
            max_size=1024 * 1024,  # 1MB
            max_dimensions=(1920, 1080),
            min_dimensions=(100, 100),
        )

    def test_validate_nonexistent_file(self, file_validator):
        """Тест валидации несуществующего файла"""
        result = file_validator.validate_file("nonexistent_file.jpg")

        assert result["valid"] is False
        assert "File does not exist" in result["errors"]

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("magic.from_file")
    def test_validate_file_too_large(
        self, mock_magic, mock_getsize, mock_exists, file_validator
    ):
        """Тест валидации слишком большого файла"""
        mock_exists.return_value = True
        mock_getsize.return_value = 2 * 1024 * 1024  # 2MB
        mock_magic.return_value = "image/jpeg"

        result = file_validator.validate_file("large_file.jpg")

        assert result["valid"] is False
        assert any("exceeds maximum" in error for error in result["errors"])

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("magic.from_file")
    def test_validate_invalid_extension(
        self, mock_magic, mock_getsize, mock_exists, file_validator
    ):
        """Тест валидации файла с недопустимым расширением"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        mock_magic.return_value = "image/jpeg"

        result = file_validator.validate_file("file.txt")

        assert result["valid"] is False
        assert any("extension" in error for error in result["errors"])

    @patch("os.path.exists")
    @patch("os.path.getsize")
    @patch("magic.from_file")
    def test_validate_invalid_mime_type(
        self, mock_magic, mock_getsize, mock_exists, file_validator
    ):
        """Тест валидации файла с недопустимым MIME типом"""
        mock_exists.return_value = True
        mock_getsize.return_value = 1024  # 1KB
        mock_magic.return_value = "text/plain"

        result = file_validator.validate_file("file.jpg")

        assert result["valid"] is False
        assert any("MIME type" in error for error in result["errors"])


class TestAuthMiddleware:
    """Тесты для AuthMiddleware"""

    @pytest.fixture
    def auth_middleware(self):
        """Фикстура для AuthMiddleware"""
        return AuthMiddleware("test_api_key", "test_admin_key")

    def test_requires_auth_protected_paths(self, auth_middleware):
        """Тест определения защищенных путей"""
        assert auth_middleware._requires_auth("/metrics") is True
        assert auth_middleware._requires_auth("/admin/users") is True
        assert auth_middleware._requires_auth("/api/data") is True
        assert auth_middleware._requires_auth("/health/live") is False
        assert auth_middleware._requires_auth("/public") is False

    def test_valid_api_key(self, auth_middleware):
        """Тест валидного API ключа"""
        # Этот тест требует мок HTTP запроса
        # В реальном тесте нужно будет замокать aiohttp Request
        pass

    def test_invalid_api_key(self, auth_middleware):
        """Тест невалидного API ключа"""
        # Этот тест требует мок HTTP запроса
        pass


class TestRateLimitMiddleware:
    """Тесты для RateLimitMiddleware"""

    @pytest.fixture
    def rate_limit_middleware(self):
        """Фикстура для RateLimitMiddleware"""
        return RateLimitMiddleware(max_requests=5, window_seconds=60)

    def test_get_client_ip_direct(self, rate_limit_middleware):
        """Тест получения IP адреса клиента напрямую"""
        # Мок HTTP запроса
        mock_request = Mock()
        mock_request.remote = "192.168.1.1"
        mock_request.headers = {}

        ip = rate_limit_middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_forwarded(self, rate_limit_middleware):
        """Тест получения IP адреса через X-Forwarded-For"""
        mock_request = Mock()
        mock_request.remote = "192.168.1.1"
        mock_request.headers = {"X-Forwarded-For": "203.0.113.1, 192.168.1.1"}

        ip = rate_limit_middleware._get_client_ip(mock_request)
        assert ip == "203.0.113.1"

    def test_check_rate_limit_within_limit(self, rate_limit_middleware):
        """Тест проверки лимита в пределах допустимого"""
        client_ip = "192.168.1.1"

        # Первые 5 запросов должны проходить
        for i in range(5):
            assert rate_limit_middleware._check_rate_limit(client_ip) is True

    def test_check_rate_limit_exceeded(self, rate_limit_middleware):
        """Тест проверки лимита при превышении"""
        client_ip = "192.168.1.1"

        # Первые 5 запросов проходят
        for i in range(5):
            assert rate_limit_middleware._check_rate_limit(client_ip) is True

        # 6-й запрос должен быть заблокирован
        assert rate_limit_middleware._check_rate_limit(client_ip) is False


class TestFileSecurityScanner:
    """Тесты для FileSecurityScanner"""

    @pytest.fixture
    def security_scanner(self):
        """Фикстура для FileSecurityScanner"""
        return FileSecurityScanner()

    def test_scan_safe_file(self, security_scanner, tmp_path):
        """Тест сканирования безопасного файла"""
        safe_file = tmp_path / "safe.txt"
        safe_file.write_text("This is a safe text file")

        result = security_scanner.scan_file(str(safe_file))

        assert result["safe"] is True
        assert result["risk_level"] == "low"
        assert len(result["threats"]) == 0

    def test_scan_malicious_file(self, security_scanner, tmp_path):
        """Тест сканирования вредоносного файла"""
        malicious_file = tmp_path / "malicious.txt"
        malicious_file.write_text("<?php system('rm -rf /'); ?>")

        result = security_scanner.scan_file(str(malicious_file))

        assert result["safe"] is False
        assert result["risk_level"] == "high"
        assert len(result["threats"]) > 0

    def test_scan_executable_file(self, security_scanner, tmp_path):
        """Тест сканирования исполняемого файла"""
        # Создаем файл с PE заголовком
        executable_file = tmp_path / "executable.exe"
        executable_file.write_bytes(b"MZ" + b"\x00" * 100)

        result = security_scanner.scan_file(str(executable_file))

        assert result["safe"] is False
        assert result["risk_level"] == "high"
        assert any("Executable file" in threat for threat in result["threats"])

    def test_is_executable(self, security_scanner):
        """Тест определения исполняемых файлов"""
        assert security_scanner._is_executable(b"MZ" + b"\x00" * 100) is True
        assert (
            security_scanner._is_executable(b"\x7fELF" + b"\x00" * 100) is True
        )
        assert (
            security_scanner._is_executable(b"PK\x03\x04" + b"\x00" * 100)
            is True
        )
        assert security_scanner._is_executable(b"This is just text") is False

    def test_has_suspicious_headers(self, security_scanner):
        """Тест определения подозрительных заголовков"""
        assert (
            security_scanner._has_suspicious_headers(
                b"PK\x03\x04" + b"\x00" * 100
            )
            is True
        )
        assert (
            security_scanner._has_suspicious_headers(b"Rar!" + b"\x00" * 100)
            is True
        )
        assert (
            security_scanner._has_suspicious_headers(
                b"\x1f\x8b" + b"\x00" * 100
            )
            is True
        )
        assert (
            security_scanner._has_suspicious_headers(b"This is just text")
            is False
        )
