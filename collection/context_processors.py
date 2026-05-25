from .permissions import is_collection_admin


def collection_permissions(request):
    return {
        'is_collection_admin': is_collection_admin(request.user),
    }
