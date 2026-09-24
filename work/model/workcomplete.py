import uuid
from django.db import models
from authuser.model.softdeletemodel import BaseModel
from authuser.model.user import User
from schedule.model.cleaningschedule import ServiceSchedule


WORK_STATUS = (
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("MISSED", "MISSED"),
)



class CompleteWork(BaseModel):
    """
    Records the work performed for one scheduled cleaning service.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="ID",
    )
    schedule = models.OneToOneField(
        ServiceSchedule,
        on_delete=models.CASCADE,
        related_name="work_completion",
        db_column="SCHEDULE_ID",
    )
    status = models.CharField(
        max_length=20,
        choices=WORK_STATUS,
        default="IN_PROGRESS",
        db_column="STATUS",
    )
    check_in_time = models.DateTimeField(
        blank=True,
        null=True,
        db_column="CHECK_IN_TIME",
    )
    check_out_time = models.DateTimeField(
        blank=True,
        null=True,
        db_column="CHECK_OUT_TIME",
    )
    completion_notes = models.TextField(
        blank=True,
        null=True,
        db_column="COMPLETION_NOTES",
    )
    completed_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="work_completions",
        db_column="COMPLETED_BY",
    )
    location = models.CharField(max_length=255, blank=True, null=True, db_column="LOCATION")

    class Meta:
        db_table = "POC_Complete_Work"

    def __str__(self):
        return f"{self.id} - {self.status}"



class WorkCompleteImage(BaseModel):
    """
    WorkCompleteImage model where all information about the work completion images is stored
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_column="ID",
    )
    work_completion = models.ForeignKey(
        CompleteWork,
        on_delete=models.CASCADE,
        related_name="work_completion_images",
        db_column="WORK_ID",
    )
    evidence_photo = models.ImageField(
        upload_to="work_evidence/",
        blank=True,
        null=True,
        db_column="EVIDENCE_PHOTO",
    )


    class Meta:
        db_table = "POC_WORK_COMPLETE_IMAGE"

    def __str__(self):
        return f"{self.work_completion} - {self.id}".strip()


