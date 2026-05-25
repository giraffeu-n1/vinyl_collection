from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse


class LoginRequiredMiddleware:
    """Гостям недоступны страницы коллекции и медиафайлы."""

    OPEN_PREFIXES = (
        '/login',
        '/register',
        '/logout',
        '/static/',
        '/admin/',
        '/health/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            return self.get_response(request)

        path = request.path
        if any(path.startswith(prefix) for prefix in self.OPEN_PREFIXES):
            return self.get_response(request)

        login_url = reverse('login')
        if path == login_url:
            return self.get_response(request)

        query = urlencode({'next': path})
        return redirect(f'{login_url}?{query}')
