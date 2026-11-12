"""Пользовательские валидаторы приложения «Блюда»."""
from django.core.exceptions import ValidationError

# Наибольший допустимый размер фотографии блюда, мегабайт.
MAX_IMAGE_SIZE_MB = 2


def validate_image_size(image):
    """Не принимать фотографии блюд больше MAX_IMAGE_SIZE_MB."""
    if image.size > MAX_IMAGE_SIZE_MB * 1024 * 1024:
        raise ValidationError(
            f"Размер файла не должен превышать {MAX_IMAGE_SIZE_MB} МБ."
        )
