from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from .models import Combo, Legend

@receiver(pre_delete, sender=Combo)
def combo_pre_delete(sender, instance, **kwargs):
    if instance.is_verified:
        instance.set_next_recommended()
        instance.update_spreadsheet(deleting=True)

@receiver(post_delete, sender=Combo)
def combo_post_delete(sender, instance, **kwargs):
    if instance.video:
        instance.video.delete(save=False)
    if instance.poster:
        instance.poster.delete(save=False)