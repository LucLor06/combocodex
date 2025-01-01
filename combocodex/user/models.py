from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from main.models import Legend, Weapon, Combo, DailyChallenge
from django.db.models import Prefetch, Q

class User(AbstractUser):
    codex_coins = models.PositiveIntegerField(default=0)

    @cached_property
    def legends(self):
        return Legend.objects.prefetch_related(
            Prefetch('combos_one', queryset=Combo.objects.prefetch_related('users')),
            Prefetch('combos_two', queryset=Combo.objects.prefetch_related('users'))
        ).filter(Q(combos_one__users=self) | Q(combos_two__users=self)).distinct()
    
    @cached_property
    def weapons(self):
        return Weapon.objects.prefetch_related(
            Prefetch('combos_one', queryset=Combo.objects.prefetch_related('users')),
            Prefetch('combos_two', queryset=Combo.objects.prefetch_related('users'))
        ).filter(Q(combos_one__users=self) | Q(combos_two__users=self)).distinct()
    
    @cached_property
    def daily_challenges(self):
        return DailyChallenge.objects.prefetch_related('combos').filter(combos__users=self).distinct()