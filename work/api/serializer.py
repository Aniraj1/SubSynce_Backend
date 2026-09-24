from rest_framework import serializers

from authuser.model.user import User
from work.model.workcomplete import CompleteWork, WorkCompleteImage
from schedule.model.cleaningschedule import ServiceSchedule





class ClockInSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompleteWork
        fields = [
            "id",
            "schedule",
            "check_in_time",
            "location",
        ]
        read_only_fields = [
            "id",
            "check_in_time",
        ]


class ClockOutSerializer(serializers.ModelSerializer):
    images = serializers.ImageField(write_only=True, required=False)
    class Meta:
        model = CompleteWork
        fields = [
            "id",
            "check_out_time",
            "completion_notes",
            "location",
            "images"
        ]
        read_only_fields = [
            "id",
            "check_out_time",
            "schedule",
        ]