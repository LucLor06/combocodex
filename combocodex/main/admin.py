from django.contrib import admin
from . import models

admin.site.register([models.Legend, models.Weapon, models.Combo, models.WebsiteSocial, models.DailyChallenge, models.Guest])