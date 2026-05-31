from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError

from .models import Item, Outfit
from django import forms


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ['name', 'category', 'season', 'color', 'brand', 'sku', 'image']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control border-0 bg-light'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'image':
                field.widget.attrs.update({
                    'class': 'form-control border-0 bg-light',
                    'style': 'border-radius: 0; padding: 12px;',
                })
class SignUpForm(UserCreationForm):
    username = forms.CharField(label="Логин (для входа, без пробелов)", help_text="Например: anna_m")

    first_name = forms.CharField(label="Имя и Фамилия", required=True, help_text="Например: Анна Малышка")

    email = forms.EmailField(label="Электронная почта", required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "email")

    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        self.fields['password1'].label = "Пароль"
        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['password1'].help_text = ""

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control border-0 bg-light',
                'style': 'border-radius: 0; padding: 12px;'
            })


class OutfitForm(forms.ModelForm):
    class Meta:
        model = Outfit
        fields = ['name', 'items', 'image']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Делаем оба поля НЕ обязательными
        self.fields['name'].required = False
        self.fields['items'].required = False

        if self.user:
            self.fields['items'].queryset = Item.objects.filter(user=self.user)

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')
        items = cleaned_data.get('items')

        # Проверка имени
        if not name:
            self.add_error('name', "Введите название комплекта")
        elif self.user:
            exists = Outfit.objects.filter(user=self.user, name__iexact=name)
            if self.instance.pk:
                exists = exists.exclude(pk=self.instance.pk)
            if exists.exists():
                self.add_error('name', "У вас уже есть комплект с таким названием!")

        # Проверка предметов
        if not items or items.count() < 2:
            self.add_error('items', "Комплект должен состоять минимум из двух вещей.")

        return cleaned_data