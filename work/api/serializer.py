from rest_framework import serializers

from authuser.model.user import User
from schedule.api import serializer
from work.model.workcomplete import CompleteWork, WorkCompleteImage


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


class WorkCompleteImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkCompleteImage
        fields = [
            "id",
            "work_completion",
            "evidence_photo",
        ]


class WorkCompleteDetailSerializer(serializers.ModelSerializer):
    images = WorkCompleteImageSerializer(
        source="work_completion_images",
        many=True, 
        read_only=True
    )

    class Meta:
        model = CompleteWork
        fields = [
            "id",
            "schedule",
            "status",
            "check_in_time",
            "check_out_time",
            "completion_notes",
            "location",
            "images",
        ]

class DetailWorkSerializer(serializers.ModelSerializer):
    schedule = serializer.DetailScheduleSerializer(read_only=True)
    images = WorkCompleteImageSerializer(
            source="work_completion_images",
            many=True, 
            read_only=True
        )
    class Meta:
        model = CompleteWork
        fields = [
            "id",
            "schedule",
            "status",
            "check_in_time",
            "check_out_time",
            "completion_notes",
            "location",
            "images",
        ]