from django.shortcuts import render
from main.models import Legend, Weapon, Social, DailyChallenge

def home(request):
    context = {'socials': Social.objects.all(), 'daily_challenge': DailyChallenge.objects.latest('id')}
    return render(request, 'home.html', context)

def combos_submit(request):
    context = {'legends': Legend.objects.all(), 'weapons': Weapon.objects.all()}
    return render(request, 'combos/submit.html', context)