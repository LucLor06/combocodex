from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('robots.txt', views.robots_txt, name='robots-txt'),
    path('about', views.about, name='about'),
    path('combos/', views.redirect_combos_search, name='combos-redirect'),
    path('combos/submit/', views.combos_submit, name='combos-submit'),
    path('combos/verify/', views.combos_verify, name='combos-verify'),
    path('combos/search/', views.combos_search, name='combos-search'),
    path('combos/twitter-embed/<pk>/', views.combos_twitter_embed, name='combos-twitter-embed'),
    path('combos/<pk>/view/', views.combos_increment_view, name='combos-increment-view'),
    path('combos/<pk>/favorite/', views.combos_favorite, name='combos-favorite'),
    path('combos/spreadsheet/', views.combos_spreadsheet, name='combos-spreadsheet'),
    path('combos/<pk>/', views.combos_combo, name='combos-combo'),
    path('combos/<pk>/update/', views.ComboUpdateView.as_view(), name='combos-update'),
    path('combos/<pk>/delete/', views.ComboDeleteView.as_view(), name='combos-delete'),
    path('requests/<pk>/delete/', views.requests_delete, name='requests-delete'),
    path('requests/submit/', views.requests_submit, name='requests-submit'),
    path('requests/', views.requests_list, name='requests')
]