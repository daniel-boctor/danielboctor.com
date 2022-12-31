from django.contrib import admin

from .models import User, Portfolio, RetsCSV, NB

# Register your models here.

admin.site.register(User)
admin.site.register(Portfolio)
admin.site.register(RetsCSV)
admin.site.register(NB)