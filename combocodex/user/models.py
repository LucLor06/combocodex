from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.functional import cached_property
from django.db.models import Prefetch, Q

class User(AbstractUser):
    codex_coins = models.PositiveIntegerField(default=0)

    def transfer_combos_to_user(self, user):
        combos = self.combos.all()
        user.combos.add(combos)
        self.combos.remove(combos)

    def collect_codex_coins(self):
        from main.models import Combo, DailyChallenge, Request
        combos = self.combos.count() * Combo.CODEX_COINS
        requests = Request.objects.filter(combos__users=self).count() * Request.CODEX_COINS
        daily_challenges = DailyChallenge.objects.filter(combos__users=self).count() * DailyChallenge.CODEX_COINS
        self.codex_coins += (combos + requests + daily_challenges)
        self.save()

    @cached_property
    def legends(self):
        from main.models import Legend, Combo
        return Legend.objects.prefetch_related(
            Prefetch('combos_one', queryset=Combo.objects.prefetch_related('users')),
            Prefetch('combos_two', queryset=Combo.objects.prefetch_related('users'))
        ).filter(Q(combos_one__users=self) | Q(combos_two__users=self)).distinct()
    
    @cached_property
    def weapons(self):
        from main.models import Weapon, Combo
        return Weapon.objects.prefetch_related(
            Prefetch('combos_one', queryset=Combo.objects.prefetch_related('users')),
            Prefetch('combos_two', queryset=Combo.objects.prefetch_related('users'))
        ).filter(Q(combos_one__users=self) | Q(combos_two__users=self)).distinct()
    
    @cached_property
    def daily_challenges(self):
        from main.models import DailyChallenge
        return DailyChallenge.objects.prefetch_related('combos').filter(combos__users=self).distinct()