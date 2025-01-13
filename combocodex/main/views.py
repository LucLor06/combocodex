from django.shortcuts import render
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge, Legend
from django.http import HttpResponse
from django.contrib.admin.views.decorators import staff_member_required

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
    if 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    if request.method == 'POST':
        print(request.FILES)
        try:
            user = request.user if request.user.is_authenticated else None
            Combo.objects.create_from_post(request.POST, request.FILES, request.user)
            message = 'Combo submitted! Please note it may take some time before mods verify your combo!'
        except:
            message = 'An error occured. Try again later. If the issue persists reach out on our discord!'
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'combos/submit.html', context)

@staff_member_required
def combos_verify(request):
    combo = None
    try:
        combo = Combo.objects.unverified().latest('id')
    except Combo.DoesNotExist:
        pass
    context = {'combo': combo, 'combos_count': Combo.objects.unverified().count()}
    if request.method == 'POST':
        is_accepted = request.POST['is_accepted']
        if is_accepted == 'all':
            for combo in Combo.objects.unverified():
                combo.verify()
            message = 'All combos verified!'
        elif is_accepted =='true':
            is_outdated = bool(request.POST.get('is_outdated', False))
            is_map_specific = bool(request.POST.get('is_map_specific', False))
            combo.is_outdated = is_outdated
            combo.is_map_specific = is_map_specific
            combo.save()
            combo.verify()
            message = 'Combo verified!'
        else:
            combo.delete()
            message = 'Combo rejected.'
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'combos/verify.html', context)

def combos_combo(request, pk):
    combo = Combo.objects.get(pk=pk)
    context = {'combo': combo, 'similar_combos': combo.get_similar()}
    return render(request, 'combos/combo.html', context)
