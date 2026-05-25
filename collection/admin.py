from django.contrib import admin

from .models import Album, AlbumPhoto, WishlistItem


class AlbumPhotoInline(admin.TabularInline):
    model = AlbumPhoto
    extra = 0


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'owner', 'created_at')
    list_filter = ('artist', 'created_at')
    search_fields = ('artist', 'title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [AlbumPhotoInline]


@admin.register(AlbumPhoto)
class AlbumPhotoAdmin(admin.ModelAdmin):
    list_display = ('album', 'is_primary', 'order', 'created_at')
    list_filter = ('is_primary',)


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('artist', 'title', 'owner', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('artist', 'title', 'note')
