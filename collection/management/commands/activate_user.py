from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Активировать пользователя (вход после регистрации на Timeweb).'

    def add_arguments(self, parser):
        parser.add_argument('username', help='Имя пользователя, например vova')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        user = User.objects.filter(username__iexact=username).first()
        if not user:
            raise CommandError(f'Пользователь «{username}» не найден в базе.')

        if user.is_active:
            self.stdout.write(self.style.WARNING(f'«{user.username}» уже активен (id={user.pk}).'))
            return

        user.is_active = True
        user.save(update_fields=['is_active'])
        self.stdout.write(self.style.SUCCESS(f'Активирован: {user.username} (id={user.pk})'))
