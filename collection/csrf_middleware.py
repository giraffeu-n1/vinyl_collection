"""Доверять Origin того же хоста, что и запрос (Timeweb *.twc1.net без ручного CSRF)."""

from urllib.parse import urlparse

from django.conf import settings


class SameHostCsrfOriginMiddleware:
    """Добавляет https://<текущий-host> в CSRF_TRUSTED_ORIGINS для POST с того же сайта."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        origin = request.META.get('HTTP_ORIGIN', '')
        if origin:
            parsed = urlparse(origin)
            req_host = request.get_host().split(':')[0]
            origin_host = parsed.hostname or ''
            if origin_host and origin_host == req_host and parsed.scheme in ('http', 'https'):
                trusted = f'{parsed.scheme}://{parsed.netloc}'
                if trusted not in settings.CSRF_TRUSTED_ORIGINS:
                    settings.CSRF_TRUSTED_ORIGINS = [
                        *settings.CSRF_TRUSTED_ORIGINS,
                        trusted,
                    ]
        return self.get_response(request)
