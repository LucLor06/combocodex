from django.shortcuts import render, get_object_or_404
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge, Legend, Weapon, Request
from django.db.models import Q
from django.http import HttpResponse, HttpRequest
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required

def home(request):
    context = {'combos': Combo.objects.verified()[:4], 'socials': WebsiteSocial.objects.all(), 'daily_challenge': DailyChallenge.objects.latest('-id'), 'combo_count': Combo.objects.verified().count(), 'user_count': User.objects.count(), 'weekly_user': User.weekly_user()}
    return render(request, 'home.html', context)

def help(request):
    return render(request, 'help.html')

def combos_increment_view(request, pk):
    combo = Combo.objects.get(pk=pk)
    combo.views += 1
    combo.save()
    return HttpResponse('')

@login_required
def combos_favorite(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    if 'favorite' in request.POST:
        request.user.favorite_combos.add(combo)
    else:
        request.user.favorite_combos.remove(combo)
    return HttpResponse(status=200)


def combos_submit(request):
    read_rules = request.session.get('read_rules', False)
    if not read_rules:
        request.session['read_rules'] = True
    context = {'legends': Legend.objects.prefetch_related('weapons'), 'read_rules': read_rules}
    if 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    if request.method == 'POST':
        Combo.objects.create_from_post(request.POST, request.FILES, request.user)
        message = 'Combo submitted! Please note it may take some time before mods verify your combo!'
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
        action = request.POST.get('action', 'accept')
        if action == 'accept':
            is_outdated = bool(request.POST.get('is_outdated', False))
            is_map_specific = bool(request.POST.get('is_map_specific', False))
            is_alternate_gamemode = bool(request.POST.get('is_alternate_gamemode', False))
            combo.is_outdated = is_outdated
            combo.is_map_specific = is_map_specific
            combo.is_alternate_gamemode = is_alternate_gamemode
            combo.save()
            combo.verify()
            message = 'Combo verified!'
        elif action == 'accept_all':
            for combo in Combo.objects.unverified():
                combo.verify()
            message = 'All combos verified!'
        elif action == 'reject':
            message = 'Combo rejected.'
            reasoning = '. '.join(request.POST.getlist('reason')) + '.' if 'reason' in request.POST else None
            combo.reject(reasoning)
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'combos/verify.html', context)

def combos_combo(request, pk):
    combo = Combo.objects.get(pk=pk)
    context = {'combo': combo, 'similar_combos': combo.get_similar()}
    return render(request, 'combos/combo.html', context)

def combos_spreadsheet(request):
    return render(request, 'combos/spreadsheet.html')

def combos_search(request):
    if 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    page_number = request.GET.get('page', 1)
    weapons = request.GET.getlist('weapon', [])
    legends =  request.GET.getlist('legend', [])
    order_by = request.GET.get('order_by', '-id') 
    show_unverified = bool(request.GET.get('show_unverified', False))
    users = request.GET.getlist('user', [])
    combos, page, count = Combo.objects.search(legends, weapons, users, order_by, show_unverified, page_number)
    context = {'combos': combos, 'page': page, 'count': count}
    if len(request.GET) > 0 and 'filter_users' not in request.GET and 'user' not in request.GET:
        return render(request, 'combos/search.html', context)
    context.update({'legends': Legend.objects.all(), 'weapons': Weapon.objects.all(), 'users': User.objects.filter(username__in=request.GET.getlist('user', []))})
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


@staff_member_required
def requests_delete(request, pk):
    combo_request = Request.objects.get(pk=pk)
    if combo_request.user:
        from user.models import Mail
        reasoning = '. '.join(request.POST.getlist('reason')) + '.' if 'reason' in request.POST else None
        mail_content = f'Your request {combo_request.legend_one.name} ({combo_request.weapon_one.name}) {combo_request.legend_two.name} ({combo_request.weapon_two.name}) has been deleted.'
        if reasoning:
            mail_content += f' The following reason(s) were provided: {reasoning}'
        mail = Mail.objects.create(subject='Request Deleted', type='bad', content=mail_content)
        mail.users.add(combo_request.user)
    combo_request.delete()
    return HttpResponse(status=200)