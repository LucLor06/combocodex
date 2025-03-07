from django.urls import path
from . import views

urlpatterns = [
    path('combos/search/', views.ComboListView.as_view(), name='api-combos-search'),
    path('combos/submit/', views.api_combos_upload, name='api-combos-submit'),
    path('link/', views.api_user_link, name='api-link'),
    path('legends/', views.LegendListView.as_view(), name='api-legends'),
    path('weapons/', views.WeaponListView.as_view(), name='api-weapons'),
]