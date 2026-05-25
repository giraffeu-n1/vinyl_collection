from django.http import JsonResponse
from django.urls import path

from . import views


def health_check(_request):
    return JsonResponse({'status': 'ok'})


urlpatterns = [
    path('health/', health_check, name='health'),
    path('', views.album_list, name='album_list'),
    path('groups/', views.artist_list, name='artist_list'),
    path('groups/<path:artist>/', views.artist_detail, name='artist_detail'),
    path('album/<int:pk>/', views.album_detail, name='album_detail'),
    path('album/add/', views.album_create, name='album_create'),
    path('album/<int:pk>/edit/', views.album_edit, name='album_edit'),
    path('album/<int:pk>/photos/<int:photo_pk>/delete/', views.photo_delete, name='photo_delete'),
    path('album/<int:pk>/photos/<int:photo_pk>/primary/', views.photo_set_primary, name='photo_set_primary'),
    path('album/<int:pk>/photos/<int:photo_pk>/rotate/', views.photo_rotate, name='photo_rotate'),
    path('album/<int:pk>/photos/<int:photo_pk>/move/', views.photo_move, name='photo_move'),
    path('album/<int:pk>/delete/', views.album_delete, name='album_delete'),
    path('wishlist/', views.wishlist_list, name='wishlist_list'),
    path('wishlist/add/', views.wishlist_create, name='wishlist_create'),
    path('wishlist/<int:pk>/edit/', views.wishlist_edit, name='wishlist_edit'),
    path('wishlist/<int:pk>/delete/', views.wishlist_delete, name='wishlist_delete'),
    path('login/', views.VinylLoginView.as_view(), name='login'),
    path('logout/', views.VinylLogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('admin/users/', views.admin_users, name='admin_users'),
]
