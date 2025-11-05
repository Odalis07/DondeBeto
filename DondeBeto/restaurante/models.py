from django.db import models
from django.contrib.auth.hashers import make_password, check_password


class Usuario(models.Model):
    cedula = models.CharField(max_length=10, null=False, blank=False)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apellido = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    contraseña = models.CharField(max_length=128, null=False, blank=False)
    rol = models.CharField(default='usuario', max_length=20)

    # Campos de seguridad
    pregunta_clave = models.CharField(max_length=255, null=True, blank=True)
    respuesta_clave = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "usuario"
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def setpassword(self, raw_password):
        self.contraseña = make_password(raw_password)

    def checkpassword(self, raw_password):
        return check_password(raw_password, self.contraseña)


class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(
        max_length=20,
        choices=[
            ('disponible', 'Disponible'),
            ('ocupada', 'Ocupada'),
            ('reservada', 'Reservada'),
        ]
    )

    class Meta:
        db_table = "mesa"
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"

    def __str__(self):
        return f"Mesa {self.numero} ({self.estado})"
