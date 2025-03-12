from django.contrib import admin
from . import models

admin.site.register([models.Legend, models.Weapon, models.WebsiteSocial, models.DailyChallenge, models.Guest, models.Request])

class ComboAdmin(admin.ModelAdmin):
    search_fields = ['legend_one__name', 'weapon_one__name', 'legend_two__name', 'weapon_two__name']

admin.site.register(models.Combo, ComboAdmin)