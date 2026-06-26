from django.db import models


class Environment(models.TextChoices):
    DEV = "DEV"
    PROD = "PROD"
    REVIEW_APP = "REVIEW-APP"
    TEST = "TEST"
