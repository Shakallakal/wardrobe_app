from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db.models.signals import m2m_changed
from django.dispatch import receiver


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Электронная почта обязательна')
        email = self.normalize_email(email)
        extra_fields.setdefault('username', email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    email = models.EmailField(unique=True, verbose_name="Электронная почта")
    first_name = models.CharField(max_length=150, verbose_name="Имя")

    username = models.CharField(max_length=150, unique=True, blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name']

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email


class Item(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField(max_length=100, verbose_name="Название предмета")

    CATEGORY_CHOICES = [
        ('outerwear', 'Верхняя одежда'),
        ('top', 'Верх'),
        ('bottom', 'Низ'),
        ('dresses', 'Платья и комбинезоны'),
        ('suits', 'Костюмы'),
        ('lingerie', 'Белье'),
        ('shoes', 'Обувь'),
        ('accessory', 'Аксессуары'),
    ]

    SEASON_CHOICES = [
        ('all', 'Любой сезон'),
        ('summer', 'Лето'),
        ('winter', 'Зима'),
        ('spring_autumn', 'Весна / Осень'),
    ]

    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, verbose_name="Категория")
    season = models.CharField(max_length=20, choices=SEASON_CHOICES, default='all', verbose_name="Сезон")
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Цвет")
    brand = models.CharField(max_length=100, blank=True, null=True, verbose_name="Бренд")
    sku = models.CharField(max_length=100, blank=True, null=True, verbose_name="Артикул")
    image = models.ImageField(upload_to='items/', blank=True, null=True, verbose_name="Изображение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата добавления")

    class Meta:
        verbose_name = "Предмет одежды"
        verbose_name_plural = "Предметы одежды"

    def __str__(self):
        return f"{self.name} ({self.user.first_name})"


class Outfit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    name = models.CharField(max_length=100, verbose_name="Название комплекта")
    items = models.ManyToManyField(Item, related_name='outfits', verbose_name="Предметы в комплекте")
    image = models.ImageField(upload_to='outfits/', blank=True, null=True, verbose_name="Фото комплекта")

    class Meta:
        verbose_name = "Комплект"
        verbose_name_plural = "Комплекты"

    def __str__(self):
        return self.name


class Event(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец")
    date = models.DateField(verbose_name="Дата события")
    description = models.TextField(blank=True, null=True, verbose_name="Описание события")
    outfit = models.ForeignKey(Outfit, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Выбранный комплект")

    class Meta:
        verbose_name = "Событие"
        verbose_name_plural = "События"
        ordering = ['-date']

@receiver(m2m_changed, sender=Outfit.items.through)
def delete_empty_outfit(sender, instance, action, **kwargs):
    # Проверяем только когда предметы удаляются из комплекта
    if action == 'post_remove' or action == 'post_clear':
        if instance.items.count() == 0:
            # Удаляем комплект, если в нем не осталось предметов
            instance.delete()