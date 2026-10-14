"""Role checks for the web frontend.

Roles come from the backend User model: OWNER, ADMINISTRATOR, CONTRACTOR.
The Owner is the superuser, so every staff screen is open to them too.
"""
from functools import wraps

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

OWNER = "OWNER"
ADMINISTRATOR = "ADMINISTRATOR"
CONTRACTOR = "CONTRACTOR"
STAFF_ROLES = (OWNER, ADMINISTRATOR)


def is_staff_user(user):
    return user.is_authenticated and user.role in STAFF_ROLES


def is_contractor(user):
    return user.is_authenticated and user.role == CONTRACTOR


def forbidden(request, message="You don't have access to this page."):
    return render(request, "ops/403.html", {"message": message}, status=403)


def role_required(*roles):
    """Allow only the given roles; anonymous users go to login, others get 403."""

    def decorator(view):
        @login_required
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.user.role not in roles:
                return forbidden(request)
            return view(request, *args, **kwargs)

        return wrapped

    return decorator


staff_required = role_required(*STAFF_ROLES)
contractor_required = role_required(CONTRACTOR)
