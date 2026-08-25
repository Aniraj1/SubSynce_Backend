import re

from rest_framework_simplejwt.tokens import RefreshToken


REGEX_PATTERN = "^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{8,}$"


def check_password_strength(password: str) -> bool:
    return bool(re.match(REGEX_PATTERN, password))


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }