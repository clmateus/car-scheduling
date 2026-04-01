from django.contrib import admin
from .models import Veiculo, Agendamento


class ListarAgendamentos(admin.ModelAdmin):
    list_display = ("id", "motorista", "dataPartida", "dataChegada", "destino",)
    list_display_links = ("id", "motorista", )
    search_fields = ("motorista",)

admin.site.register(Veiculo)
admin.site.register(Agendamento, ListarAgendamentos)