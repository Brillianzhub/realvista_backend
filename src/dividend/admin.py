from django.contrib import admin

# Register your models here.
from .models import Dividend, DividendShare


admin.site.register(Dividend)
admin.site.register(DividendShare)
