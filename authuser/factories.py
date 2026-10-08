import factory
from django.contrib.auth.hashers import make_password
from faker import Faker
from decouple import config
from authuser.model.user import User, UserDetail

fake = Faker()


class UserFactory(factory.Factory):
    class Meta:
        model = User

    username = f"{fake.unique.first_name()}{fake.pyint()}"
    email = fake.unique.email()
    password = make_password(config("DEFAULT_USER_PASSWORD"))


class UserDetailFactory(factory.Factory):
    class Meta:
        model = UserDetail

    user = factory.SubFactory(UserFactory)
    first_name = fake.unique.first_name()
    last_name = fake.unique.last_name()
    phone = fake.phone_number()
