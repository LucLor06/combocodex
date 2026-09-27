import django
import os
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from main.models import DailyChallenge

daily_challenge_count = 3

for i in range(daily_challenge_count):
    DailyChallenge.objects.create_with_weight()