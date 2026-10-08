from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum


class Cliente(models.Model):
    nombres = models.CharField(max_length=200)
    documento = models.CharField(max_length=20, unique=True, help_text="DNI o RUC del cliente")
    telefono = models.CharField(max_length=20)
    correo = models.EmailField()

    def __str__(self):
        return f"{self.nombres} ({self.documento})"


class EstadoCaso(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    permite_pagos = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre


class Caso(models.Model):
    codigo = models.CharField(max_length=20, unique=True)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    fecha_inicio = models.DateField()
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='casos')
    estado = models.ForeignKey(EstadoCaso, on_delete=models.PROTECT, related_name='casos')
    abogados = models.ManyToManyField(User, related_name='casos_asignados', blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"

    def total_pagado(self):
        resultado = self.pagos.aggregate(total=Sum('monto'))
        return resultado['total'] or 0


class Expediente(models.Model):
    numero = models.CharField(max_length=50, unique=True)
    juzgado = models.CharField(max_length=200)
    fecha_presentacion = models.DateField()
    documento = models.FileField(upload_to='expedientes/', blank=True, null=True)
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='expedientes')

    def __str__(self):
        return f"Exp. {self.numero} - {self.juzgado}"


class Pago(models.Model):
    caso = models.ForeignKey(Caso, on_delete=models.CASCADE, related_name='pagos')
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha = models.DateField()
    descripcion = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Pago {self.id} - {self.monto} ({self.caso.codigo})"

    def clean(self):
        if self.caso_id and not self.caso.estado.permite_pagos:
            raise ValidationError(
                f"No se puede registrar un pago porque el caso esta "
                f"en estado '{self.caso.estado.nombre}', "
                f"el cual no permite pagos."
            )


class PerfilAbogado(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil_abogado')
    numero_colegiatura = models.CharField(max_length=20, unique=True)
    especialidad = models.CharField(max_length=100)

    def __str__(self):
        return f"Abg. {self.usuario.get_full_name() or self.usuario.username} - {self.especialidad}"
