from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import User
from main.models import Guest

@receiver(post_save, sender=User)
def user_post_save(sender, instance: User, created, **kwargs):
    if created:
        try:
            guest = Guest.objects.get(username__iexact=instance.username)
            guest.transfer_combos_to_user(instance)
        except Guest.DoesNotExist:
            pass
        instance.collect_codex_coins()
        instance.check_trusted()
