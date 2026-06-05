from django.db import models


class TimeStampedModel(models.Model):
    '''Abstract base model with auditable timestamps.

    All concrete models in the project must inherit from this class
    so that every table carries created_at and updated_at.
    '''

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
