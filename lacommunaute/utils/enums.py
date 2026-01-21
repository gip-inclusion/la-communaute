from django.db import models


class PeriodAggregation(models.TextChoices):
    MONTH = "MONTH"
    WEEK = "WEEK"


class Environment(models.TextChoices):
    DEV = "DEV"
    PROD = "PROD"
    REVIEW_APP = "REVIEW-APP"
    TEST = "TEST"
