import uuid

from django.db import models
from django_softdelete.models import SoftDeleteModel


class BaseModel(SoftDeleteModel):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_column="CREATED_AT")
    updated_at = models.DateTimeField(auto_now=True, db_column="UPDATED_AT")
    is_deleted = models.BooleanField(default=False, db_column="IS_DELETED")
    deleted_at = models.DateTimeField(
        blank=True, null=True, db_column="DELETED_AT"
    )

    class Meta:
        abstract = True