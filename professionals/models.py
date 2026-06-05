from django.db import models

from core.models import TimeStampedModel


class Specialty(TimeStampedModel):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name


class Professional(TimeStampedModel):
    specialty = models.ForeignKey(
        Specialty,
        on_delete=models.PROTECT,
        related_name='professionals',
    )
    full_name = models.CharField(max_length=150)
    registration_number = models.CharField(max_length=30)
    bio = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('full_name',)

    def __str__(self):
        return self.full_name
