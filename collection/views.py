import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import DatabaseError, IntegrityError
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from .decorators import admin_required
from .forms import (
    AlbumCreateForm,
    AlbumEditForm,
    RegisterForm,
    SearchForm,
    VinylAuthenticationForm,
    WishlistForm,
)
from .models import Album, AlbumPhoto, WishlistItem
logger = logging.getLogger(__name__)

from .services import (
    ROTATE_ANGLES,
    add_album_photos,
    delete_album_photo,
    move_album_photo,
    rotate_album_photo,
    set_primary_photo,
    sync_album_cover,
)


def artist_list(request):
    artists = (
        Album.objects.values('artist')
        .annotate(album_count=Count('id'))
        .order_by('artist')
    )
    return render(request, 'collection/artist_list.html', {'artists': artists})


def artist_detail(request, artist):
    albums = (
        Album.objects.filter(artist=artist)
        .select_related('owner')
        .prefetch_related('photos')
        .annotate(photo_count=Count('photos'))
    )
    if not albums.exists():
        from django.http import Http404
        raise Http404('Группа не найдена')
    return render(request, 'collection/artist_detail.html', {
        'artist': artist,
        'albums': albums,
    })


def album_list(request):
    form = SearchForm(request.GET or None)
    total_album_count = Album.objects.count()
    search_query = ''
    albums = (
        Album.objects.select_related('owner')
        .prefetch_related('photos')
        .annotate(photo_count=Count('photos'))
        .order_by('artist', 'title')
    )

    if form.is_valid():
        query = form.cleaned_data.get('q', '').strip()
        if query:
            search_query = query
            albums = albums.filter(
                Q(artist__icontains=query) | Q(title__icontains=query)
            )

    return render(request, 'collection/album_list.html', {
        'albums': albums,
        'search_form': form,
        'total_album_count': total_album_count,
        'search_query': search_query,
    })


def album_detail(request, pk):
    album = get_object_or_404(
        Album.objects.select_related('owner').prefetch_related('photos'),
        pk=pk,
    )
    return render(request, 'collection/album_detail.html', {'album': album})


@admin_required
def album_create(request):
    if request.method == 'POST':
        form = AlbumCreateForm(request.POST, request.FILES)
        if form.is_valid():
            album = form.save(commit=False)
            album.owner = request.user
            album.save()
            count = add_album_photos(
                album, request.FILES.getlist('new_photos'), set_first_primary=True,
            )
            if count and not album.cover:
                sync_album_cover(album)
            messages.success(request, f'Альбом «{album.title}» добавлен в коллекцию.')
            return redirect('album_detail', pk=album.pk)
    else:
        form = AlbumCreateForm()
    return render(request, 'collection/album_form.html', {
        'form': form,
        'title': 'Добавить альбом',
        'is_create': True,
    })


@admin_required
def album_edit(request, pk):
    album = get_object_or_404(
        Album.objects.prefetch_related('photos'),
        pk=pk,
    )
    if request.method == 'POST':
        form = AlbumEditForm(request.POST, request.FILES, instance=album)
        if form.is_valid():
            form.save()
            added = add_album_photos(album, request.FILES.getlist('new_photos'))
            if added:
                messages.success(request, f'Добавлено фотографий: {added}.')
            messages.success(request, 'Альбом обновлён.')
            return redirect('album_detail', pk=album.pk)
    else:
        form = AlbumEditForm(instance=album)
    other_albums = (
        Album.objects.exclude(pk=album.pk)
        .order_by('artist', 'title')
    )
    return render(request, 'collection/album_edit.html', {
        'form': form,
        'album': album,
        'photos': album.photos.all(),
        'rotate_angles': sorted(ROTATE_ANGLES),
        'other_albums': other_albums,
    })


@admin_required
@require_POST
def photo_delete(request, pk, photo_pk):
    album = get_object_or_404(Album, pk=pk)
    photo = get_object_or_404(AlbumPhoto, pk=photo_pk, album=album)
    delete_album_photo(photo)
    messages.success(request, 'Фотография удалена.')
    next_url = request.POST.get('next', '')
    if next_url == 'edit':
        return redirect('album_edit', pk=album.pk)
    return redirect('album_detail', pk=album.pk)


@admin_required
@require_POST
def photo_set_primary(request, pk, photo_pk):
    album = get_object_or_404(Album, pk=pk)
    photo = get_object_or_404(AlbumPhoto, pk=photo_pk, album=album)
    set_primary_photo(album, photo)
    messages.success(request, 'Главное фото обновлено.')
    next_url = request.POST.get('next', '')
    if next_url == 'edit':
        return redirect('album_edit', pk=album.pk)
    return redirect('album_detail', pk=album.pk)


@admin_required
@require_POST
def photo_move(request, pk, photo_pk):
    source_album = get_object_or_404(Album, pk=pk)
    photo = get_object_or_404(AlbumPhoto, pk=photo_pk, album=source_album)

    new_artist = request.POST.get('new_artist', '').strip()
    new_title = request.POST.get('new_title', '').strip()
    created_new = False

    if new_artist and new_title:
        target_album = Album.objects.create(
            artist=new_artist,
            title=new_title,
            owner=request.user,
        )
        created_new = True
    else:
        try:
            target_id = int(request.POST.get('target_album', 0))
        except (TypeError, ValueError):
            target_id = 0

        target_album = Album.objects.filter(pk=target_id).first()
        if not target_album:
            if new_artist or new_title:
                messages.error(request, 'Для нового альбома укажите и исполнителя, и название.')
            else:
                messages.error(request, 'Выберите альбом или заполните поля нового альбома.')
            return redirect('album_edit', pk=source_album.pk)

    if target_album.pk == source_album.pk:
        messages.error(request, 'Нельзя перенести фото в тот же альбом.')
        return redirect('album_edit', pk=source_album.pk)

    move_album_photo(photo, target_album)
    if created_new:
        messages.success(
            request,
            f'Создан альбом «{target_album.artist} — {target_album.title}», фото перенесено.',
        )
    else:
        messages.success(
            request,
            f'Фото перенесено в «{target_album.artist} — {target_album.title}».',
        )
    next_url = request.POST.get('next', '')
    if next_url == 'target_edit':
        return redirect('album_edit', pk=target_album.pk)
    return redirect('album_edit', pk=source_album.pk)


@admin_required
@require_POST
def photo_rotate(request, pk, photo_pk):
    album = get_object_or_404(Album, pk=pk)
    photo = get_object_or_404(AlbumPhoto, pk=photo_pk, album=album)
    try:
        degrees = int(request.POST.get('degrees', 0))
    except (TypeError, ValueError):
        degrees = 0
    if degrees not in ROTATE_ANGLES:
        messages.error(request, 'Выберите поворот: 90°, 180° или 270°.')
        return redirect('album_edit', pk=album.pk)
    rotate_album_photo(photo, degrees)
    messages.success(request, f'Фото повёрнуто на {degrees}°.')
    return redirect('album_edit', pk=album.pk)


@admin_required
def album_delete(request, pk):
    album = get_object_or_404(
        Album.objects.prefetch_related('photos'),
        pk=pk,
    )
    if request.method == 'POST':
        title = album.title
        album.delete()
        messages.success(request, f'Альбом «{title}» удалён из коллекции.')
        return redirect('album_list')
    return render(request, 'collection/album_confirm_delete.html', {'album': album})


class VinylLoginView(LoginView):
    template_name = 'collection/login.html'
    authentication_form = VinylAuthenticationForm
    redirect_authenticated_user = True


class VinylLogoutView(LogoutView):
    next_page = reverse_lazy('login')


def wishlist_list(request):
    items = WishlistItem.objects.select_related('owner').order_by('artist', 'title')
    return render(request, 'collection/wishlist_list.html', {'items': items})


@admin_required
def wishlist_create(request):
    if request.method == 'POST':
        form = WishlistForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user
            item.save()
            messages.success(request, f'«{item.title}» добавлен в Wishlist.')
            return redirect('wishlist_list')
    else:
        form = WishlistForm()
    return render(request, 'collection/wishlist_form.html', {
        'form': form,
        'title': 'Добавить в Wishlist',
    })


@admin_required
def wishlist_edit(request, pk):
    item = get_object_or_404(WishlistItem, pk=pk)
    if request.method == 'POST':
        form = WishlistForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Запись обновлена.')
            return redirect('wishlist_list')
    else:
        form = WishlistForm(instance=item)
    return render(request, 'collection/wishlist_form.html', {
        'form': form,
        'item': item,
        'title': 'Редактировать запись',
    })


@admin_required
def wishlist_delete(request, pk):
    item = get_object_or_404(WishlistItem, pk=pk)
    if request.method == 'POST':
        title = item.title
        item.delete()
        messages.success(request, f'«{title}» удалён из Wishlist.')
        return redirect('wishlist_list')
    return render(request, 'collection/wishlist_confirm_delete.html', {'item': item})


def register(request):
    if request.user.is_authenticated:
        return redirect('album_list')
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                form.save()
            except IntegrityError:
                form.add_error('username', 'Это имя пользователя уже занято.')
            except DatabaseError:
                logger.exception('Registration database error')
                messages.error(
                    request,
                    'Ошибка базы данных. Сообщите администратору или попробуйте позже.',
                )
            else:
                messages.success(
                    request,
                    'Регистрация принята. Дождитесь активации аккаунта администратором, '
                    'затем войдите на сайт.',
                )
                return redirect('login')
    else:
        form = RegisterForm()
    return render(request, 'collection/register.html', {'form': form})


@admin_required
def admin_users(request):
    if request.method == 'POST':
        try:
            user_id = int(request.POST.get('user_id', 0))
        except (TypeError, ValueError):
            user_id = 0
        user = User.objects.filter(pk=user_id, is_active=False, is_staff=False).first()
        if user:
            user.is_active = True
            user.save(update_fields=['is_active'])
            messages.success(request, f'Пользователь «{user.username}» активирован.')
        else:
            messages.error(request, 'Пользователь не найден или уже активен.')
        return redirect('admin_users')

    pending_users = User.objects.filter(
        is_active=False,
        is_staff=False,
    ).order_by('date_joined')
    recent_active = User.objects.filter(
        is_active=True,
        is_staff=False,
    ).order_by('-last_login', '-date_joined')[:10]
    return render(request, 'collection/admin_users.html', {
        'pending_users': pending_users,
        'recent_active': recent_active,
    })
