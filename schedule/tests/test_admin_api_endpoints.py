import pytest
from decouple import config
from django.urls import reverse

from authuser import utils


# ------------------- Add ServiceSchedule Tests ------------------ #
def test_add_service_schedule(api_client, test_site, test_admin_user, login_test_admin_user):
    url = reverse('ServiceScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "site": test_site.id,
        "scheduled_date": "2023-08-15",
        "scheduled_time": "10:00:00",
        "status": "SCHEDULED",
        "notes": "Test notes for the service schedule.",
        "created_by": test_admin_user.id
    }
    response = api_client.post(url, data)
    assert response.status_code == 201

def test_add_service_schedule_unauthorized(api_client, test_site, test_admin_user):
    url = reverse('ServiceScheduleView')
    data = {
        "site": test_site.id,
        "scheduled_date": "2023-08-15",
        "scheduled_time": "10:00:00",
        "status": "SCHEDULED",
        "notes": "Test notes for the service schedule.",
        "created_by": test_admin_user.id
    }
    response = api_client.post(url, data)
    assert response.status_code == 401

def test_add_service_schedule_with_invalid_site_id(api_client, test_admin_user, login_test_admin_user):
    url = reverse('ServiceScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "site": "b1edf6d5-4d85-4035-9fc2-4e0161971bfa",
        "scheduled_date": "2023-08-15",
        "scheduled_time": "10:00:00",
        "status": "SCHEDULED",
        "notes": "Test notes for the service schedule.",
        "created_by": test_admin_user.id
    }
    response = api_client.post(url, data)
    assert response.status_code == 404


# ------------------- ServiceSchedule List Tests ------------------ #
def test_get_service_schedule_list(api_client, test_service_schedule ,login_test_admin_user):
    url = reverse('ServiceScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_service_schedule_list_unauthorized(api_client, test_service_schedule):
    url = reverse('ServiceScheduleView')
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_service_schedule_list_with_contractor(api_client, test_service_schedule, login_test_contractor_user):
    url = reverse('ServiceScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 403


# ------------------- ServiceSchedule With ID Tests ------------------ #
def test_get_service_schedule_with_id(api_client, test_service_schedule ,login_test_admin_user):
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_service_schedule_with_id_unauthorized(api_client, test_service_schedule):
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_service_schedule_with_invalid_id(api_client, test_service_schedule, login_test_admin_user):
    url = reverse('ServiceScheduleDetailView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 404


# ------------------- ServiceSchedule Update Tests ------------------ #
def test_update_service_schedule(api_client, test_site, test_service_schedule ,login_test_admin_user):
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    test_service_schedule.status = "SCHEDULED"
    test_service_schedule.save(update_fields=["status"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "site": test_site.id,
        "scheduled_date": "2023-08-20",
        "scheduled_time": "14:00:00",
        "status": "COMPLETED",
        "notes": "Updated notes for the service schedule."
    }
    response = api_client.put(url, data)
    assert response.status_code == 200


def test_update_service_schedule_unauthorized(api_client, test_site, test_service_schedule):
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    data = {
        "site": test_site.id,
        "scheduled_date": "2023-08-20",
        "scheduled_time": "14:00:00",
        "status": "COMPLETED",
        "notes": "Updated notes for the service schedule."
    }
    response = api_client.put(url, data)
    assert response.status_code == 401

def test_update_service_schedule_with_invalid_id(api_client, test_site, test_service_schedule, login_test_admin_user):
    url = reverse('ServiceScheduleDetailView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "site": test_site.id,
        "scheduled_date": "2023-08-20",
        "scheduled_time": "14:00:00",
        "status": "COMPLETED",
        "notes": "Updated notes for the service schedule."
    }
    response = api_client.put(url, data)
    assert response.status_code == 404


# ------------------- ServiceSchedule Delete Tests ------------------ #
def test_delete_service_schedule(api_client, test_service_schedule ,login_test_admin_user):
    test_service_schedule.status = "SCHEDULED"
    test_service_schedule.save(update_fields=["status"])
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 200

def test_delete_service_schedule_unauthorized(api_client, test_service_schedule):
    url = reverse('ServiceScheduleDetailView', args=[test_service_schedule.id])
    response = api_client.delete(url)
    assert response.status_code == 401

def test_delete_service_schedule_with_invalid_id(api_client, test_service_schedule, login_test_admin_user):
    url = reverse('ServiceScheduleDetailView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.delete(url)
    assert response.status_code == 404


# ------------------- ServiceSchedule Partial Update Tests ------------------ #
def test_partial_update_service_schedule(api_client, test_site, test_service_schedule ,login_test_admin_user):
    url = reverse('ChangeStatusView', args=[test_service_schedule.id])
    test_service_schedule.status = "SCHEDULED"
    test_service_schedule.save(update_fields=["status"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "status": "COMPLETED",
    }
    response = api_client.patch(url, data)
    assert response.status_code == 200

def test_partial_update_service_schedule_unauthorized(api_client, test_site, test_service_schedule):
    url = reverse('ChangeStatusView', args=[test_service_schedule.id])
    data = {
        "status": "COMPLETED",
    }
    response = api_client.patch(url, data)
    assert response.status_code == 401

def test_partial_update_service_schedule_with_invalid_id(api_client, test_site, test_service_schedule, login_test_admin_user):
    url = reverse('ChangeStatusView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    data = {
        "status": "COMPLETED",
    }
    response = api_client.patch(url, data)
    assert response.status_code == 404


