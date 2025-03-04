from django.urls import path
from . import views

urlpatterns = [
    path('combos/', views.ComboListView.as_view(), name='api-combos'),
    path('link/', views.api_user_link, name='api-link')
]