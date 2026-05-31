import calendar
from datetime import date, timedelta, datetime

import requests
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from .models import Item, Outfit, Event
from django.contrib.auth import login
from .forms import SignUpForm, ItemForm, OutfitForm


@login_required
def index(request):
    items = Item.objects.filter(user=request.user)

    search_query = request.GET.get('q')
    if search_query:
        items = items.filter(name__icontains=search_query)

    user_brands = Item.objects.filter(user=request.user).exclude(brand__isnull=True).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
    user_colors = Item.objects.filter(user=request.user).exclude(color__isnull=True).exclude(color='').values_list('color', flat=True).distinct().order_by('color')

    category = request.GET.get('category')
    season = request.GET.get('season')
    brand = request.GET.get('brand')
    color = request.GET.get('color')

    if category: items = items.filter(category=category)
    if season: items = items.filter(season=season)
    if brand: items = items.filter(brand=brand)
    if color: items = items.filter(color=color)

    context = {
        'items': items,
        'brands': user_brands,
        'colors': user_colors,
        'category_choices': Item.CATEGORY_CHOICES,
        'season_choices': Item.SEASON_CHOICES,
        'search_query': search_query,
    }
    return render(request, 'wardrobe/index.html', context)


def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    else:
        form = SignUpForm()
    return render(request, 'wardrobe/signup.html', {'form': form})


@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            return redirect('index')
    else:
        form = ItemForm()
    return render(request, 'wardrobe/add_item.html', {'form': form})


@login_required
def edit_item(request, item_id):
    item = Item.objects.get(id=item_id, user=request.user)
    if request.method == 'POST':
        # Обработка удаления фото
        if request.POST.get('clear_image') == 'true':
            if item.image:
                item.image.delete(save=False)
                item.image = None
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            return redirect('index')
    else:
        form = ItemForm(instance=item)
    return render(request, 'wardrobe/add_item.html', {'form': form, 'edit_mode': True})


@login_required
def delete_item(request, item_id):
    item = get_object_or_404(Item, id=item_id, user=request.user)

    if request.method == 'POST':
        # Находим все комплекты, в которых есть этот предмет
        affected_outfits = list(Outfit.objects.filter(items=item))

        # Удаляем предмет
        item.delete()

        # Удаляем комплекты, в которых не осталось предметов
        for outfit in affected_outfits:
            # Обновляем из базы, так как связь могла измениться
            outfit = Outfit.objects.get(id=outfit.id)
            if outfit.items.count() == 0:
                outfit.delete()

        return redirect('index')

    return redirect('index')

@login_required
def outfit_list(request):
    outfits = Outfit.objects.filter(user=request.user)
    return render(request, 'wardrobe/outfit_list.html', {'outfits': outfits})


@login_required
def add_outfit(request):
    items = Item.objects.filter(user=request.user)

    selected_ids = request.GET.getlist('selected')

    user_brands = items.exclude(brand__isnull=True).exclude(brand='').values_list('brand', flat=True).distinct().order_by('brand')
    user_colors = items.exclude(color__isnull=True).exclude(color='').values_list('color', flat=True).distinct().order_by('color')

    category = request.GET.get('category')
    season = request.GET.get('season')
    brand = request.GET.get('brand')
    color = request.GET.get('color')

    if category: items = items.filter(category=category)
    if season: items = items.filter(season=season)
    if brand: items = items.filter(brand=brand)
    if color: items = items.filter(color=color)

    if request.method == 'POST':
        form = OutfitForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            outfit = form.save(commit=False)
            outfit.user = request.user
            outfit.save()
            form.save_m2m()
            return redirect('outfit_list')
    else:
        form = OutfitForm(user=request.user)

    return render(request, 'wardrobe/outfit_form.html', {
        'form': form,
        'user_items': items,
        'brands': user_brands,
        'colors': user_colors,
        'category_choices': Item.CATEGORY_CHOICES,
        'season_choices': Item.SEASON_CHOICES,
        'selected_ids': selected_ids,
    })


@login_required
def edit_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)

    items = Item.objects.filter(user=request.user)

    category = request.GET.get('category')
    season = request.GET.get('season')
    brand = request.GET.get('brand')
    color = request.GET.get('color')

    if category: items = items.filter(category=category)
    if season: items = items.filter(season=season)
    if brand: items = items.filter(brand=brand)
    if color: items = items.filter(color=color)

    if 'selected' in request.GET:
        selected_ids = request.GET.getlist('selected')
    else:
        selected_ids = list(outfit.items.values_list('id', flat=True))

    if request.method == 'POST':
        # Обработка удаления фото
        if request.POST.get('clear_image') == 'true':
            if outfit.image:
                outfit.image.delete(save=False)
                outfit.image = None
        form = OutfitForm(request.POST, request.FILES, instance=outfit, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('outfit_list')
    else:
        form = OutfitForm(instance=outfit, user=request.user)

    return render(request, 'wardrobe/outfit_form.html', {
        'form': form,
        'outfit': outfit,
        'user_items': items,
        'selected_ids': [str(id) for id in selected_ids],
        'brands': Item.objects.filter(user=request.user).exclude(brand='').values_list('brand', flat=True).distinct(),
        'colors': Item.objects.filter(user=request.user).exclude(color='').values_list('color', flat=True).distinct(),
        'category_choices': Item.CATEGORY_CHOICES,
        'season_choices': Item.SEASON_CHOICES,
    })


@login_required
def delete_outfit(request, outfit_id):
    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)
    if request.method == 'POST':
        # Удаляем все события, связанные с этим комплектом
        Event.objects.filter(outfit=outfit).delete()
        # Удаляем сам комплект
        outfit.delete()
    return redirect('outfit_list')


@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id, user=request.user)
    event.delete()
    return redirect('outfit_calendar')


# Вспомогательная функция для получения погоды
def get_weather_info(city, target_date=None):
    api_key = "6efa76f7899e516bc82c9f6b3267bc3a"

    if target_date:
        url = f"https://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric&lang=ru"
        try:
            response = requests.get(url, timeout=10).json()
            for item in response['list']:
                if item['dt_txt'].split()[0] == target_date:
                    temp = round(item['main']['temp'])
                    desc = item['weather'][0]['description']
                    break
            else:
                return None
        except:
            return None
    else:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=ru"
        try:
            response = requests.get(url, timeout=10).json()
            temp = round(response['main']['temp'])
            desc = response['weather'][0]['description']
        except:
            return None

    if temp > 22:
        advice = "Солнечно и жарко, выбирайте легкие ткани."
    elif 15 <= temp <= 22:
        advice = "Приятная погода, подойдет легкий верх или рубашка."
    elif 5 <= temp < 15:
        advice = "Прохладно, не забудьте тренч или легкую куртку."
    else:
        advice = "На улице холодно, выбирайте самое теплое пальто."

    return {
        'temp': temp,
        'desc': desc.capitalize(),
        'advice': advice,
        'city': city.capitalize()
    }


@login_required
def outfit_calendar(request):
    today = date.today()
    date_str = request.GET.get('date', today.strftime('%Y-%m-%d'))
    selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()

    start_date = selected_date - timedelta(days=14)
    days_range = [start_date + timedelta(days=i) for i in range(45)]

    events_today = Event.objects.filter(user=request.user, date=selected_date).select_related('outfit')[:3]
    all_outfits = Outfit.objects.filter(user=request.user)
    can_add_more = events_today.count() < 3
    dates_with_events = Event.objects.filter(user=request.user, date__in=days_range).values_list('date', flat=True).distinct()

    return render(request, 'wardrobe/calendar.html', {
        'days_range': days_range,
        'selected_date': selected_date,
        'events_today': events_today,
        'all_outfits': all_outfits,
        'can_add_more': can_add_more,
        'can_create_event': all_outfits.exists(),
        'dates_with_events': dates_with_events,
        'today': today,
    })


@login_required
def save_event(request):
    if request.method == 'POST':
        event_date = request.POST.get('date')
        description = request.POST.get('description')
        outfit_id = request.POST.get('outfit')

        count = Event.objects.filter(user=request.user, date=event_date).count()
        if count < 3:
            Event.objects.create(
                user=request.user,
                date=event_date,
                description=description,
                outfit_id=outfit_id
            )
    return redirect(f'/calendar/?date={request.POST.get("date")}')


@login_required
def get_weather_api(request):
    city = request.GET.get('city', 'Москва')
    date = request.GET.get('date')
    weather = get_weather_info(city, date)

    if weather:
        return JsonResponse({'success': True, **weather})
    return JsonResponse({'success': False, 'error': 'Не удалось загрузить погоду'})


@login_required
def get_city_by_coords(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')

    if not lat or not lon:
        return JsonResponse({'success': False, 'error': 'Нет координат'})

    try:
        api_key = "6efa76f7899e516bc82c9f6b3267bc3a"
        url = f"http://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={api_key}"
        response = requests.get(url, timeout=5).json()

        if response and len(response) > 0:
            city = response[0].get('name')
            if city:
                request.session['current_city'] = city
                return JsonResponse({'success': True, 'city': city})
        return JsonResponse({'success': False, 'error': 'Город не найден'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})