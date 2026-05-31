from django.contrib import admin
from .models import Item, Outfit, Event

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'user', 'created_at') # что видим в списке
    list_filter = ('category', 'season', 'user')            # фильтры справа
    search_fields = ('name', 'brand')                       # поиск

@admin.register(Outfit)
class OutfitAdmin(admin.ModelAdmin):
    list_display = ('name', 'user')
    filter_horizontal = ('items',) # удобный интерфейс для выбора вещей в комплект

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('date', 'user', 'outfit')
    list_filter = ('date', 'user')