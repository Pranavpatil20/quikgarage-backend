from django.contrib.auth import get_user_model


def create_or_update_superuser(*, phone: str, password: str, name: str = 'Admin') -> tuple[object, bool]:
    """Create or update a Django superuser. Returns (user, created)."""
    User = get_user_model()
    phone = phone.strip()
    name = (name or 'Admin').strip() or 'Admin'
    if not phone:
        raise ValueError('Phone is required.')
    if not password:
        raise ValueError('Password is required.')

    user, created = User.objects.get_or_create(
        phone=phone,
        defaults={'name': name, 'role': 'owner'},
    )
    user.name = name
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    return user, created
