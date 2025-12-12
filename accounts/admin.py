from django.contrib import admin
from django.contrib import admin
from .models import UserSecurity

# Register your models here.
from .models import Customer,Transaction,Credit

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name','phone','balance_display')
    search_fields = ('name','phone')

    def balance_display(self,obj):
        return obj.balance()
    balance_display.short_description='Balance'

admin.site.register(Transaction)
admin.site.register(Credit)


admin.site.register(UserSecurity)