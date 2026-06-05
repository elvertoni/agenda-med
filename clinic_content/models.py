from django.db import models

from core.models import TimeStampedModel


class PriceItem(TimeStampedModel):
    specialty = models.ForeignKey(
        'professionals.Specialty',
        on_delete=models.PROTECT,
        related_name='price_items',
    )
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('specialty__name', 'name')

    def __str__(self):
        return self.name


class ServiceProtocol(TimeStampedModel):
    title = models.CharField(max_length=150)
    content = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('title',)

    def __str__(self):
        return self.title


class ExamProtocol(TimeStampedModel):
    specialty = models.ForeignKey(
        'professionals.Specialty',
        on_delete=models.PROTECT,
        related_name='exam_protocols',
    )
    exam_name = models.CharField(max_length=150)
    preparation_instructions = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ('specialty__name', 'exam_name')

    def __str__(self):
        return self.exam_name
