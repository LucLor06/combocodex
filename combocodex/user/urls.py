from django.urls import path
from . import views

urlpatterns = [
    path('resend-email/', views.email_resend, name='email-resend'),
    path('shop/', views.shop, name='shop'),
    path('inventory/', views.inventory, name='inventory'),
    path('settings/', views.settings, name='settings'),
    path('search/', views.search, name='search'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('profile/<pk>/', views.profile, name='profile'),
]