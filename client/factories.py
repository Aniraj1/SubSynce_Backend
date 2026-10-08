import factory
from django.contrib.auth.hashers import make_password
from faker import Faker
from authuser.factories import UserFactory
from client.model.clientmanage import Client, Site

fake = Faker()


class ClientFactory(factory.Factory):
    class Meta:
        model = Client

    first_name = fake.unique.first_name()
    last_name = fake.unique.last_name()
    phone = fake.phone_number()
    email = fake.unique.email()

class SiteFactory(factory.Factory):
    class Meta:
        model = Site

    name = fake.unique.company()
    address = fake.address()
    cleaning_frequency = fake.random_element(elements=("Daily", "Weekly", "Monthly"))
    price = fake.pydecimal(left_digits=3, right_digits=2, positive=True)
    client_id = factory.SubFactory(ClientFactory)
    cleaning_instructions = fake.text(max_nb_chars=200)
    assigned_contractor = factory.SubFactory(UserFactory)
