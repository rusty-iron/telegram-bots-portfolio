"""
Утилиты для валидации загружаемых файлов
"""

import os
from typing import Any, Dict, List, Optional

import magic
import structlog
from PIL import Image

logger = structlog.get_logger()


class FileValidator:
    """Валидатор для загружаемых файлов"""

    def __init__(
        self,
        allowed_extensions: List[str] = None,
        allowed_mime_types: List[str] = None,
        max_size: int = 5 * 1024 * 1024,  # 5MB
        max_dimensions: tuple = (4096, 4096),
        min_dimensions: tuple = (100, 100),
    ):
        self.allowed_extensions = allowed_extensions or [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
        ]
        self.allowed_mime_types = allowed_mime_types or [
            "image/jpeg",
            "image/png",
            "image/webp",
        ]
        self.max_size = max_size
        self.max_dimensions = max_dimensions
        self.min_dimensions = min_dimensions

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Валидирует файл по всем параметрам"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "file_info": {},
        }

        try:
            # Проверяем существование файла
            if not os.path.exists(file_path):
                validation_result["valid"] = False
                validation_result["errors"].append("File does not exist")
                return validation_result

            # Получаем информацию о файле
            file_info = self._get_file_info(file_path)
            validation_result["file_info"] = file_info

            # Проверяем размер файла
            if not self._validate_file_size(file_info["size"]):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"File size {
                        file_info['size']} exceeds maximum {
                        self.max_size}")

            # Проверяем расширение файла
            if not self._validate_extension(file_info["extension"]):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"File extension {file_info['extension']} not allowed"
                )

            # Проверяем MIME тип
            if not self._validate_mime_type(file_info["mime_type"]):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"MIME type {file_info['mime_type']} not allowed"
                )

            # Проверяем изображение (если это изображение)
            if file_info["mime_type"].startswith("image/"):
                image_validation = self._validate_image(file_path)
                if not image_validation["valid"]:
                    validation_result["valid"] = False
                    validation_result["errors"].extend(
                        image_validation["errors"])
                validation_result["warnings"].extend(
                    image_validation["warnings"])

            # Проверяем на вредоносный контент
            if not self._scan_for_malware(file_path):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    "File appears to be malicious")

        except Exception as e:
            validation_result["valid"] = False
            validation_result["errors"].append(f"Validation error: {str(e)}")
            logger.error(
                "file_validation_error",
                file_path=file_path,
                error=str(e))

        return validation_result

    def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Получает информацию о файле"""
        file_info = {}

        # Размер файла
        file_info["size"] = os.path.getsize(file_path)

        # Расширение файла
        _, ext = os.path.splitext(file_path)
        file_info["extension"] = ext.lower()

        # MIME тип
        try:
            file_info["mime_type"] = magic.from_file(file_path, mime=True)
        except Exception:
            file_info["mime_type"] = "unknown"

        # Имя файла
        file_info["filename"] = os.path.basename(file_path)

        return file_info

    def _validate_file_size(self, size: int) -> bool:
        """Проверяет размер файла"""
        return size <= self.max_size

    def _validate_extension(self, extension: str) -> bool:
        """Проверяет расширение файла"""
        return extension in self.allowed_extensions

    def _validate_mime_type(self, mime_type: str) -> bool:
        """Проверяет MIME тип файла"""
        return mime_type in self.allowed_mime_types

    def _validate_image(self, file_path: str) -> Dict[str, Any]:
        """Валидирует изображение"""
        result = {"valid": True, "errors": [], "warnings": []}

        try:
            with Image.open(file_path) as img:
                width, height = img.size

                # Проверяем размеры изображения
                if width > self.max_dimensions[0] or height > self.max_dimensions[1]:
                    result["valid"] = False
                    result["errors"].append(
                        f"Image dimensions {width}x{height} exceed maximum {
                            self.max_dimensions}")

                if width < self.min_dimensions[0] or height < self.min_dimensions[1]:
                    result["warnings"].append(
                        f"Image dimensions {width}x{height} are below recommended minimum {
                            self.min_dimensions}")

                # Проверяем формат изображения
                if img.format not in ["JPEG", "PNG", "WEBP"]:
                    result["valid"] = False
                    result["errors"].append(
                        f"Unsupported image format: {
                            img.format}")

                # Проверяем на повреждения
                try:
                    img.verify()
                except Exception:
                    result["valid"] = False
                    result["errors"].append("Image appears to be corrupted")

        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Image validation error: {str(e)}")

        return result

    def _scan_for_malware(self, file_path: str) -> bool:
        """Сканирует файл на наличие вредоносного контента"""
        try:
            # Проверяем на подозрительные паттерны
            with open(file_path, "rb") as f:
                content = f.read(1024)  # Читаем первые 1024 байта

                # Проверяем на исполняемые файлы
                executable_signatures = [
                    b"MZ",  # PE файлы
                    b"\x7fELF",  # ELF файлы
                    b"\xfe\xed\xfa",  # Mach-O файлы
                ]

                for signature in executable_signatures:
                    if content.startswith(signature):
                        logger.warning(
                            "executable_file_detected",
                            file_path=file_path)
                        return False

                # Проверяем на подозрительные строки
                suspicious_strings = [
                    b"<script",
                    b"javascript:",
                    b"eval(",
                    b"exec(",
                    b"system(",
                ]

                for suspicious in suspicious_strings:
                    if suspicious in content:
                        logger.warning(
                            "suspicious_content_detected",
                            file_path=file_path)
                        return False

            return True

        except Exception as e:
            logger.error(
                "malware_scan_error",
                file_path=file_path,
                error=str(e))
            return False


class ImageProcessor:
    """Процессор для обработки изображений"""

    def __init__(self, max_size: int = 5 * 1024 * 1024):
        self.max_size = max_size

    def process_image(self, input_path: str, output_path: str,
                      **kwargs) -> Dict[str, Any]:
        """Обрабатывает изображение"""
        result = {"success": False, "errors": [], "file_info": {}}

        try:
            with Image.open(input_path) as img:
                # Конвертируем в RGB если необходимо
                if img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                # Изменяем размер если необходимо
                if "resize" in kwargs:
                    img = img.resize(
                        kwargs["resize"], Image.Resampling.LANCZOS)

                # Оптимизируем качество
                quality = kwargs.get("quality", 85)

                # Сохраняем изображение
                img.save(output_path, "JPEG", quality=quality, optimize=True)

                # Получаем информацию о результирующем файле
                result["file_info"] = {
                    "size": os.path.getsize(output_path),
                    "format": "JPEG",
                    "dimensions": img.size,
                }

                result["success"] = True

        except Exception as e:
            result["errors"].append(str(e))
            logger.error(
                "image_processing_error",
                input_path=input_path,
                error=str(e))

        return result

    def create_thumbnail(
        self, input_path: str, output_path: str, size: tuple = (300, 300)
    ) -> Dict[str, Any]:
        """Создает миниатюру изображения"""
        return self.process_image(
            input_path,
            output_path,
            resize=size,
            quality=75)

    def optimize_image(self, input_path: str,
                       output_path: str) -> Dict[str, Any]:
        """Оптимизирует изображение"""
        return self.process_image(input_path, output_path, quality=85)


class FileSecurityScanner:
    """Сканер безопасности файлов"""

    def __init__(self):
        self.malicious_patterns = [
            # PHP код
            b"<?php",
            b"<?=",
            # JavaScript
            b"<script",
            b"javascript:",
            # SQL инъекции
            b"union select",
            b"drop table",
            # Системные команды
            b"system(",
            b"exec(",
            b"eval(",
        ]

    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Сканирует файл на наличие угроз"""
        result = {"safe": True, "threats": [], "risk_level": "low"}

        try:
            with open(file_path, "rb") as f:
                content = f.read()

                # Проверяем на подозрительные паттерны
                for pattern in self.malicious_patterns:
                    if pattern in content.lower():
                        result["threats"].append(
                            f"Malicious pattern detected: {
                                pattern.decode()}")
                        result["safe"] = False
                        result["risk_level"] = "high"

                # Проверяем на исполняемые файлы
                if self._is_executable(content):
                    result["threats"].append("Executable file detected")
                    result["safe"] = False
                    result["risk_level"] = "high"

                # Проверяем на подозрительные заголовки
                if self._has_suspicious_headers(content):
                    result["threats"].append(
                        "Suspicious file headers detected")
                    result["safe"] = False
                    result["risk_level"] = "medium"

        except Exception as e:
            result["safe"] = False
            result["threats"].append(f"Scan error: {str(e)}")
            result["risk_level"] = "high"
            logger.error(
                "security_scan_error",
                file_path=file_path,
                error=str(e))

        return result

    def _is_executable(self, content: bytes) -> bool:
        """Проверяет, является ли файл исполняемым"""
        executable_signatures = [
            b"MZ",  # PE файлы
            b"\x7fELF",  # ELF файлы
            b"\xfe\xed\xfa",  # Mach-O файлы
            b"\xca\xfe\xba\xbe",  # Java class files
        ]

        return any(content.startswith(sig) for sig in executable_signatures)

    def _has_suspicious_headers(self, content: bytes) -> bool:
        """Проверяет на подозрительные заголовки"""
        suspicious_headers = [
            b"PK\x03\x04",  # ZIP файлы
            b"Rar!",  # RAR файлы
            b"\x1f\x8b",  # GZIP файлы
        ]

        return any(content.startswith(header) for header in suspicious_headers)


# Глобальные экземпляры
_file_validator: Optional[FileValidator] = None
_image_processor: Optional[ImageProcessor] = None
_security_scanner: Optional[FileSecurityScanner] = None


def init_file_validation_services() -> None:
    """Инициализирует сервисы валидации файлов"""
    global _file_validator, _image_processor, _security_scanner

    _file_validator = FileValidator()
    _image_processor = ImageProcessor()
    _security_scanner = FileSecurityScanner()

    logger.info("file_validation_services_initialized")


def get_file_validator() -> FileValidator:
    """Получает валидатор файлов"""
    if _file_validator is None:
        raise RuntimeError("File validation services not initialized")
    return _file_validator


def get_image_processor() -> ImageProcessor:
    """Получает процессор изображений"""
    if _image_processor is None:
        raise RuntimeError("File validation services not initialized")
    return _image_processor


def get_security_scanner() -> FileSecurityScanner:
    """Получает сканер безопасности"""
    if _security_scanner is None:
        raise RuntimeError("File validation services not initialized")
    return _security_scanner
