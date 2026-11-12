"""Формы приложения «Меню»: фильтрация списка и запись меню."""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from dishes.models import Dish
from menu.models import MenuEntry
from users.models import User

# Варианты сортировки списка меню. Ключи совпадают с ENTRY_SORT_FIELDS
# в menu/views.py: пользователь выбирает короткое значение, а поля
# order_by() подставляет представление.
SORT_CHOICES = [
    ("date", "дате"),
    ("dish", "блюду"),
    ("user", "пользователю"),
    ("calories", "калорийности"),
]


class MenuFilterForm(forms.Form):
    """Параметры фильтрации списка меню (GET-запрос).

    Имена полей совпадают с прежними GET-параметрами, поэтому ссылки
    пагинации и закладки продолжают работать. Номер страницы page в
    форму не входит: он относится к пагинации, а не к фильтрам.
    """

    date = forms.DateField(
        required=False,
        label="Дата",
        widget=forms.DateInput(
            # type="date" включает календарь браузера; браузер
            # передаёт и ожидает дату в формате ГГГГ-ММ-ДД.
            format="%Y-%m-%d",
            attrs={"type": "date", "class": "form-control"},
        ),
    )
    dish = forms.ModelChoiceField(
        queryset=Dish.objects.order_by("name"),
        required=False,
        label="Блюдо",
        empty_label="Все блюда",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    user = forms.ModelChoiceField(
        queryset=User.objects.order_by("name"),
        required=False,
        label="Пользователь",
        empty_label="Все",
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    status = forms.ChoiceField(
        required=False,
        label="Статус",
        choices=[("", "Кроме отменённых"), *MenuEntry.Status.choices],
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    q = forms.CharField(
        required=False,
        max_length=100,
        label="Поиск",
        widget=forms.TextInput(attrs={
            "type": "search",
            "class": "form-control",
            "placeholder": "блюдо или имя",
        }),
    )
    sort = forms.ChoiceField(
        required=False,
        label="Сортировать по",
        choices=SORT_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def clean_q(self):
        """Поисковая строка: без лишних пробелов, не короче 2 символов."""
        query = " ".join(self.cleaned_data["q"].split())
        if len(query) == 1:
            raise ValidationError("Введите для поиска хотя бы 2 символа.")
        return query


class MenuEntryForm(forms.ModelForm):
    """Создание и редактирование записи меню.

    Поле status в форму не входит: новая запись получает статус
    «Запланировано» по умолчанию, а при редактировании статус
    сохраняется. Отмена выполняется отдельным действием.
    """

    class Meta:
        model = MenuEntry
        fields = ["dish", "menu_date", "user"]
        labels = {
            "dish": "Блюдо",
            "menu_date": "Дата",
            "user": "Пользователь",
        }
        help_texts = {
            "dish": "Блюдо не может повторяться в меню пользователя "
                    "на один день.",
            "menu_date": "День, на который планируется блюдо; "
                         "прошедшую дату выбрать нельзя.",
        }
        widgets = {
            "dish": forms.Select(attrs={"class": "form-select"}),
            "menu_date": forms.DateInput(
                format="%Y-%m-%d",
                attrs={"type": "date", "class": "form-control"},
            ),
            "user": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_menu_date(self):
        """Дата меню не может быть в прошлом.

        Исключение – редактирование записи без смены даты: старую
        запись можно поправить (например, заменить блюдо), не перенося
        её на другой день.
        """
        menu_date = self.cleaned_data["menu_date"]
        unchanged = (
            self.instance.pk is not None
            and menu_date == self.initial.get("menu_date")
        )
        if menu_date < timezone.localdate() and not unchanged:
            raise ValidationError(
                "Нельзя запланировать блюдо на прошедшую дату."
            )
        return menu_date

    def clean(self):
        """Проверка нескольких полей: блюдо и дневной лимит пользователя."""
        cleaned_data = super().clean()
        dish = cleaned_data.get("dish")
        user = cleaned_data.get("user")
        # Проверяем только если оба поля прошли стандартную валидацию.
        if dish and user and dish.calories > user.daily_limit:
            raise ValidationError(
                f"Калорийность блюда ({dish.calories} ккал) больше "
                f"дневного лимита пользователя ({user.daily_limit} ккал)."
            )
        return cleaned_data
