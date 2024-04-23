from django.contrib import admin

from AgentMap.models import Agent, Form, LicensedState


# Registration of the Form model in the admin site
@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    pass


# Registration of the Agent model in the admin site
@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    pass


# Registration of the LicensedState model in the admin site
@admin.register(LicensedState)
class LicensedStateAdmin(admin.ModelAdmin):
    pass
