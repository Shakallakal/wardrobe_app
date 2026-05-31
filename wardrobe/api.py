import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from .models import Item, Outfit, Event


# ========== АВТОРИЗАЦИЯ И РЕГИСТРАЦИЯ ==========

@csrf_exempt
@require_http_methods(["POST"])
def api_register(request):
    """Регистрация нового пользователя"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        first_name = data.get('first_name')
        password = data.get('password')

        # Проверка обязательных полей
        if not email or not first_name or not password:
            return JsonResponse({
                'success': False,
                'error': 'Заполните все поля'
            }, status=400)

        # Проверка существования пользователя
        if User.objects.filter(email=email).exists():
            return JsonResponse({
                'success': False,
                'error': 'Пользователь с такой почтой уже существует'
            }, status=400)

        # Создание пользователя
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            password=password
        )

        return JsonResponse({
            'success': True,
            'user_id': user.id,
            'first_name': user.first_name
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_login(request):
    """Авторизация пользователя"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return JsonResponse({
                'success': False,
                'error': 'Введите email и пароль'
            }, status=400)

        user = authenticate(username=email, password=password)

        if user is not None:
            login(request, user)
            return JsonResponse({
                'success': True,
                'user_id': user.id,
                'first_name': user.first_name,
                'email': user.email
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'Неверный email или пароль'
            }, status=401)

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def api_logout(request):
    """Выход из системы"""
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Не авторизован'}, status=401)


# ========== РАБОТА С ПРЕДМЕТАМИ ОДЕЖДЫ ==========

@csrf_exempt
def api_items(request):
    """Получение списка вещей и добавление новой вещи"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    # GET - получение списка вещей
    if request.method == 'GET':
        items = Item.objects.filter(user=request.user).values(
            'id', 'name', 'category', 'season', 'color', 'brand', 'sku', 'image', 'created_at'
        )
        # Преобразуем image в полный URL
        items_list = list(items)
        for item in items_list:
            if item['image']:
                item['image_url'] = f"/media/{item['image']}"
            else:
                item['image_url'] = None
        return JsonResponse(items_list, safe=False)

    # POST - добавление новой вещи
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)

            # Проверка обязательных полей
            if not data.get('name'):
                return JsonResponse({'success': False, 'error': 'Название обязательно'}, status=400)

            item = Item.objects.create(
                user=request.user,
                name=data['name'],
                category=data.get('category', 'top'),
                season=data.get('season', 'all'),
                color=data.get('color', ''),
                brand=data.get('brand', ''),
                sku=data.get('sku', '')
            )

            return JsonResponse({
                'success': True,
                'id': item.id,
                'message': 'Вещь добавлена'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_item_detail(request, item_id):
    """Получение, редактирование, удаление конкретной вещи"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    item = get_object_or_404(Item, id=item_id, user=request.user)

    # GET - получение одной вещи
    if request.method == 'GET':
        data = {
            'id': item.id,
            'name': item.name,
            'category': item.category,
            'season': item.season,
            'color': item.color,
            'brand': item.brand,
            'sku': item.sku,
            'image_url': f"/media/{item.image}" if item.image else None,
            'created_at': item.created_at
        }
        return JsonResponse(data)

    # PUT - редактирование вещи
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            item.name = data.get('name', item.name)
            item.category = data.get('category', item.category)
            item.season = data.get('season', item.season)
            item.color = data.get('color', item.color)
            item.brand = data.get('brand', item.brand)
            item.sku = data.get('sku', item.sku)
            item.save()
            return JsonResponse({'success': True, 'message': 'Вещь обновлена'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # DELETE - удаление вещи
    elif request.method == 'DELETE':
        item.delete()
        return JsonResponse({'success': True, 'message': 'Вещь удалена'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ========== РАБОТА С КОМПЛЕКТАМИ ==========

@csrf_exempt
def api_outfits(request):
    """Получение списка комплектов и создание нового"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    # GET - получение списка комплектов
    if request.method == 'GET':
        outfits = Outfit.objects.filter(user=request.user).values('id', 'name', 'image')
        # Для каждого комплекта получаем ID предметов
        outfits_list = list(outfits)
        for outfit_data in outfits_list:
            outfit = Outfit.objects.get(id=outfit_data['id'])
            outfit_data['items_ids'] = list(outfit.items.values_list('id', flat=True))
            if outfit_data['image']:
                outfit_data['image_url'] = f"/media/{outfit_data['image']}"
            else:
                outfit_data['image_url'] = None
        return JsonResponse(outfits_list, safe=False)

    # POST - создание нового комплекта
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            items_ids = data.get('items_ids', [])

            if not name:
                return JsonResponse({'success': False, 'error': 'Название комплекта обязательно'}, status=400)

            if len(items_ids) < 2:
                return JsonResponse({'success': False, 'error': 'Комплект должен состоять минимум из двух вещей'},
                                    status=400)

            # Создаём комплект
            outfit = Outfit.objects.create(
                user=request.user,
                name=name
            )

            # Добавляем предметы
            items = Item.objects.filter(id__in=items_ids, user=request.user)
            outfit.items.set(items)

            return JsonResponse({
                'success': True,
                'id': outfit.id,
                'message': 'Комплект создан'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_outfit_detail(request, outfit_id):
    """Получение, редактирование, удаление конкретного комплекта"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    outfit = get_object_or_404(Outfit, id=outfit_id, user=request.user)

    # GET - получение одного комплекта
    if request.method == 'GET':
        data = {
            'id': outfit.id,
            'name': outfit.name,
            'items_ids': list(outfit.items.values_list('id', flat=True)),
            'image_url': f"/media/{outfit.image}" if outfit.image else None,
        }
        return JsonResponse(data)

    # PUT - редактирование комплекта
    elif request.method == 'PUT':
        try:
            data = json.loads(request.body)
            outfit.name = data.get('name', outfit.name)

            items_ids = data.get('items_ids', [])
            if len(items_ids) >= 2:
                items = Item.objects.filter(id__in=items_ids, user=request.user)
                outfit.items.set(items)

            outfit.save()
            return JsonResponse({'success': True, 'message': 'Комплект обновлён'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    # DELETE - удаление комплекта
    elif request.method == 'DELETE':
        outfit.delete()
        return JsonResponse({'success': True, 'message': 'Комплект удалён'})

    return JsonResponse({'error': 'Method not allowed'}, status=405)


# ========== РАБОТА С СОБЫТИЯМИ КАЛЕНДАРЯ ==========

@csrf_exempt
def api_events(request):
    """Получение событий и создание нового"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    # GET - получение событий (можно фильтровать по дате)
    if request.method == 'GET':
        date = request.GET.get('date')
        if date:
            events = Event.objects.filter(user=request.user, date=date).values('id', 'date', 'description', 'outfit_id')
        else:
            events = Event.objects.filter(user=request.user).values('id', 'date', 'description', 'outfit_id')

        events_list = list(events)
        for event in events_list:
            if event['outfit_id']:
                outfit = Outfit.objects.filter(id=event['outfit_id']).first()
                event['outfit_name'] = outfit.name if outfit else None

        return JsonResponse(events_list, safe=False)

    # POST - создание события
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            date = data.get('date')
            description = data.get('description')
            outfit_id = data.get('outfit_id')

            if not date:
                return JsonResponse({'success': False, 'error': 'Дата обязательна'}, status=400)

            # Проверка лимита (не более 3 событий в день)
            events_count = Event.objects.filter(user=request.user, date=date).count()
            if events_count >= 3:
                return JsonResponse({'success': False, 'error': 'Не более 3 событий в день'}, status=400)

            event = Event.objects.create(
                user=request.user,
                date=date,
                description=description,
                outfit_id=outfit_id if outfit_id else None
            )

            return JsonResponse({
                'success': True,
                'id': event.id,
                'message': 'Событие создано'
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)


@csrf_exempt
def api_event_delete(request, event_id):
    """Удаление события"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    event = get_object_or_404(Event, id=event_id, user=request.user)
    event.delete()
    return JsonResponse({'success': True, 'message': 'Событие удалено'})


# ========== ИНФОРМАЦИЯ О ПОЛЬЗОВАТЕЛЕ ==========

def api_user_info(request):
    """Получение информации о текущем пользователе"""

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Не авторизован'}, status=401)

    return JsonResponse({
        'id': request.user.id,
        'first_name': request.user.first_name,
        'email': request.user.email
    })