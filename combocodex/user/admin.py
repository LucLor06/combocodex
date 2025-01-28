from django.contrib import admin
from .models import User, UserColor

admin.site.register([User, UserColor])