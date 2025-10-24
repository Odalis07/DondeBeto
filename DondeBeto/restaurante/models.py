from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Modelo de Usuario con pregunta y respuesta clave directamente en la misma tabla
class Usuario(models.Model):
    cedula = models.CharField(max_length=10, unique=True, null=False, blank=False)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apellido = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    contraseña = models.CharField(max_length=128, null=False, blank=False)
    rol = models.CharField(default='usuario', max_length=20)

    # Campos para la pregunta y respuesta de seguridad
    pregunta_clave = models.CharField(max_length=255, null=True, blank=True)  # Pregunta de seguridad
    respuesta_clave = models.CharField(max_length=255, null=True, blank=True)  # Respuesta de seguridad

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
