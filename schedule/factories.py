import factory
from django.contrib.auth.hashers import make_password
from faker import Faker
from authuser.factories import UserFactory
from client.factories import SiteFactory
from schedule.model.cleaningschedule import ServiceSchedule

fake = Faker()


class ServiceScheduleFactory(factory.Factory):
    class Meta:
        model = ServiceSchedule

    site = factory.SubFactory(SiteFactory)
    scheduled_date = fake.date_between(start_date="today", end_date="+30d")
    scheduled_time = fake.time()
    status = fake.random_element(elements=("SCHEDULED", "COMPLETED", "MISSED", "CANCELLED"))
    notes = fake.text(max_nb_chars=200)
    created_by = factory.SubFactory(UserFactory)
