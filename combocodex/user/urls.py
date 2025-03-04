from django.urls import path, re_path
from . import views
import allauth.account.views as allauth_views

urlpatterns = [
    path('login/', allauth_views.login, name='account_login'),
    path('logout/', allauth_views.logout, name='account_logout'),
    path('register/', allauth_views.signup, name='account_signup'),
    path('email-verification-sent/', allauth_views.email_verification_sent, name='account_email_verification_sent'),
    re_path(r'^email-confirm/(?P<key>[-:\w]+)/$', allauth_views.confirm_email, name='account_confirm_email'),
    path('password-reset/', allauth_views.password_reset, name='account_reset_password'),
    re_path(r'^password-reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<key>.+)/$', allauth_views.password_reset_from_key, name='account_reset_password_from_key'),
    path('password-reset-sent/', allauth_views.password_reset_done, name='account_reset_password_done'),
    path('password-reset-done/', allauth_views.password_reset_from_key_done, name='account_reset_password_from_key_done'),
    path('logout/', allauth_views.logout, name='account_logout'),
    path('resend-email/', views.email_resend, name='email-resend'),
    path('shop/', views.shop, name='shop'),
    path('inventory/', views.inventory, name='inventory'),
    path('settings/', views.settings, name='settings'),
    path('user-search/', views.search, name='user-search'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('mail/', views.mail, name='mail'),
    path('profile/<pk>/', views.profile, name='profile'),
]