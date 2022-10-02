from django.contrib import admin

# Register your models here.

from . import models

admin.site.register(models.Account)
admin.site.register(models.Address)
admin.site.register(models.TelcoProvider)
admin.site.register(models.Transfer)
admin.site.register(models.Card)
admin.site.register(models.DirectDebit)
admin.site.register(models.StandingOrder)