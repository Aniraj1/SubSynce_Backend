import pytest
from pytest_factoryboy import register
from rest_framework.test import APIClient
from authuser.utils import get_tokens_for_user

from authuser.factories import UserDetailFactory, UserFactory
from client.factories import ClientFactory, SiteFactory
from schedule.factories import ServiceScheduleFactory
from work.factories import CompleteWorkFactory
from authuser.model.user import User
from client.model.clientmanage import Client, Site
from work.model.workcomplete import CompleteWork
from schedule.model.cleaningschedule import ServiceSchedule


register(UserFactory)
register(UserDetailFactory)
register(ClientFactory)
register(SiteFactory)
register(ServiceScheduleFactory)
register(CompleteWorkFactory)

@pytest.fixture()
def api_client():
    return APIClient()


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
def login_test_contractor_user(db, test_contractor_user):
    return get_tokens_for_user(test_contractor_user)

@pytest.fixture()
def login_test_admin_user(db, test_admin_user):
    return get_tokens_for_user(test_admin_user)



@pytest.fixture()
def test_client(db, client_factory):
    client_from_factory = client_factory.build()
    client = Client.objects.create(
        first_name=client_from_factory.first_name,
        last_name=client_from_factory.last_name,
        phone=client_from_factory.phone,
        email=client_from_factory.email,
    )
    return client

@pytest.fixture()
def test_site(db, test_client, test_contractor_user, site_factory):
    site_from_factory = site_factory.build()
    site = Site.objects.create(
        name=site_from_factory.name,
        address=site_from_factory.address,
        cleaning_frequency=site_from_factory.cleaning_frequency,
        price=site_from_factory.price,
        client_id=test_client,
        cleaning_instructions=site_from_factory.cleaning_instructions,
        assigned_contractor=test_contractor_user,
    )
    return site

@pytest.fixture()
def test_service_schedule(db, test_site, test_contractor_user, service_schedule_factory):
    service_schedule_from_factory = service_schedule_factory.build()
    service_schedule = ServiceSchedule.objects.create(
        site=test_site,
        scheduled_date=service_schedule_from_factory.scheduled_date,
        scheduled_time=service_schedule_from_factory.scheduled_time,
        status="SCHEDULED",
        notes=service_schedule_from_factory.notes,
        created_by=test_contractor_user,
    )
    return service_schedule

@pytest.fixture()
def test_complete_work(db, test_service_schedule, test_contractor_user, complete_work_factory):
    complete_work_from_factory = complete_work_factory.build()
    complete_work = CompleteWork.objects.create(
        schedule=test_service_schedule,
        status="IN_PROGRESS",
        check_in_time=complete_work_from_factory.check_in_time,
        check_out_time=None,
        completion_notes=complete_work_from_factory.completion_notes,
        completed_by=test_contractor_user,
        location=complete_work_from_factory.location
    )
    return complete_work

