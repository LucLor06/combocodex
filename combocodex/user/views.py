from django.shortcuts import render
from .models import User
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