from django.contrib import admin
from .models import User, UserColor, UserTheme

admin.site.register([User, UserColor, UserTheme])