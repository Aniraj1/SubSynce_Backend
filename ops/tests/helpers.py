"""Shared test data for the ops frontend."""
import itertools
from datetime import date, time
from decimal import Decimal

from authuser.model.user import User
from client.model.clientmanage import Client, Site
from schedule.model.cleaningschedule import ServiceSchedule

PASSWORD = "pw-Test-12345"
_seq = itertools.count(1)


def make_user(role, username=None):
    username = username or f"{role.lower()}{next(_seq)}"
    return User.objects.create_user(username=username, password=PASSWORD, role=role)


def make_site(contractor=None, price="450.00", name=None):
    n = next(_seq)
    client = Client.objects.create(first_name=f"Client{n}", phone=f"0400{n:06d}", role="ADMINISTRATOR")
    return Site.objects.create(
        name=name or f"Site {n}",
        address=f"{n} King William St",
        cleaning_frequency="WEEKLY",
        price=Decimal(price),
        client_id=client,
        assigned_contractor=contractor,
    )


def make_schedule(site, created_by, day=None, at=time(16, 0), status="SCHEDULED"):
    return ServiceSchedule.objects.create(
        site=site,
        scheduled_date=day or date.today(),
        scheduled_time=at,
        status=status,
        created_by=created_by,
    )


def login(client, user):
    assert client.login(username=user.username, password=PASSWORD)
