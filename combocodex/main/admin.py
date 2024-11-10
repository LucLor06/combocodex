from django.contrib import admin
from . import models

admin.site.register(models.Weapon)
admin.site.register(models.Legend)
admin.site.register(models.LegendWeaponPair)
admin.site.register(models.Combo)
admin.site.register(models.Social)
admin.site.register(models.DailyChallenge)