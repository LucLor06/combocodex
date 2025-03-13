from django.shortcuts import render
from .models import User, UserColor, UserTheme, UserBackground
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.shortcuts import redirect
from django.contrib.auth import logout
from django.contrib.auth.forms import PasswordResetForm
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum
from django.contrib import messages

def email_resend(request):
    if request.method == "POST":
        try:
            email = EmailAddress.objects.get(email__iexact=request.POST.get('email'))
            if not email.verified:
                send_email_confirmation(request, email.user, email=email.email)
                message = 'A new verification email has been sent!'
            else:
                message = 'This email has already been verified!'
        except EmailAddress.DoesNotExist:
            message = 'An account with that email does not exist.'
        return render(request, 'partials/modal-message.html', {'message': message})
    return render(request, 'account/verification_resend.html')

@login_required
def shop(request):
    if request.method == 'POST':
        if 'user_color' in request.POST:
            user_color = UserColor.objects.get(id=request.POST['user_color'])
            user_color.purchase(request.user)
            item = user_color
        elif 'user_theme' in request.POST:
            user_theme = UserTheme.objects.get(id=request.POST['user_theme'])
            user_theme.purchase(request.user)
            item = user_theme
        elif 'user_background' in request.POST:
            user_background = UserBackground.objects.get(id=request.POST['user_background'])
            user_background.purchase(request.user)
            item = user_background
        if item:
            messages.add_message(request, messages.SUCCESS, f'Purchased {item.name}')
    context = {'user_colors': UserColor.objects.exclude(users=request.user), 'user_themes': UserTheme.objects.exclude(users=request.user), 'user_backgrounds': UserBackground.objects.exclude(users=request.user)}
    return render(request, 'shop.html', context)

@login_required
def inventory(request):
    context = {'user_colors': request.user.user_colors.all(), 'user_themes': request.user.user_themes.exclude(name='Custom'), 'user_backgrounds': request.user.user_backgrounds.all()}
    try:
        custom_theme = request.user.user_themes.get(name='Custom')
        context['custom_theme'] = custom_theme
    except UserTheme.DoesNotExist:
        pass
    if request.POST:
        if 'user_color' in request.POST:
            user_color = UserColor.objects.get(id=request.POST['user_color'])
            previous_item = request.user.user_color
            user_color.set(request.user)
            item = user_color
        elif 'user_theme' in request.POST:
            user_theme = UserTheme.objects.get(id=request.POST['user_theme'])
            previous_item = request.user.user_theme
            user_theme.set(request.user)
            item = user_theme
        elif 'custom_theme' in request.POST:
            previous_item = request.user.user_theme
            request.user.user_theme = context['custom_theme']
            request.user.theme_color = request.POST['custom_theme']
            item = context['custom_theme']
            request.user.save()
        elif 'user_background' in request.POST:
            user_background = UserBackground.objects.get(id=request.POST['user_background'])
            previous_item = request.user.user_background
            user_background.set(request.user)
            item = user_background
        if item:
            messages.add_message(request, messages.SUCCESS, f'Changed from {previous_item.name} to {item.name}')
    return render(request, 'inventory.html', context)

@login_required
def settings(request):
    errors = []
    if request.method == 'POST':
        if 'email' in request.POST:
            email = EmailAddress.objects.filter(email__iexact=request.POST.get('email'))
            if email.exists():
                errors.append('An account with this email already exists')
            else:
                EmailAddress.objects.get(user=request.user).delete()
                email = EmailAddress.objects.create(user=request.user, email=request.POST['email'], verified=False, primary=True)
                send_email_confirmation(request, request.user, email=request.POST['email'])
                logout(request)
                return redirect('account_email_verification_sent')     
    return render(request, 'account/settings.html', {'errors': errors})

@login_required
def mail(request):
    show = request.GET.get('show', 'unread')
    mail = request.user.mail.all()
    if show == 'unread':
        mail = mail.filter(read=False)
    mailbox = list(mail)
    mail.update(read=True)
    context = {'mailbox': mailbox}
    return render(request, 'mail.html', context)

def profile(request, pk):
    from main.models import Legend, Weapon, Request, DailyChallenge
    user = get_object_or_404(User, pk=pk)
    legends = Legend.objects.all()
    weapons = Weapon.objects.all()
    context = {'user': user}
    if 'view' in request.GET:
        view = request.GET['view']
        if view == 'general':
            context.update({'legends': legends, 'weapons': weapons, 'legends_percent': round((user.legends.count() / legends.count()) * 100, 2), 'weapons_percent': round((user.weapons.count() / weapons.count()) * 100, 2)})
            return render(request, 'profile/general.html', context)
        elif view == 'requests':
            requests = Request.objects.all()
            context.update({'requests': requests, 'requests_percent': round((user.requests.count() / requests.count()) * 100, 2), 'completed_requests_percent': round((user.completed_requests.count() / requests.count()) * 100, 2)})
            return render(request, 'profile/requests.html', context)
        elif view == 'items':
            user_colors = UserColor.objects.all()
            user_themes = UserTheme.objects.all()
            user_backgrounds = UserBackground.objects.all()
            context.update({'user_colors': user_colors, 'user_themes': user_themes, 'user_backgrounds': user_backgrounds, 'user_colors_percent': round((user.user_colors.count() / user_colors.count()) * 100, 2), 'user_themes_percent': round((user.user_themes.count() / user_themes.count()) * 100, 2), 'user_backgrounds_percent': round((user.user_backgrounds.count() / user_backgrounds.count()) * 100, 2)})
            return render(request, 'profile/items.html', context)
        elif view == 'challenges':
            daily_challenges = DailyChallenge.objects.all()
            context.update({'daily_challenges': daily_challenges, 'daily_challenges_percent': round((user.daily_challenges.count() / daily_challenges.count()) * 100, 2)})
            return render(request, 'profile/challenges.html', context)
        elif view == 'favorites':
            favorites = user.favorite_combos.all()
            context.update({'combos': favorites})
            return render(request, 'profile/favorites.html', context)
    else:
        context.update({'total_views': request.user.combos.aggregate(total_views=Sum('views'))['total_views'], 'legends': legends, 'weapons': weapons, 'legends_percent': round((user.legends.count() / legends.count()) * 100, 2), 'weapons_percent': round((user.weapons.count() / weapons.count()) * 100, 2)})
    return render(request, 'profile/profile.html', context)

def search(request):
    username = request.GET.get('user')
    users = User.objects.all() if not username else User.objects.filter(username__icontains=username)  
    user_count = users.count()
    page_number = request.GET.get('page', 1)
    paginator = Paginator(users, 15)
    page = paginator.get_page(page_number)
    users = page.object_list
    context = {'users': users, 'page': page, 'user_count': user_count}
    return render(request, 'user-search.html', context)

def leaderboard(request):
    ordering = request.GET.get('order_by', '-total')
    if ordering == '-total':
        users = User.objects.annotate(total=(Count('combos') + Count('combos__request') + Count('combos__daily_challenge', distinct=True)))
    elif ordering == '-completed_requests':
        users = User.objects.annotate(completed_requests=Count('combos__request'))
    elif ordering == '-daily_challenges':
        users = User.objects.annotate(daily_challenges=Count('combos__daily_challege', distinct=True))
    users = users.order_by(ordering)
    context = {'users': users[:20]}
    return render(request, 'leaderboard.html', context)
