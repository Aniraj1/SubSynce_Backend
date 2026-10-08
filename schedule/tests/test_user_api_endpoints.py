import pytest
from decouple import config
from django.urls import reverse

from authuser import utils



# ------------------- ServiceSchedule List Tests ------------------ #
def test_get_contractor_service_schedule_list(api_client, test_service_schedule ,login_test_contractor_user):
    url = reverse('UserScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_contractor_service_schedule_list_unauthorized(api_client, test_service_schedule):
    url = reverse('UserScheduleView')
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_contractor_service_schedule_list_with_admin(api_client, test_service_schedule, login_test_admin_user):
    url = reverse('UserScheduleView')
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 403


# ------------------- ServiceSchedule With ID Tests ------------------ #
def test_get_contractor_service_schedule_with_id(api_client, test_service_schedule ,login_test_contractor_user):
    url = reverse('GetDetailScheduleView', args=[test_service_schedule.id])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_contractor_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 200

def test_get_contractor_service_schedule_with_id_unauthorized(api_client, test_service_schedule):
    url = reverse('GetDetailScheduleView', args=[test_service_schedule.id])
    response = api_client.get(url)
    assert response.status_code == 401

def test_get_contractor_service_schedule_with_invalid_id(api_client, test_service_schedule, login_test_admin_user):
    url = reverse('GetDetailScheduleView', args=["b1edf6d5-4d85-4035-9fc2-4e0161971bfa"])
    api_client.credentials(
        HTTP_AUTHORIZATION=f'Bearer {login_test_admin_user["access"]}'
        )
    response = api_client.get(url)
    assert response.status_code == 403

