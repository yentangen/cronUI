from django.contrib import admin

from .models import Server, User, Cron

admin.site.register(Server)
admin.site.register(User)
admin.site.register(Cron)
