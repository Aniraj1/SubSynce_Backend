from datetime import timedelta
import uuid
from django.conf import settings
from django.db import models
from jsonschema import ValidationError
from authuser.model.softdeletemodel import BaseModel
from client.model.clientmanage import Site
from authuser.model.user import User

SCHEDULE_FREQUENCY = (
    ("ONCE", "ONCE"),
    ("DAILY", "DAILY"),
    ("WEEKLY", "WEEKLY"),
    ("MONTHLY", "MONTHLY")
)

SCHEDULE_STATUS = (
    ("ACTIVE", "ACTIVE"),
    ("CANCELLED", "CANCELLED"),
    ("COMPLETED", "COMPLETED"),
)

OCCURENCE_STATUS = (
    ("SCHEDULED", "SCHEDULED"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)

ASSIGNMENT_STATUS = (
    ("ASSIGNED", "ASSIGNED"),
    ("ACCEPTED", "ACCEPTED"),
    ("DECLINED", "DECLINED"),
    ("COMPLETED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


class ServiceSchedule(BaseModel):
    """
    ServiceSchedule model where all information about the service schedule is stored
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="service_schedules",
        db_column="SITE_ID",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_service_schedules",
        db_column="CREATED_BY",
    )
    frequency = models.CharField(max_length=255, choices=SCHEDULE_FREQUENCY, default="ONCE", db_column="FREQUENCY")
    status = models.CharField(max_length=255, choices=SCHEDULE_STATUS, default="ACTIVE", db_column="STATUS")
    start_date = models.DateField(db_column="START_DATE")
    end_date = models.DateField(blank=True, null=True, db_column="END_DATE")
    notes = models.TextField(blank=True, null=True, db_column="NOTES")
    
    class Meta:
        db_table = "POC_SERVICE_SCHEDULE"
        ordering = ["start_date"]

    def clean(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date": "End date cannot be earlier than start date."})
        if self.frequency != "ONCE" and not self.end_date:
            raise ValidationError({"end_date": "End date is required for recurring schedules."})

    def __str__(self):
        return f"{self.id}"


class ServiceOccurrence(BaseModel):
    """
    Stores one actual cleaning appointment.
    A recurring schedule can have multiple occurrences, each with its own date and time.
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    schedule = models.ForeignKey(
        ServiceSchedule,
        on_delete=models.CASCADE,
        related_name="occurrences",
        db_column="SCHEDULE_ID",
    )
    starts_at = models.DateTimeField(db_column="STARTS_AT")

    ends_at = models.DateTimeField(db_column="ENDS_AT")
    status = models.CharField(max_length=255, choices=OCCURENCE_STATUS, default="SCHEDULED", db_column="STATUS")
    completed_at = models.DateTimeField(blank=True, null=True, db_column="COMPLETED_AT")
    completion_notes = models.TextField(blank=True, null=True, db_column="COMPLETION_NOTES")
    
    
    class Meta:
        db_table = "POC_SERVICE_OCCURRENCE"
        ordering = ["starts_at"]
        constraints = [
            models.UniqueConstraint(fields=['schedule', 'starts_at'], name='unique_schedule_occurrence')
        ]

    def clean(self):
        if self.ends_at <= self.starts_at:
            raise ValidationError({"ends_at": "End time cannot be earlier than start time."})

    def __str__(self):
        return f"{self.id}"


class ScheduleAssignment(BaseModel):
    """
    Represents the assignment of a service occurrence to a cleaner.
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    occurrence = models.ForeignKey(
        ServiceOccurrence,
        on_delete=models.CASCADE,
        related_name="assignments",
        db_column="OCCURRENCE_ID",
    )
    contractor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assigned_occurrences",
        db_column="CONTRACTOR_ID",
    )
    status = models.CharField(max_length=255, choices=ASSIGNMENT_STATUS, default="ASSIGNED", db_column="STATUS")
    
    class Meta:
        db_table = "POC_SCHEDULE_ASSIGNMENT"
        constraints = [
            models.UniqueConstraint(fields=['occurrence', 'contractor'], name='unique_occurrence_assignment')
        ]

    def clean(self):
        if self.contractor.role != "CONTRACTOR":
            raise ValidationError({"contractor": "Only contractors can be assigned."})

        if self.occurrence.status == "CANCELLED":
            raise ValidationError(
                {"occurrence": "A contractor cannot be assigned to a cancelled occurrence."}
            )

        buffer_time = timedelta(hours=1)
    
        # Pad the NEW occurrence's times
        padded_new_start = self.occurrence.starts_at - buffer_time
        padded_new_end = self.occurrence.ends_at + buffer_time

        # Ask the database directly if any overlapping records exist
        has_conflict = ScheduleAssignment.objects.filter(
            contractor=self.contractor,
            occurrence__status__in=["SCHEDULED", "IN_PROGRESS"],
            # An overlap happens if an existing job starts BEFORE the new one ends
            # AND ends AFTER the new one starts.
            occurrence__starts_at__lt=padded_new_end,
            occurrence__ends_at__gt=padded_new_start
        ).exclude(id=self.id).exists() # .exists() is highly optimized!

        if has_conflict:
            raise ValidationError(
                {"contractor": "This contractor has another service within the required one-hour travel buffer."}
            )

    def __str__(self):
        return f"{self.id}"