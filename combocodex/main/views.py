from django.shortcuts import render
from user.models import User
from main.models import Combo, WebsiteSocial

def home(request):
    context = {'socials': WebsiteSocial.objects.all(), 'combo_count': Combo.objects.count(), 'user_count': User.objects.count()}
    return render(request, 'home.html', context)