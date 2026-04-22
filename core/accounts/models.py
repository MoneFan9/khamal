from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """
    Custom User model for Khamal.
    Extends AbstractUser to allow for future custom fields.
    """
    pass
