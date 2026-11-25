"""Формы приложения «Блюда»."""
from pathlib import Path

from django import forms
from django.core.exceptions import ValidationError

from dishes.models import Dish


class DishPhotoField(forms.ImageField):
    formats = {
        ".jpg": "JPEG",
        ".jpeg": "JPEG",
        ".png": "PNG",
        ".webp": "WEBP",
    }

    def to_python(self, data):
        photo = super().to_python(data)
        if photo is not None:
            expected_format = self.formats.get(Path(photo.name).suffix.lower())
            if expected_format != photo.image.format:
                raise ValidationError(
                    "Загрузите фотографию в формате JPG, PNG или WebP "
                    "с соответствующим расширением."
                )
        return photo


class DishForm(forms.ModelForm):
    """Создание и редактирование блюда, включая загрузку фотографии.

    slug и is_light в форму не входят: slug формируется при первом
    сохранении, is_light вычисляет база данных.
    """

    class Meta:
        model = Dish
        fields = ["name", "calories", "dish_type", "image"]
        field_classes = {"image": DishPhotoField}
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "например, Сырники со сметаной",
            }),
            "calories": forms.NumberInput(attrs={
                "class": "form-control",
                "min": 1,
            }),
            "dish_type": forms.Select(attrs={"class": "form-select"}),
            # accept подсказывает браузеру, какие файлы показывать;
            # настоящую проверку выполняет ImageField на сервере.
            "image": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/jpeg,image/png,image/webp",
            }),
        }

    def clean_name(self):
        """Название без лишних пробелов и без повторов (регистр не важен)."""
        name = " ".join(self.cleaned_data["name"].split())
        duplicates = Dish.objects.filter(name__iexact=name)
        if self.instance.pk is not None:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise ValidationError("Блюдо с таким названием уже есть.")
        return name
