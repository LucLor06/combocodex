from django.contrib import admin
from .models import User, UserColor, UserTheme, UserBackground, Mail

admin.site.register([User, UserColor, UserTheme, UserBackground, Mail])