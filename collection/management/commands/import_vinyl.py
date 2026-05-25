"""Импорт фотографий винила из папки на диске."""

from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from collection.models import Album, AlbumPhoto
from collection.vinyl_import import (
    extract_artist_title,
    group_photos,
    resize_image,
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Импортировать фотографии винила из папки (группировка + OCR)'

    def add_arguments(self, parser):
        parser.add_argument(
            'source_dir',
            nargs='?',
            default=r'C:\music\vinyl',
            help='Папка с JPG-фотографиями',
        )
        parser.add_argument(
            '--username',
            default='collector',
            help='Имя пользователя-владельца альбомов',
        )
        parser.add_argument(
            '--gap',
            type=int,
            default=33,
            help='Пауза в секундах между альбомами',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Удалить существующие альбомы перед импортом',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Только показать группы без загрузки',
        )

    def handle(self, *args, **options):
        source = Path(options['source_dir'])
        if not source.is_dir():
            raise CommandError(f'Папка не найдена: {source}')

        paths = sorted(source.glob('*.jpg')) + sorted(source.glob('*.jpeg'))
        paths += sorted(source.glob('*.JPG')) + sorted(source.glob('*.JPEG'))
        paths = sorted(set(paths), key=lambda p: p.name)

        if not paths:
            raise CommandError(f'В {source} нет JPG-файлов')

        groups = group_photos(paths, gap_seconds=options['gap'])
        self.stdout.write(f'Найдено {len(paths)} фото -> {len(groups)} альбомов')

        if options['dry_run']:
            for i, group in enumerate(groups, 1):
                self.stdout.write(f'  [{i}] {len(group)} фото: {group[0].name} … {group[-1].name}')
            return

        try:
            import easyocr
            import numpy  # noqa: F401 — нужен для easyocr
        except ImportError as exc:
            raise CommandError(
                'Установите easyocr: pip install easyocr numpy'
            ) from exc

        self.stdout.write('Загрузка OCR-модели (первый запуск может занять время)…')
        reader = easyocr.Reader(['en'], gpu=False, verbose=False)

        user, created = User.objects.get_or_create(
            username=options['username'],
            defaults={'email': f'{options["username"]}@vinyl.local'},
        )
        if created:
            user.set_password('vinyl123')
            user.save()
            self.stdout.write(f'Создан пользователь {user.username} (пароль: vinyl123)')

        if options['clear']:
            deleted, _ = Album.objects.all().delete()
            self.stdout.write(self.style.WARNING(f'Удалено записей: {deleted}'))

        created_albums = 0
        created_photos = 0

        for num, group in enumerate(groups, 1):
            cover_idx = 0
            artist, title = extract_artist_title(reader, group[0])
            if (
                len(group) > 1
                and (
                    artist.startswith('Неизвест')
                    or title == 'Без названия'
                    or len(artist) < 4
                )
            ):
                artist, title = extract_artist_title(reader, group[1])

            self.stdout.write(
                f'[{num}/{len(groups)}] {artist} - {title} ({len(group)} фото)',
                ending='\n',
            )
            self.stdout.flush()

            with transaction.atomic():
                album = Album.objects.create(
                    artist=artist,
                    title=title,
                    owner=user,
                )

                for order, path in enumerate(group):
                    data = resize_image(path)
                    filename = f'{album.pk}_{order}_{path.stem}.jpg'
                    is_primary = order == cover_idx

                    photo = AlbumPhoto(
                        album=album,
                        is_primary=is_primary,
                        order=order,
                    )
                    photo.image.save(filename, ContentFile(data), save=True)
                    created_photos += 1

                    if is_primary:
                        album.cover.save(filename, ContentFile(data), save=False)

                album.save(update_fields=['cover'])
            created_albums += 1

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {created_albums} альбомов, {created_photos} фотографий '
            f'(пользователь: {user.username})'
        ))
