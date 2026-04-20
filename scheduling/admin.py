from django.contrib import admin
from .models import *
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

class ListarAgendamentos(admin.ModelAdmin):
    list_display = ("id", "motorista", "dataPartida", "dataChegada", "destino")
    list_display_links = ("id", "motorista")
    search_fields = ("motorista",)

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil'

class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Veiculo)
admin.site.register(Agendamento, ListarAgendamentos)
admin.site.register(Seguro)
admin.site.register(Info)
admin.site.register(Ativo)
admin.site.register(SolicitacaoAtivo)