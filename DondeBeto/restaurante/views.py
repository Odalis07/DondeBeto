from django.contrib.auth import authenticate, login
from django.contrib.auth.hashers import make_password
from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Usuario


def login_view(request):
    if request.method == "POST":
        # Recibimos los datos del formulario
        email = request.POST.get("email")
        contraseña = request.POST.get("contraseña")

        # Intentamos obtener al usuario con el email proporcionado
        try:
            usuario = Usuario.objects.get(email=email)

            # Verificamos si la contraseña es correcta
            if usuario.checkpassword(contraseña):  # Usamos checkpassword de tu modelo personalizado
                # Si la contraseña es correcta, establecemos manualmente la sesión
                request.session['usuario_id'] = usuario.id  # Guardamos el id de usuario en la sesión
                return redirect('vista_adm')  # Redirigir a la vista de administración
            else:
                messages.error(request, "Contraseña incorrecta.")
        except Usuario.DoesNotExist:
            messages.error(request, "El correo no está registrado.")

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
        pregunta_clave = request.POST.get('pregunta_clave')  # Obtener la pregunta de seguridad
        respuesta_clave = request.POST.get('respuesta_clave')  # Obtener la respuesta de seguridad

        # Crear un nuevo usuario
        usuario = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),  # Encriptar la contraseña
            rol=rol,
            pregunta_clave=pregunta_clave,  # Almacenar la pregunta clave
            respuesta_clave=respuesta_clave  # Almacenar la respuesta clave
        )

        # Guardar el usuario en la base de datos
        usuario.save()

        # Guardar el ID del usuario en la sesión para usarlo en el siguiente paso
        request.session['usuario_id'] = usuario.id

        # Mostrar mensaje de éxito
        messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')

        # Redirigir a la página de login
        return redirect('login')  # Redirigir a login después del registro

    return render(request, 'usuario/registro.html')  # Formulario de registro básico


def clave_olvidada(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        respuesta = request.POST.get('respuesta')

        try:
            # Buscar el usuario por correo electrónico
            usuario = Usuario.objects.get(email=email)

            # Verificar si la respuesta a la pregunta de seguridad es correcta
            if usuario.respuesta_clave == respuesta:
                # La respuesta es correcta, redirigir a la página de cambio de clave
                return redirect('clave_cambiada')  # Cambiar a la URL que maneja la vista clave_cambiada
            else:
                # Si la respuesta es incorrecta
                messages.error(request, 'La respuesta a la pregunta de seguridad es incorrecta.')
        except Usuario.DoesNotExist:
            # Si no se encuentra el usuario por correo
            messages.error(request, 'No se encuentra un usuario con ese correo electrónico.')

    return render(request, 'usuario/clave_olvidada.html')  # Aquí sería tu plantilla clave_olvidada.html

def clave_cambiada(request):
    return render(request, 'usuario/clave_cambiada.html')
def vista_adm(request):
    # Verificamos si el usuario está logueado
    if 'usuario_id' not in request.session:
        return redirect('login')  # Si no está logueado, redirigir al login

    # Si está logueado, continuar con la vista

    return render(request, 'adm/Vista_Adm.html')