from django.dispatch import receiver
from django.db.models.signals import m2m_changed
from .models import Legend, LegendWeaponPair, Combo

@receiver(m2m_changed, sender=Legend.weapons.through)
def legend_weapons_changed(sender, instance, action, reverse, model, pk_set, **kwargs):
    if action == 'post_add':
        for weapon in instance.weapons.all():
            LegendWeaponPair.objects.get_or_create(legend=instance, weapon=weapon)
