from django.contrib import admin
from . import models

admin.site.register(models.Weapon)
admin.site.register(models.Legend)
admin.site.register(models.LegendWeaponPair)