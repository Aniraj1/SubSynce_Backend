import uuid
from django.db import models
from authuser.model.softdeletemodel import BaseModel
from authuser.model.user import User



class Client(BaseModel):
    """
    Client model where all information about the client is stored
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    first_name = models.CharField(max_length=255, db_column="FIRST_NAME")
    last_name = models.CharField(
        max_length=255, blank=True, null=True, db_column="LAST_NAME"
    )
    phone = models.CharField(
        max_length=255, blank=True, null=True, unique=True, db_column="PHONE"
    )
    email = models.EmailField(blank=True, db_column="EMAIL")

    class Meta:
        db_table = "POC_CLIENT"
        

    def __str__(self):
        return f"{self.first_name} {self.last_name} || {self.id}".strip()


class Site(BaseModel):
    """
    Site model where all information about the site is stored
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    name = models.CharField(max_length=255, db_column="NAME")
    address = models.CharField(max_length=255, db_column="ADDRESS")
    cleaning_frequency = models.CharField(max_length=255, db_column="CLEANING_FREQUENCY")
    price = models.DecimalField(max_digits=10, decimal_places=2, db_column="PRICE")
    client_id = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="sites",
        db_column="CLIENT_ID",
    )
    cleaning_instructions = models.TextField(blank=True, null=True, db_column="CLEANING_INSTRUCTIONS")
    assigned_contractor = models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null=True, related_name="assigned_contractors", db_column="ASSIGNED_CONTRACTOR")
    
    class Meta:
        db_table = "POC_SITE"

    def __str__(self):
        return f"{self.id}"


class SiteImage(BaseModel):
    """
    SiteImage model where all information about the site images is stored
    """
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name="images",
        db_column="SITE_ID",
    )
    image = models.ImageField(
        upload_to="site_images/",
        blank=True,
        null=True,
        db_column="IMAGE",
    )

    class Meta:
        db_table = "POC_SITE_IMAGE"

    def __str__(self):
        return f"{self.site.name} - {self.id}".strip()