from django.contrib import admin

# Register your models here.

from .models import *

admin.site.register(Account)
admin.site.register(Address)
admin.site.register(TelcoProvider)
admin.site.register(Transfer)
admin.site.register(Card)
admin.site.register(DirectDebit)
admin.site.register(StandingOrder)