"""
CSRF на Timeweb: прокси ломает сравнение Origin/Referer.
Проверка csrfmiddlewaretoken + cookie сохраняется (основная защита).
"""

from urllib.parse import urlsplit

from django.middleware.csrf import CsrfViewMiddleware, RejectRequest


class VinylCsrfViewMiddleware(CsrfViewMiddleware):
    """Без проверки Origin/Referer за reverse-proxy; токен в форме — как в Django."""

    def _origin_verified(self, request):
        request_origin = request.META.get('HTTP_ORIGIN', '')
        if not request_origin:
            return True

        if super()._origin_verified(request):
            return True

        try:
            host = urlsplit(request_origin).hostname or ''
        except ValueError:
            return False

        if host.endswith('.twc1.net') or host == 'twc1.net':
            return True

        hosts = []
        try:
            hosts.append(request.get_host().split(':')[0])
        except Exception:
            pass
        forwarded = request.META.get('HTTP_X_FORWARDED_HOST', '')
        if forwarded:
            hosts.append(forwarded.split(',')[0].strip().split(':')[0])

        return host in hosts

    def process_view(self, request, callback, callback_args, callback_kwargs):
        if getattr(request, 'csrf_processing_done', False):
            return None

        if getattr(callback, 'csrf_exempt', False):
            return None

        if request.method in ('GET', 'HEAD', 'OPTIONS', 'TRACE'):
            return self._accept(request)

        if getattr(request, '_dont_enforce_csrf_checks', False):
            return self._accept(request)

        # Origin/Referer не проверяем — Timeweb/nginx часто отдают другой Host.
        try:
            self._check_token(request)
        except RejectRequest as exc:
            return self._reject(request, exc.reason)

        return self._accept(request)
