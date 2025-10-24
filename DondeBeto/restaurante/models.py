from django.db import models
from datetime import date
from django.contrib.auth.hashers import make_password, check_password


# Modelo de PreguntaClave
class PreguntaClave(models.Model):
    pregunta = models.CharField(max_length=255, unique=True, null=False, blank=False)
    respuesta = models.CharField(max_length=255, null=False, blank=False)

    class Meta:
        db_table = "pregunta_clave"
        verbose_name = "Pregunta Clave"
        verbose_name_plural = "Preguntas Clave"

    def __str__(self):
        return self.pregunta


# Modelo de Usuario con relación a PreguntaClave
class Usuario(models.Model):
    cedula = models.CharField(max_length=10, unique=True, null=False, blank=False)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apellido = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    contraseña = models.CharField(max_length=128, null=False, blank=False)
    rol = models.CharField(default='usuario', max_length=20)

    # Relación con PreguntaClave
    pregunta_clave = models.ForeignKey(PreguntaClave, on_delete=models.SET_NULL, null=True, blank=True)

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
