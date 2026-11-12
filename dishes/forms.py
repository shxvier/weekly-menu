"""Формы приложения «Блюда»."""
from django import forms
from django.core.exceptions import ValidationError

from dishes.models import Dish


class DishForm(forms.ModelForm):
    """Создание и редактирование блюда, включая загрузку фотографии.

    slug и is_light в форму не входят: slug формируется при первом
    сохранении, is_light вычисляет база данных.
    """

    class Meta:
        model = Dish
        fields = ["name", "calories", "dish_type", "image"]
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
                "accept": "image/*",
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
