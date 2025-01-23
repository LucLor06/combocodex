from django.shortcuts import render
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge, Legend, Weapon, Request
from django.db.models import Q
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

def combos_search(request):
    if 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    page_number = request.GET.get('page', 1)
    weapons = request.GET.getlist('weapon', [])
    legends =  request.GET.getlist('legend', [])
    order_by = request.GET.get('order_by', 'created_on') 
    show_unverified = bool(request.GET.get('show_unverified', False))
    users = request.GET.getlist('user', [])
    combos, page, count = Combo.objects.search(legends, weapons, users, order_by, show_unverified, page_number)
    context = {'combos': combos, 'page': page, 'count': count}
    if len(request.GET) > 0 and 'filter_users' not in request.GET:
        return render(request, 'combos/search.html', context)
    context.update({'legends': Legend.objects.all(), 'weapons': Weapon.objects.all()})
    return render(request, 'combos/search.html', context)

def requests_list(request):
    requests = Request.objects.incomplete()
    context = {'requests': requests}
    return render(request, 'requests/requests.html', context)

def requests_submit(request):
    if request.method == 'POST':
        legends = [request.POST['legend_one'], request.POST['legend_two']]
        weapons = [request.POST['weapon_one'], request.POST['weapon_two']]
        existing_requests = Request.objects.filter(Q(legend_one=legends[0], weapon_one=weapons[0], legend_two=legends[1], weapon_two=weapons[1]) | Q(legend_one=legends[1], weapon_one=weapons[1], legend_two=legends[0], weapon_two=weapons[0]))
        if existing_requests.exists():
            message = 'There is already a request for this open!'
            return render(request, 'partials/modal-message.html', {'message': message})
        combos, count = Combo.objects.search(legends, weapons, paginate=False)
        if 'confirmation' in request.POST or not combos.exists():
            Request.objects.create_from_post(request.POST, request.user)
            message = 'Request submitted!'
            return render(request, 'partials/modal-message.html', {'message': message})
        if combos.exists():
            context = {'combos': combos, 'count': count, 'notes': request.POST.get('notes')}
            return render(request, 'requests/found.html', context)
    context = {'legends': Legend.objects.all()}
    return render(request, 'requests/submit.html', context)