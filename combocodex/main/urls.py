from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('combos/submit/', views.combos_submit, name='combos-submit'),
    path('combos/<pk>/view/', views.combos_view, name='combos-view')
]