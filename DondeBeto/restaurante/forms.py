from django import forms
from django.contrib.auth.hashers import make_password

from .models import Usuario, PreguntaClave


class RegistroForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['cedula', 'nombre', 'apellido', 'email', 'contraseña', 'rol']

    def clean_contraseña(self):
        # Asegúrate de encriptar la contraseña antes de guardarla
        password = self.cleaned_data.get('contraseña')
        return make_password(password)


class PreguntaClaveForm(forms.Form):
    # Este campo es para seleccionar la pregunta
    pregunta_clave = forms.ModelChoiceField(queryset=PreguntaClave.objects.all(), empty_label="Selecciona una pregunta",
                                            required=True)

    # Este campo es para que el usuario ingrese la respuesta
    respuesta = forms.CharField(max_length=255, required=True)