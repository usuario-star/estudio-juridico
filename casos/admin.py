from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Cliente, EstadoCaso, Caso, Expediente, Pago, PerfilAbogado


class PerfilAbogadoInline(admin.StackedInline):
    model = PerfilAbogado
    can_delete = False
    verbose_name_plural = 'Perfil de Abogado'
    max_num = 1


class CustomUserAdmin(UserAdmin):
    inlines = [PerfilAbogadoInline]


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombres', 'documento', 'telefono', 'correo')
    search_fields = ('nombres', 'documento', 'correo')
    list_filter = ()


@admin.register(EstadoCaso)
class EstadoCasoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'permite_pagos')
    search_fields = ('nombre',)
    list_filter = ('permite_pagos',)


class ExpedienteInline(admin.TabularInline):
    model = Expediente
    extra = 1
    fields = ('numero', 'juzgado', 'fecha_presentacion')


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 1
    fields = ('monto', 'fecha', 'descripcion')


@admin.register(Caso)
class CasoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'titulo', 'cliente', 'estado', 'total_pagado_display', 'fecha_inicio')
    search_fields = ('codigo', 'titulo', 'cliente__nombres', 'descripcion')
    list_filter = ('estado', 'fecha_inicio')
    filter_horizontal = ('abogados',)
    inlines = [ExpedienteInline, PagoInline]

    def total_pagado_display(self, obj):
        return f'S/ {obj.total_pagado():.2f}'

    total_pagado_display.short_description = 'Total Pagado'


@admin.register(Expediente)
class ExpedienteAdmin(admin.ModelAdmin):
    list_display = ('numero', 'juzgado', 'fecha_presentacion', 'caso')
    search_fields = ('numero', 'juzgado', 'caso__codigo')
    list_filter = ('juzgado', 'fecha_presentacion')
