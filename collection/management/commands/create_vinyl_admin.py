from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

ADMIN_USERNAME = 'vinyladmin'
ADMIN_PASSWORD = 'VinylCol2026!'


class Command(BaseCommand):
    help = 'Создать или обновить учётную запись администратора коллекции'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username=ADMIN_USERNAME,
            defaults={'email': '', 'is_active': True},
        )
        user.set_password(ADMIN_PASSWORD)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()

        verb = 'Создан' if created else 'Обновлён'
        self.stdout.write(self.style.SUCCESS(f'{verb} администратор: {ADMIN_USERNAME}'))
        self.stdout.write(f'Пароль: {ADMIN_PASSWORD}')
