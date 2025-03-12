import django
import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from main.models import DailyChallenge, Legend

legends = Legend.objects.exclude(name='Universal')

legend_one = random.choice(legends)
weapon_one = random.choice(legend_one.weapons.exclude(name='Unarmed'))
legend_two = random.choice(legends)
weapon_two = random.choice(legend_two.weapons.exclude(name='Unarmed'))

daily_challenge = DailyChallenge.objects.create(legend_one=legend_one, weapon_one=weapon_one, legend_two=legend_two, weapon_two=weapon_two)