from django.db.models.signals import post_save
from django.dispatch import receiver
from models import Appointment

@receiver(post_save, sender=Appointment)
def send_appointment_confirmation(sender, instance, created, **kwargs):
    if created and instance.status == 'confirmed':
        # Отправка email подтверждения
        pass