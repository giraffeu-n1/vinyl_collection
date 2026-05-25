import io

from django.core.files.base import ContentFile
from django.db.models import Max
from PIL import Image

from .models import Album, AlbumPhoto

ROTATE_ANGLES = frozenset({90, 180, 270})

def sync_album_cover(album: Album) -> None:
    """Синхронизировать поле cover с главным фото альбома."""
    photo = album.photos.filter(is_primary=True).first()
    if not photo:
        photo = album.photos.order_by('order', 'pk').first()

    if photo:
        album.photos.exclude(pk=photo.pk).update(is_primary=False)
        if not photo.is_primary:
            photo.is_primary = True
            photo.save(update_fields=['is_primary'])
        if album.cover.name != photo.image.name:
            album.cover = photo.image
            album.save(update_fields=['cover'])
    elif album.cover:
        album.cover = ''
        album.save(update_fields=['cover'])


def add_album_photos(album: Album, files, *, set_first_primary: bool = False) -> int:
    """Добавить несколько фотографий к альбому. Возвращает число добавленных."""
    max_order = album.photos.aggregate(m=Max('order'))['m'] or 0
    has_primary = album.photos.filter(is_primary=True).exists()
    created = 0

    for uploaded in files:
        if not uploaded:
            continue
        max_order += 1
        is_primary = (set_first_primary and created == 0 and not has_primary)
        AlbumPhoto.objects.create(
            album=album,
            image=uploaded,
            order=max_order,
            is_primary=is_primary,
        )
        created += 1
        if is_primary:
            has_primary = True

    if created:
        sync_album_cover(album)
    return created


def set_primary_photo(album: Album, photo: AlbumPhoto) -> None:
    album.photos.update(is_primary=False)
    photo.is_primary = True
    photo.save(update_fields=['is_primary'])
    sync_album_cover(album)


def move_album_photo(photo: AlbumPhoto, target_album: Album) -> None:
    """Перенести фото в другой альбом."""
    if photo.album_id == target_album.pk:
        return

    source_album = photo.album
    was_primary = photo.is_primary

    max_order = target_album.photos.aggregate(m=Max('order'))['m'] or 0
    has_primary = target_album.photos.filter(is_primary=True).exists()

    photo.album = target_album
    photo.order = max_order + 1
    photo.is_primary = not has_primary
    photo.save(update_fields=['album', 'order', 'is_primary'])

    sync_album_cover(target_album)
    if was_primary or not source_album.photos.exists():
        sync_album_cover(source_album)


def delete_album_photo(photo: AlbumPhoto) -> None:
    album = photo.album
    was_primary = photo.is_primary
    photo.delete()
    if was_primary:
        sync_album_cover(album)


def rotate_album_photo(photo: AlbumPhoto, degrees: int) -> None:
    """Повернуть изображение по часовой стрелке на 90, 180 или 270 градусов."""
    if degrees not in ROTATE_ANGLES:
        raise ValueError(f'Угол должен быть 90, 180 или 270, получено: {degrees}')

    transpose_map = {
        90: Image.Transpose.ROTATE_270,
        180: Image.Transpose.ROTATE_180,
        270: Image.Transpose.ROTATE_90,
    }

    with Image.open(photo.image.path) as img:
        rotated = img.transpose(transpose_map[degrees])
        if rotated.mode in ('RGBA', 'P'):
            rotated = rotated.convert('RGB')
        buf = io.BytesIO()
        rotated.save(buf, format='JPEG', quality=90, optimize=True)
        data = buf.getvalue()

    name = photo.image.name.split('/')[-1]
    photo.image.save(name, ContentFile(data), save=True)

    if photo.is_primary:
        sync_album_cover(photo.album)
