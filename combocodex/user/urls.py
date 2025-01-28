from django.urls import path
from . import views

urlpatterns = [
    path('resend-email/', views.email_resend, name='email-resend')
]