from rest_framework import serializers

from authuser.model.user import User
from client.model.clientmanage import Site
from schedule.model.cleaningschedule import ServiceSchedule


class ServiceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "site",
            "scheduled_date",
            "scheduled_time",
            "status",
            "notes",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "created_by",
            "status",
        ]


class UserSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username"]


class SiteScheduleSerializer(serializers.ModelSerializer):
    assigned_contractor = UserSummarySerializer(read_only=True)

    class Meta:
        model = Site
        fields = [
            "id",
            "name",
            "address",
            "cleaning_frequency",
            "cleaning_instructions",
            "assigned_contractor",
        ]


class DetailScheduleSerializer(serializers.ModelSerializer):
    site = SiteScheduleSerializer(read_only=True)
    created_by = UserSummarySerializer(read_only=True)

    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "site",
            "scheduled_date",
            "scheduled_time",
            "notes",
            "status",
            "created_by",
        ]

class ChangeServiceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "site",
            "scheduled_date",
            "scheduled_time",
            "status",
            "notes",
            "created_by",
        ]
        read_only_fields = [
            "id",
            "created_by",
        ]

class ChangeStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = [
            "status",
        ]