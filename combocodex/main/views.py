from django.shortcuts import render
from main.models import Legend, Weapon

def home(request):
    return render(request, 'home.html')

def combos_submit(request):
    context = {'legends': Legend.objects.all(), 'weapons': Weapon.objects.all()}
    return render(request, 'combos/submit.html', context)