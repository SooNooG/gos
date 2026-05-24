from .views import get_user_role


def role_context(request):
    role = None
    if request.user.is_authenticated:
        role = get_user_role(request.user)
    return {"user_role": role}
