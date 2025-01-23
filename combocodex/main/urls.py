from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('combos/submit/', views.combos_submit, name='combos-submit'),
    path('combos/verify/', views.combos_verify, name='combos-verify'),
    path('combos/search/', views.combos_search, name='combos-search'),
    path('combos/<pk>/view/', views.combos_view, name='combos-view'),
    path('combos/<pk>/', views.combos_combo, name='combos-combo'),
    path('requests/submit/', views.requests_submit, name='requests-submit'),
    path('requests/', views.requests_list, name='requests')
]