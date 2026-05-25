from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.static import serve

from collection.views import admin_users

urlpatterns = [
    # До admin.site.urls — иначе catch-all Django Admin отдаёт 404 на admin/users/
    path('admin/users/', admin_users, name='admin_users'),
    path('admin/', admin.site.urls),
    path('', include('collection.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT},
        ),
    ]
