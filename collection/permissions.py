def is_collection_admin(user) -> bool:
    return user.is_authenticated and user.is_staff
