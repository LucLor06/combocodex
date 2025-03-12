from django.contrib import admin
from .models import User, UserColor, UserTheme, UserBackground, Mail

admin.site.register([UserColor, UserTheme, UserBackground, Mail])

class UserAdmin(admin.ModelAdmin):
    search_fields = ['username']

admin.site.register(User, UserAdmin)