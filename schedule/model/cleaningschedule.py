from datetime import timedelta
import uuid
from django.db import models
from authuser.model.softdeletemodel import BaseModel
from client.model.clientmanage import Site
from authuser.model.user import User



SCHEDULE_STATUS = (
    ("SCHEDULED", "SCHEDULED"),
    ("COMPLETED", "COMPLETED"),
    ("MISSED", "MISSED"),
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

    scheduled_date = models.DateField(db_column="SCHEDULED_DATE")
    scheduled_time = models.TimeField(db_column="SCHEDULED_TIME")

    status = models.CharField(max_length=255, choices=SCHEDULE_STATUS, default="SCHEDULED", db_column="STATUS")
    notes = models.TextField(blank=True, null=True, db_column="NOTES")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_service_schedules",
        db_column="CREATED_BY",
    )
    
    class Meta:
        db_table = "POC_SERVICE_SCHEDULE"

    def __str__(self):
        return f"{self.id}"

