from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
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
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, 'No se encuentra un usuario con ese correo electrónico.')
            return render(request, 'usuario/clave_olvidada.html')

        # Si el usuario ya está respondiendo la pregunta
        if respuesta:
            if usuario.respuesta_clave.strip().lower() == respuesta.strip().lower():
                # Redirigir si la respuesta es correcta
                return redirect('clave_cambiada')

            else:
                messages.error(request, 'La respuesta a la pregunta de seguridad es incorrecta.')
                # Volver a mostrar la pregunta
                return render(request, 'usuario/clave_olvidada.html', {
                    'email': email,
                    'pregunta_clave': usuario.pregunta_clave,
                })

        # Si solo se envió el email, mostrar la pregunta
        else:
            return render(request, 'usuario/clave_olvidada.html', {
                'email': email,
                'pregunta_clave': usuario.pregunta_clave,
            })

    # Si es GET
    return render(request, 'usuario/clave_olvidada.html')

def clave_cambiada(request):
    return render(request, 'usuario/clave_cambiada.html')
def vista_adm(request):

    usuario_id = request.session.get('usuario_id')

    if usuario_id:
        try:

            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            usuario = None
    else:
        usuario = None

    return render(request, 'adm/Vista_Adm.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})


def usuarios_view(request):
    # Obtener el rol seleccionado desde la URL (por ejemplo, 'Todos', 'cajero', etc.)
    rol_seleccionado = request.GET.get('rol', 'Todos').lower()  # Convertir siempre a minúsculas

    if rol_seleccionado == 'todos':
        # Excluir el rol 'cliente' para que no aparezca en la vista "Todos"
        usuarios = Usuario.objects.exclude(rol='cliente')  # Excluimos 'cliente' en minúsculas
    elif rol_seleccionado in ['cajero', 'mesero', 'repartidor', 'administrador']:
        # Filtramos según el rol seleccionado en minúsculas
        usuarios = Usuario.objects.filter(rol=rol_seleccionado)
    else:
        # Si no se pasa un rol válido, mostramos todos los usuarios
        usuarios = Usuario.objects.all()

    # Obtener el usuario actual (opcional)
    usuario_id = request.session.get('usuario_id')
    if usuario_id:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            usuario = None
    else:
        usuario = None

    # Pasamos los usuarios y el rol seleccionado a la plantilla
    return render(request, 'adm/Usuarios.html', {'usuario': usuario, 'usuarios': usuarios, 'rol_seleccionado': rol_seleccionado})






def clientes_view(request):
    usuario_id = request.session.get('usuario_id')

    # Verificamos si hay un usuario en la sesión
    if usuario_id:
        try:
            usuario = Usuario.objects.get(id=usuario_id)  # El usuario logueado
        except Usuario.DoesNotExist:
            usuario = None
    else:
        usuario = None

    # Filtrar los usuarios con el rol 'cliente'
    clientes = Usuario.objects.filter(rol='cliente')

    # Pasar a la plantilla
    return render(request, 'adm/clientes.html', {'usuario': usuario, 'clientes': clientes})



def lista_clientes(request):
    # Filtramos solo los usuarios con rol 'cliente'
    clientes = Usuario.objects.filter(rol='cliente')  # Asegúrate que los clientes tienen rol 'cliente'
    return render(request, 'Clientes.html', {'clientes': clientes})