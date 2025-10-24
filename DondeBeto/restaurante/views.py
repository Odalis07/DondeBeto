from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistroForm, PreguntaClaveForm
from .models import Usuario, PreguntaClave


def login_view(request):
    return render(request, 'usuario/login.html')


# Vista para manejar el registro de usuario
def registro_view(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol')

        # Crear un nuevo usuario
        usuario = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),  # Encriptar la contraseña
            rol=rol
        )

        # Guardar el usuario en la base de datos
        usuario.save()

        # Guardar el ID del usuario en la sesión para usarlo en el siguiente paso
        request.session['usuario_id'] = usuario.id

        # Mostrar mensaje de éxito
        messages.success(request, '¡Registro exitoso! Ahora puedes configurar tu pregunta de seguridad.')

        # Redirigir a la página del segundo paso (registro_2)
        return redirect('registro_2')  # Asegúrate de tener configurada la URL 'registro_2'

    return render(request, 'usuario/registro.html')  # Formulario de registro básico


def registro_2_view(request):
    if request.method == 'POST':
        form = PreguntaClaveForm(request.POST)
        if form.is_valid():
            # Recuperar el ID del usuario desde la sesión
            usuario_id = request.session.get('usuario_id')
            if not usuario_id:
                return redirect('registro')  # Redirigir al primer paso si no hay ID de usuario en sesión

            # Obtener el usuario usando el ID
            usuario = Usuario.objects.get(id=usuario_id)

            # Obtener la pregunta de seguridad y la respuesta del formulario
            pregunta = form.cleaned_data['pregunta_clave']
            respuesta = form.cleaned_data['respuesta']

            # Crear una nueva entrada en la tabla PreguntaClave con la respuesta
            pregunta_respuesta = PreguntaClave.objects.create(
                pregunta=pregunta.pregunta,
                respuesta=respuesta
            )

            # Asociar la pregunta clave con el usuario
            usuario.pregunta_clave = pregunta_respuesta  # Usamos la instancia completa, no solo el texto de la pregunta
            usuario.save()

            # Limpiar la sesión después de completar el registro
            del request.session['usuario_id']

            # Redirigir al login o a una página de éxito
            return redirect('login')  # O redirigir a una página de éxito

    else:
        form = PreguntaClaveForm()

    return render(request, 'usuario/registro_dos.html', {'form': form})


def claveOlvidada_view(request):
    return render(request, 'usuario/clave_olvidada.html')


def clave_cambiada(request):
    return render(request, 'usuario/clave_cambiada.html')
