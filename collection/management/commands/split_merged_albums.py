"""Разделить альбомы с >2 фото: пары снимков + идентификация обложек."""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count

from collection.album_splits_data import ALBUM_SPLITS
from collection.models import Album, AlbumPhoto
from collection.services import sync_album_cover
from collection.vinyl_import import extract_artist_title


def _group_photos_in_pairs(photos: list[AlbumPhoto]) -> list[list[AlbumPhoto]]:
    if len(photos) <= 2:
        return [photos]
    groups = []
    i = 0
    while i < len(photos):
        if i + 1 < len(photos):
            groups.append([photos[i], photos[i + 1]])
            i += 2
        else:
            groups.append([photos[i]])
            i += 1
    return groups


def _identify_groups(reader, album_pk: int, groups: list[list[AlbumPhoto]]):
    predefined = ALBUM_SPLITS.get(album_pk)
    result = []
    for idx, grp in enumerate(groups):
        if predefined and idx < len(predefined):
            artist, title = predefined[idx]
        else:
            artist, title = extract_artist_title(reader, grp[0].image.path)
        result.append((artist, title, grp))
    return result


def _apply_split(album: Album, identified: list[tuple[str, str, list[AlbumPhoto]]]):
    first_artist, first_title, first_grp = identified[0]
    album.artist = first_artist
    album.title = first_title
    album.save(update_fields=['artist', 'title', 'updated_at'])

    for order, photo in enumerate(first_grp):
        photo.album = album
        photo.order = order
        photo.is_primary = order == 0
        photo.save(update_fields=['album', 'order', 'is_primary'])
    sync_album_cover(album)

    created = 0
    for artist, title, grp in identified[1:]:
        new_album = Album.objects.create(
            artist=artist,
            title=title,
            owner=album.owner,
        )
        for order, photo in enumerate(grp):
            photo.album = new_album
            photo.order = order
            photo.is_primary = order == 0
            photo.save(update_fields=['album', 'order', 'is_primary'])
        sync_album_cover(new_album)
        created += 1
    return created


class Command(BaseCommand):
    help = 'Разделить альбомы с 3+ фото на отдельные записи'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--min-photos', type=int, default=3)
        parser.add_argument('--album-id', type=int, help='Только указанный альбом')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        qs = Album.objects.annotate(pc=Count('photos')).filter(pc__gte=options['min_photos'])
        if options['album_id']:
            qs = qs.filter(pk=options['album_id'])

        if not qs.exists():
            self.stdout.write('Нет альбомов для разделения.')
            return

        import easyocr
        import numpy  # noqa: F401

        self.stdout.write('Загрузка OCR…')
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)

        total_new = 0
        for album in qs.prefetch_related('photos').order_by('pk'):
            photos = list(album.photos.order_by('order', 'pk'))
            groups = _group_photos_in_pairs(photos)
            if len(groups) <= 1:
                continue

            identified = _identify_groups(reader, album.pk, groups)
            if len(identified) <= 1:
                continue

            self.stdout.write(
                f'\n[{album.pk}] {album.artist} — {album.title} ({len(photos)} фото) '
                f'-> {len(identified)} альбомов:'
            )
            for artist, title, grp in identified:
                self.stdout.write(f'  • {artist} — {title} ({len(grp)} фото)')

            if dry_run:
                continue

            with transaction.atomic():
                total_new += _apply_split(album, identified)

        if dry_run:
            self.stdout.write(self.style.NOTICE('Dry-run: изменений нет.'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Создано новых альбомов: {total_new}'))
