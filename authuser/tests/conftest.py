import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient


from authuser.utils import get_tokens_for_user

from authuser.factories import UserDetailFactory, UserFactory
from authuser.model.user import User, UserDetail

register(UserFactory)
register(UserDetailFactory)

@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def test_user(db, user_factory):
    user_from_factory = user_factory.build()
    user = User.objects.create(
        username=user_from_factory.username,
        password=user_from_factory.password,
        email=user_from_factory.email,
        is_superuser=True,
        role="OWNER",
        )
    return user

@pytest.fixture()
def test_contractor_user(db, user_factory):
    user_from_factory = user_factory.build()
    user = User.objects.create(
        username="contractor_user",
        password=user_from_factory.password,
        email="contractor_user@example.com",
        role="CONTRACTOR",
        )
    return user

@pytest.fixture()
def test_admin_user(db, user_factory):
    user_from_factory = user_factory.build()
    user = User.objects.create(
        username=user_from_factory.username,
        password=user_from_factory.password,
        email=user_from_factory.email,
        role="ADMINISTRATOR",
        )
    return user

@pytest.fixture()
def login_test_user(db, test_user):
    return get_tokens_for_user(test_user)

@pytest.fixture()
def login_test_admin_user(db, test_admin_user):
    return get_tokens_for_user(test_admin_user)


@pytest.fixture()
def test_user_detail(db, test_user, user_detail_factory):
    user_detail_from_factory = user_detail_factory.build()
    user_detail = UserDetail.objects.create(
        user=test_user,  # Use the test_user instance
        first_name=user_detail_from_factory.first_name,
        last_name=user_detail_from_factory.last_name,
        phone=user_detail_from_factory.phone,
    )
    return user_detail