from django.urls import path
from . import views, api

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('add/', views.add_item, name='add_item'),
    path('edit/<int:item_id>/', views.edit_item, name='edit_item'),
    path('delete/<int:item_id>/', views.delete_item, name='delete_item'),
path('outfits/', views.outfit_list, name='outfit_list'),
    path('outfits/add/', views.add_outfit, name='add_outfit'),
path('outfits/edit/<int:outfit_id>/', views.edit_outfit, name='edit_outfit'),
path('outfits/delete/<int:outfit_id>/', views.delete_outfit, name='delete_outfit'),
path('calendar/', views.outfit_calendar, name='outfit_calendar'),
    path('calendar/save/', views.save_event, name='save_event'),
    path('calendar/delete/<int:event_id>/', views.delete_event, name='delete_event'),
path('calendar/weather/', views.get_weather_api, name='get_weather'),
path('calendar/geolocate/', views.get_city_by_coords, name='geolocate'),

]
