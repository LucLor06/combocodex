from django.shortcuts import render
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge, Legend
from django.http import HttpResponse

def home(request):
    context = {'combos': Combo.objects.verified()[:4], 'socials': WebsiteSocial.objects.all(), 'daily_challenge': DailyChallenge.objects.latest('-id'), 'combo_count': Combo.objects.verified().count(), 'user_count': User.objects.count()}
    return render(request, 'home.html', context)

def combos_view(request, pk):
    combo = Combo.objects.get(pk=pk)
    combo.views += 1
    combo.save()
    return HttpResponse('')

def combos_submit(request):
    context = {'legends': Legend.objects.prefetch_related('weapons')}
    if 'username' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['username'])
        return render(request, 'combos/submit.html#users', {'users': users})
    if request.method == 'POST':
        try:
            Combo.objects.create_from_post(request.POST, request.FILES)
            message = 'Combo submitted! Please note it may take some time before mods verify your combo!'
        except:
            message = 'An error occured. Try again later. If the issue persists reach out on our discord!'
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'combos/submit.html', context)