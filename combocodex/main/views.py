from django.shortcuts import render, get_object_or_404, redirect
from user.models import User
from main.models import Combo, WebsiteSocial, DailyChallenge, Legend, Weapon, Request
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponse, HttpRequest
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from config.settings import BASE_DIR
from datetime import datetime
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.generic import UpdateView, DeleteView
from django.contrib.auth.mixins import UserPassesTestMixin

class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff

def home(request):
    context = {'combos': Combo.objects.verified()[:4], 'socials': WebsiteSocial.objects.all(), 'daily_challenge': DailyChallenge.objects.latest('id'), 'combo_count': Combo.objects.verified().count(), 'user_count': User.objects.count(), 'weekly_user': User.weekly_user(), 'today_combo_count': Combo.objects.filter(created_on=datetime.today()).count()}
    return render(request, 'home.html', context)

def help(request):
    return render(request, 'help.html')

def about(request):
    return render(request, 'about.html')

def robots_txt(request):
    content = """
    User-agent: Twitterbot
    Allow: /

    User-agent: *
    Disallow: /admin/
    Disallow: /api/
    Disallow: /login/
    Disallow: /register/
    Disallow: /media/
    Disallow: /combos/
    Allow: /combos/search/
    Allow: /combos/submit/
    Allow: /
    """
    return HttpResponse(content, content_type='text/plain')

def combos_increment_view(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    combo.views += 1
    combo.save(skip_custom_logic=True)
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
    if request.htmx and 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    if request.method == 'POST':
        video = request.FILES.get('video')
        if video.size > 25 * 1024 * 1024:
            message = 'Please make sure your videos are less than 25mb.'
        else:
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
    if combo:
        context['similar_combos'] = combo.get_combos_with_matching_pairs()
    if request.htmx and request.method == 'POST':
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
            reasons = [reason for reason in request.POST.getlist('reason') if reason != ''] if 'reason' in request.POST else None
            reasoning = '. '.join(reasons).rstrip('.') + '.' if reasons else None
            combo.reject(reasoning)
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'combos/verify.html', context)

def combos_combo(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    context = {'combo': combo, 'related_combos': combo.get_combos_with_matching_legends() if not combo.has_universal else combo.get_combos_with_matching_pairs()}
    return render(request, 'combos/combo.html', context)

@xframe_options_exempt
def combos_twitter_embed(request, pk):
    combo = get_object_or_404(Combo, pk=pk)
    context = {'combo': combo}
    return render(request, 'combos/twitter_embed.html', context)

def combos_spreadsheet(request):
    context = {'spreadsheet': ''}
    with open(BASE_DIR / 'main/templates/combos/rendered_sheet.html', 'r') as spreadsheet:
        context['spreadsheet'] = spreadsheet.read()
    response = render(request, 'combos/spreadsheet.html', context)
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def combos_search(request: HttpRequest):
    if request.htmx and 'filter_users' in request.GET:
        users = User.objects.filter(username__icontains=request.GET['filter_users'])
        return render(request, 'combos/submit.html#users', {'users': users})
    page_number = request.GET.get('page', 1)
    weapons = request.GET.getlist('weapon', [])
    legends =  request.GET.getlist('legend', [])
    order_by = request.GET.get('order_by', 'id')
    order_by_function = request.GET.get('order_by_function', 'descending')
    includes = request.GET.getlist('includes', [])
    recommended_first = 'recommended_first' in request.GET if request.GET else True
    users = request.GET.getlist('user', [])
    context = Combo.objects.search(legends, weapons, users, page=page_number, order_by=order_by, order_by_function=order_by_function, recommended_first=recommended_first, ignore_default_excludes=includes)
    if request.htmx and not request.htmx.history_restore_request:
        return render(request, 'combos/search.html#combos', context)
    context.update({
        'selected_legends': [Legend.objects.get(id=id) for id in legends[:2]],
        'selected_weapons': [Weapon.objects.get(id=id) for id in weapons[:2]],
        'order_by': order_by,
        'order_by_function': order_by_function,
        'includes': includes,
        'recommended_first': recommended_first,
        'legends': Legend.objects.all(),
        'weapons': Weapon.objects.all(),
        'users': User.objects.filter(username__in=request.GET.getlist('user', []))})
    return render(request, 'combos/search.html', context)

def redirect_combos_search(request):
    return redirect(reverse('combos-search'))

class ComboUpdateView(UpdateView, StaffRequiredMixin):
    model = Combo
    fields = ['is_outdated', 'is_recommended', 'is_map_specific']

    def form_valid(self, form):
        self.object = form.save()
        print(self.object.is_outdated)
        if self.request.htmx:
            print(self.object)
            context = {'combo': self.object}
            return render(self.request, 'partials/combo.html', context)
        return reverse('combos-combo', kwargs={'pk': self.object.pk})

class ComboDeleteView(DeleteView, StaffRequiredMixin):
    model = Combo

    def get_success_url(self):
        return self.request.POST.get('next', '')

def requests_list(request):
    requests = Request.objects.incomplete()
    context = {'requests': requests}
    return render(request, 'requests/requests.html', context)

def requests_submit(request):
    if request.method == 'POST' and request.htmx:
        legends = [request.POST['legend_one'], request.POST['legend_two']]
        weapons = [request.POST['weapon_one'], request.POST['weapon_two']]
        existing_requests = Request.objects.filter(Q(legend_one=legends[0], weapon_one=weapons[0], legend_two=legends[1], weapon_two=weapons[1]) | Q(legend_one=legends[1], weapon_one=weapons[1], legend_two=legends[0], weapon_two=weapons[0]))
        if existing_requests.exists():
            message = 'There is already a request for this open!'
            return render(request, 'partials/modal-message.html', {'message': message})
        combo_data = Combo.objects.search(legends, weapons, paginate=False)
        combos = combo_data['combos']
        if 'confirmation' in request.POST or not combos.exists():
            user = request.user if type(request.user) == User else None
            Request.objects.create_from_post(request.POST, user)
            message = 'Request submitted!'
            return render(request, 'partials/modal-message.html', {'message': message})
        if combos.exists():
            context = {'combos': combos, 'count': combo_data['combo_count'], 'notes': request.POST.get('notes')}
            return render(request, 'requests/found.html', context)
    context = {'legends': Legend.objects.exclude(name='Universal')}
    return render(request, 'requests/submit.html', context)


@staff_member_required
def requests_delete(request, pk):
    combo_request = get_object_or_404(Request, pk=pk)
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