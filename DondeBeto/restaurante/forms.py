from django import forms
from django.contrib.auth.hashers import make_password

from DondeBeto.restaurante.models import Usuario


class RegistroForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'apellido', 'email', 'contraseña', 'rol']

    def clean_contraseña(self):
        # Asegúrate de encriptar la contraseña antes de guardarla
        password = self.cleaned_data.get('contraseña')
        return make_password(password)

