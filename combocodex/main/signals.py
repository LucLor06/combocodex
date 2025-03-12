from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Combo, Legend

@receiver(pre_delete, sender=Combo)
def combo_delete(**kwargs):
    instance = kwargs.get('instance')
    if instance.is_verified:
        instance.update_spreadsheet(deleting=True)
