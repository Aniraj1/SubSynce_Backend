import factory
from faker import Faker
from authuser.factories import UserFactory
from schedule.factories import ServiceScheduleFactory
from work.model.workcomplete import CompleteWork

fake = Faker()

class CompleteWorkFactory(factory.Factory):
    class Meta:
        model = CompleteWork

    schedule= factory.SubFactory(ServiceScheduleFactory)
    status= fake.random_element(elements=("IN_PROGRESS", "COMPLETED", "MISSED"))
    check_in_time= fake.date_time_this_year()
    check_out_time= fake.date_time_this_year()
    completion_notes= fake.text(max_nb_chars=200)
    completed_by= factory.SubFactory(UserFactory)
    location= fake.address()

