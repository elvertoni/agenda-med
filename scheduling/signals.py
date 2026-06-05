from django.db.models.signals import post_save
from django.dispatch import receiver

from messaging.services import schedule_presence_confirmation

from .models import Appointment


@receiver(post_save, sender=Appointment)
def create_presence_confirmation(sender, instance, created, **kwargs):
    if created:
        schedule_presence_confirmation(instance)
