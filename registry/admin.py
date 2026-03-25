from django.contrib import admin
from .models import Member, Baptism, Confirmation, FirstHolyCommunion, Marriage, LastRites, Pledge, PledgePayment

admin.site.register(Member)
admin.site.register(Baptism)
admin.site.register(Confirmation)
admin.site.register(FirstHolyCommunion)
admin.site.register(Marriage)
admin.site.register(LastRites)
admin.site.register(Pledge)
admin.site.register(PledgePayment)
