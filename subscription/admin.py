from django.contrib import admin

from .models import Membership, PayHistory, Subscription, User, UserMembership

admin.site.register(User)
admin.site.register(UserMembership)
admin.site.register(Membership)
admin.site.register(Subscription)
admin.site.register(PayHistory)
