from django.contrib import admin

from .models import Claim, ClaimAnswer, VerificationQuestion


admin.site.register(Claim)
admin.site.register(ClaimAnswer)
admin.site.register(VerificationQuestion)