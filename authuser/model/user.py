import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    PermissionsMixin,
    UserManager,
)
from django.db import models
from authuser.model.softdeletemodel import BaseModel



ROLE_CHOICES = (
            ("ADMINISTRATOR", "ADMINISTRATOR"),
            ("CONTRACTOR", "CONTRACTOR"),
            ("OWNER", "OWNER"),
)

class CustomUserManager(UserManager):
    """
    Custom user model manager where username and email is the unique identifiers
    """

    def _create_user(self, username, email, password, **extra_fields):
        if not username:
            raise ValueError("Username is required")
        if email:
            email = self.normalize_email(email)
            user = self.model(email=email, **extra_fields)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email="", password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(
        self, username, email="", password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)   
        return self._create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    """
    User model which contain all the basic information to create user
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    username = models.CharField(
        max_length=255, unique=True, db_column="USERNAME"
    )
    email = models.EmailField(blank=True, db_column="EMAIL")
    is_superuser = models.BooleanField(default=False, db_column="IS_SUPERUSER")
    is_staff = models.BooleanField(default=False, db_column="IS_STAFF")
    is_user = models.BooleanField(default=True, db_column="IS_USER")
    role = models.CharField(
        max_length=255,
        choices=ROLE_CHOICES,
        default="CONTRACTOR",
        db_column="ROLE",
    )

    objects = CustomUserManager()
    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []  # type: List[str]

    class Meta:
        db_table = "POC_USER"

    def __str__(self):
        return self.username


class UserDetail(BaseModel):
    """
    User detail model where all extra information about user are store
    """
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, db_column="ID"
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        db_column="USER_ID",
        related_name="user_detail",
    )
    first_name = models.CharField(max_length=255, db_column="FIRST_NAME")
    last_name = models.CharField(
        max_length=255, blank=True, null=True, db_column="LAST_NAME"
    )
    phone = models.CharField(
        max_length=255, blank=True, null=True, unique=True, db_column="PHONE"
    )

    class Meta:
        db_table = "POC_USER_DETAIL"

    def __str__(self):
        return self.user.username