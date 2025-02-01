from django.shortcuts import render
from .models import User, UserColor, UserTheme
from django.contrib.auth.decorators import login_required
from allauth.account.models import EmailAddress
from allauth.account.utils import send_email_confirmation
from django.shortcuts import redirect
from datetime import datetime, timedelta
from django.utils import timezone

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
        elif 'user_theme' in request.POST:
            user_theme = UserTheme.objects.get(id=request.POST['user_theme'])
            user_theme.purchase(request.user)
    context = {'user_colors': UserColor.objects.exclude(users=request.user), 'user_themes': UserTheme.objects.exclude(users=request.user)}
    return render(request, 'shop.html', context)

@login_required
def inventory(request):
    context = {'user_colors': request.user.user_colors.all(), 'user_themes': request.user.user_themes.all()}
    if request.POST:
        if 'user_color' in request.POST:
            user_color = UserColor.objects.get(id=request.POST['user_color'])
            user_color.set(request.user)
        elif 'user_theme' in request.POST:
            user_theme = UserTheme.objects.get(id=request.POST['user_theme'])
            user_theme.set(request.user)
    return render(request, 'inventory.html', context)