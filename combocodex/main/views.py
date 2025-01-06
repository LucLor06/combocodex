from django.shortcuts import render
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge

def home(request):
    context = {'combos': Combo.objects.verified()[:4], 'socials': WebsiteSocial.objects.all(), 'daily_challenge': DailyChallenge.objects.latest('-id'), 'combo_count': Combo.objects.count(), 'user_count': User.objects.count()}
    return render(request, 'home.html', context)