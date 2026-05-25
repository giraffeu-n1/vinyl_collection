from django.conf import settings
from django.db import models


class Album(models.Model):
    """Виниловый альбом в коллекции."""

    artist = models.CharField('Группа / исполнитель', max_length=200)
    title = models.CharField('Название альбома', max_length=200)
    description = models.TextField('Описание', blank=True)
    cover = models.ImageField('Обложка', upload_to='covers/%Y/%m/', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='albums',
        verbose_name='Владелец',
    )
    created_at = models.DateTimeField('Добавлен', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'альбом'
        verbose_name_plural = 'альбомы'
        indexes = [
            models.Index(fields=['artist']),
            models.Index(fields=['title']),
        ]

    def __str__(self):
        return f'{self.artist} — {self.title}'

    @property
    def primary_image(self):
        photo = self.photos.filter(is_primary=True).first()
        if photo:
            return photo.image
        photo = self.photos.order_by('order', 'pk').first()
        if photo:
            return photo.image
        return self.cover if self.cover else None


class AlbumPhoto(models.Model):
    """Фотография альбома (обложка, задник, этикетка и т.д.)."""

    album = models.ForeignKey(
        Album,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name='Альбом',
    )
    image = models.ImageField('Фото', upload_to='albums/%Y/%m/')
    is_primary = models.BooleanField('Главное фото', default=False)
    order = models.PositiveIntegerField('Порядок', default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order', 'pk']
        verbose_name = 'фото альбома'
        verbose_name_plural = 'фото альбомов'

    def __str__(self):
        return f'Фото #{self.pk} — {self.album}'


class WishlistItem(models.Model):
    """Запись в списке желаемых пластинок."""

    artist = models.CharField('Группа', max_length=200)
    title = models.CharField('Альбом', max_length=200)
    photo = models.ImageField('Фото', upload_to='wishlist/%Y/%m/', blank=True)
    note = models.TextField('Примечание', blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlist_items',
        verbose_name='Владелец',
    )
    created_at = models.DateTimeField('Добавлено', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        ordering = ['artist', 'title']
        verbose_name = 'запись wishlist'
        verbose_name_plural = 'wishlist'

    def __str__(self):
        return f'{self.artist} — {self.title}'
