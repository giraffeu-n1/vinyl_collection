from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

from .permissions import is_collection_admin


def admin_required(view_func):
    """Только администратор коллекции (is_staff)."""

    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_collection_admin(request.user):
            messages.error(request, 'Недостаточно прав. Доступ только для просмотра.')
            return redirect('album_list')
        return view_func(request, *args, **kwargs)

    return wrapper
