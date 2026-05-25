"""CSRF за reverse-proxy Timeweb (HTTPS Origin при DEBUG=True и без trusted origins)."""

from urllib.parse import urlsplit

from django.middleware.csrf import CsrfViewMiddleware


class VinylCsrfViewMiddleware(CsrfViewMiddleware):
    """Принимает https Origin с тем же host, что у запроса (прокси без is_secure)."""

    def _origin_verified(self, request):
        if super()._origin_verified(request):
            return True

        request_origin = request.META.get('HTTP_ORIGIN')
        if not request_origin:
            return False

        try:
            parsed = urlsplit(request_origin)
        except ValueError:
            return False

        if parsed.scheme != 'https' or not parsed.netloc:
            return False

        hosts = []
        try:
            hosts.append(request.get_host())
        except Exception:
            pass

        forwarded = request.META.get('HTTP_X_FORWARDED_HOST', '')
        if forwarded:
            hosts.append(forwarded.split(',')[0].strip())

        for host in hosts:
            if not host:
                continue
            if parsed.netloc == host or parsed.hostname == host.split(':')[0]:
                return True

        return False
