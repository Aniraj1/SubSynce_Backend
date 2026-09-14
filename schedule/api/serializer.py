from rest_framework import serializers

from schedule.model.cleaningschedule import ServiceSchedule, ScheduleAssignment, ServiceOccurrence


class ServiceScheduleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "site",
            "notes",
            "start_date",
            "end_date",
            "frequency",
            "status",
            "created_by",
        ]

class DetailScheduleSerializer(serializers.ModelSerializer):
    site = serializers.CharField(source="site.name", read_only=True)
    created_by = serializers.CharField(source="created_by.username", read_only=True)
    class Meta:
        model = ServiceSchedule
        fields = [
            "id",
            "site",
            "notes",
            "start_date",
            "end_date",
            "frequency",
            "status",
            "created_by",
        ]