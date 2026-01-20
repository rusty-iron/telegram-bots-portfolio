"""
Сервис для оптимизации изображений
"""

import io
from pathlib import Path
from typing import Optional, Tuple

import structlog
from PIL import Image, ImageOps

logger = structlog.get_logger()


class ImageOptimizationService:
    """Сервис для оптимизации изображений"""

    # Стандартные размеры для разных типов изображений
    THUMBNAIL_SIZE = (150, 150)
    CATEGORY_IMAGE_SIZE = (300, 300)
    PRODUCT_IMAGE_SIZE = (400, 400)
    LARGE_IMAGE_SIZE = (800, 800)

    # Качество сжатия
    JPEG_QUALITY = 85
    WEBP_QUALITY = 80

    # Поддерживаемые форматы
    SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff"}

    def __init__(self, base_path: str = "static/images"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def optimize_image(
        self,
        image_data: bytes,
        output_format: str = "WEBP",
        max_size: Optional[Tuple[int, int]] = None,
        quality: Optional[int] = None,
    ) -> bytes:
        """Оптимизировать изображение"""
        try:
            # Открываем изображение
            image = Image.open(io.BytesIO(image_data))

            # Конвертируем в RGB если нужно
            if image.mode in ("RGBA", "LA", "P"):
                # Создаем белый фон для прозрачных изображений
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                background.paste(
                    image,
                    mask=image.split()[-1] if image.mode == "RGBA" else None,
                )
                image = background
            elif image.mode != "RGB":
                image = image.convert("RGB")

            # Изменяем размер если нужно
            if max_size:
                image = ImageOps.fit(image, max_size, Image.Resampling.LANCZOS)

            # Оптимизируем
            image = ImageOps.exif_transpose(image)  # Исправляем ориентацию

            # Сохраняем в нужном формате
            output = io.BytesIO()

            if output_format.upper() == "WEBP":
                quality = quality or self.WEBP_QUALITY
                image.save(
                    output, format="WEBP", quality=quality, optimize=True
                )
            elif output_format.upper() == "JPEG":
                quality = quality or self.JPEG_QUALITY
                image.save(
                    output, format="JPEG", quality=quality, optimize=True
                )
            else:
                image.save(output, format=output_format.upper(), optimize=True)

            return output.getvalue()

        except Exception as e:
            logger.error("image_optimization_error", error=str(e))
            raise

    def create_thumbnail(self, image_data: bytes) -> bytes:
        """Создать миниатюру изображения"""
        return self.optimize_image(
            image_data,
            output_format="WEBP",
            max_size=self.THUMBNAIL_SIZE,
            quality=self.WEBP_QUALITY,
        )

    def create_category_image(self, image_data: bytes) -> bytes:
        """Создать изображение для категории"""
        return self.optimize_image(
            image_data,
            output_format="WEBP",
            max_size=self.CATEGORY_IMAGE_SIZE,
            quality=self.WEBP_QUALITY,
        )

    def create_product_image(self, image_data: bytes) -> bytes:
        """Создать изображение для товара"""
        return self.optimize_image(
            image_data,
            output_format="WEBP",
            max_size=self.PRODUCT_IMAGE_SIZE,
            quality=self.WEBP_QUALITY,
        )

    def create_large_image(self, image_data: bytes) -> bytes:
        """Создать большое изображение"""
        return self.optimize_image(
            image_data,
            output_format="WEBP",
            max_size=self.LARGE_IMAGE_SIZE,
            quality=self.WEBP_QUALITY,
        )

    def save_optimized_image(
        self, image_data: bytes, filename: str, image_type: str = "product"
    ) -> str:
        """Сохранить оптимизированное изображение"""
        try:
            # Определяем путь для сохранения
            if image_type == "category":
                save_path = self.base_path / "categories"
                optimized_data = self.create_category_image(image_data)
            elif image_type == "product":
                save_path = self.base_path / "products"
                optimized_data = self.create_product_image(image_data)
            else:
                save_path = self.base_path / "general"
                optimized_data = self.optimize_image(image_data)

            # Создаем директорию если не существует
            save_path.mkdir(parents=True, exist_ok=True)

            # Генерируем имя файла
            base_name = Path(filename).stem
            webp_filename = f"{base_name}.webp"
            full_path = save_path / webp_filename

            # Сохраняем файл
            with open(full_path, "wb") as f:
                f.write(optimized_data)

            # Возвращаем относительный путь
            relative_path = str(full_path.relative_to(self.base_path))
            logger.info("image_saved", path=relative_path, type=image_type)

            return relative_path

        except Exception as e:
            logger.error("image_save_error", filename=filename, error=str(e))
            raise

    def create_multiple_sizes(
        self,
        image_data: bytes,
        base_filename: str,
        image_type: str = "product",
    ) -> dict:
        """Создать изображения разных размеров"""
        try:
            results = {}

            if image_type == "product":
                # Создаем миниатюру
                thumbnail_data = self.create_thumbnail(image_data)
                thumbnail_path = self._save_image_data(
                    thumbnail_data, base_filename, "thumb", "products"
                )
                results["thumbnail"] = thumbnail_path

                # Создаем основное изображение
                main_data = self.create_product_image(image_data)
                main_path = self._save_image_data(
                    main_data, base_filename, "main", "products"
                )
                results["main"] = main_path

                # Создаем большое изображение
                large_data = self.create_large_image(image_data)
                large_path = self._save_image_data(
                    large_data, base_filename, "large", "products"
                )
                results["large"] = large_path

            elif image_type == "category":
                # Создаем изображение категории
                category_data = self.create_category_image(image_data)
                category_path = self._save_image_data(
                    category_data, base_filename, "main", "categories"
                )
                results["main"] = category_path

            return results

        except Exception as e:
            logger.error(
                "multiple_sizes_error", filename=base_filename, error=str(e)
            )
            raise

    def _save_image_data(
        self,
        image_data: bytes,
        base_filename: str,
        size_suffix: str,
        subdirectory: str,
    ) -> str:
        """Сохранить данные изображения"""
        save_path = self.base_path / subdirectory
        save_path.mkdir(parents=True, exist_ok=True)

        base_name = Path(base_filename).stem
        filename = f"{base_name}_{size_suffix}.webp"
        full_path = save_path / filename

        with open(full_path, "wb") as f:
            f.write(image_data)

        return str(full_path.relative_to(self.base_path))

    def delete_image(self, image_path: str) -> bool:
        """Удалить изображение"""
        try:
            full_path = self.base_path / image_path
            if full_path.exists():
                full_path.unlink()
                logger.info("image_deleted", path=image_path)
                return True
            return False
        except Exception as e:
            logger.error("image_delete_error", path=image_path, error=str(e))
            return False

    def get_image_info(self, image_data: bytes) -> dict:
        """Получить информацию об изображении"""
        try:
            image = Image.open(io.BytesIO(image_data))
            return {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "width": image.width,
                "height": image.height,
                "has_transparency": image.mode in ("RGBA", "LA")
                or "transparency" in image.info,
            }
        except Exception as e:
            logger.error("image_info_error", error=str(e))
            return {}

    def validate_image(self, image_data: bytes) -> bool:
        """Проверить валидность изображения"""
        try:
            image = Image.open(io.BytesIO(image_data))
            image.verify()
            return True
        except Exception as e:
            logger.error("image_validation_error", error=str(e))
            return False

    def get_file_size_reduction(
        self, original_data: bytes, optimized_data: bytes
    ) -> dict:
        """Получить информацию о сжатии"""
        original_size = len(original_data)
        optimized_size = len(optimized_data)
        reduction_percent = (
            (original_size - optimized_size) / original_size
        ) * 100

        return {
            "original_size": original_size,
            "optimized_size": optimized_size,
            "reduction_bytes": original_size - optimized_size,
            "reduction_percent": round(reduction_percent, 2),
        }
