from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Usuario


# ---------------------------
# LOGIN VIEW
# ---------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        contraseña = request.POST.get("contraseña")

        try:
            # Buscar usuario por correo
            usuario = Usuario.objects.get(email=email)

            # Verificar contraseña
            if usuario.checkpassword(contraseña):
                # Guardar el ID en sesión
                request.session['usuario_id'] = usuario.id

                # Redirección según el rol
                rol = usuario.rol.strip().lower()

                if rol == "administrador":
                    return redirect('vista_adm')
                elif rol == "cliente":
                    return redirect('home_cliente')
                elif rol == "cajero":
                    return redirect('vista_cajero')
                elif rol == "mesero":
                    return redirect('vista_mesero')
                elif rol == "repartidor":
                    return redirect('vista_repartidor')
                else:
                    messages.error(request, "Rol de usuario no reconocido.")
            else:
                messages.error(request, "Contraseña incorrecta.")
        except Usuario.DoesNotExist:
            messages.error(request, "El correo no está registrado.")

    # Si no es POST o hay error, mostrar login
    return render(request, 'Login/login.html')

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

    return render(request, 'Login/registro.html')  # Formulario de registro básico


def clave_olvidada(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        respuesta = request.POST.get('respuesta')

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, 'No se encuentra un usuario con ese correo electrónico.')
            return render(request, 'Login/clave_olvidada.html')

        # Si el usuario ya está respondiendo la pregunta
        if respuesta:
            if usuario.respuesta_clave.strip().lower() == respuesta.strip().lower():
                # Redirigir si la respuesta es correcta
                return redirect('clave_cambiada')

            else:
                messages.error(request, 'La respuesta a la pregunta de seguridad es incorrecta.')
                # Volver a mostrar la pregunta
                return render(request, 'Login/clave_olvidada.html', {
                    'email': email,
                    'pregunta_clave': usuario.pregunta_clave,
                })

        # Si solo se envió el email, mostrar la pregunta
        else:
            return render(request, 'Login/clave_olvidada.html', {
                'email': email,
                'pregunta_clave': usuario.pregunta_clave,
            })

    # Si es GET
    return render(request, 'Login/clave_olvidada.html')

def clave_cambiada(request):
    return render(request, 'Login/clave_cambiada.html')

# ---------------------------
# ADMINISTRADOR VIEW
# ---------------------------

def vista_adm(request):

    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_Adm/Vista_Adm.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})


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
    return render(request, 'Vista_Adm/Usuarios.html', {'usuario': usuario, 'usuarios': usuarios, 'rol_seleccionado': rol_seleccionado,'rol': usuario.rol if usuario else None})


# Vista para registrar un trabajador
def registrar_usuario_view(request):
    if request.method == 'POST':
        # Obtener datos del formulario
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol').lower()  # Convertimos a minúsculas
        pregunta_clave = request.POST.get('pregunta_clave')
        respuesta_clave = request.POST.get('respuesta_clave')

        # Validar que el rol sea uno de los válidos para trabajadores
        roles_validos = ['cajero', 'mesero', 'repartidor', 'administrador']
        if rol not in roles_validos:
            messages.error(request, 'Rol no válido para trabajadores.')
            return redirect('usuarios')  # Redirige de nuevo a la lista de usuarios

        # Validar que la cédula no exista (ya que es unique)
        if Usuario.objects.filter(cedula=cedula).exists():
            messages.error(request, 'Ya existe un usuario con esa cédula.')
            return redirect('usuarios')

        # Crear nuevo usuario
        usuario = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),  # Encriptar contraseña
            rol=rol,
            pregunta_clave=pregunta_clave,
            respuesta_clave=respuesta_clave
        )
        usuario.save()

        messages.success(request, f'Trabajador {nombre} {apellido} registrado correctamente.')
        return redirect('usuarios')  # Redirige de nuevo a la lista de usuarios

    # Si no es POST, redirigir a la lista de usuarios
    return redirect('usuarios')



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
    return render(request, 'Vista_Adm/Clientes.html', {'usuario': usuario, 'clientes': clientes,'rol': usuario.rol if usuario else None})

# Vista para registrar nuevos clientes
def registrar_cliente_view(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        pregunta_clave = request.POST.get('pregunta_clave')
        respuesta_clave = request.POST.get('respuesta_clave')

        # Crear un nuevo cliente (rol fijo: cliente)
        cliente = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),
            rol='cliente',
            pregunta_clave=pregunta_clave,
            respuesta_clave=respuesta_clave
        )

        cliente.save()
        messages.success(request, '¡Cliente registrado exitosamente!')

        # Redirigir de vuelta a la lista de clientes
        return redirect('clientes')

    # Si es GET, simplemente recargar la página de clientes
    return redirect('clientes')

def lista_clientes(request):
    # Filtramos solo los usuarios con rol 'cliente'
    clientes = Usuario.objects.filter(rol='cliente')  # Asegúrate que los clientes tienen rol 'cliente'
    return render(request, 'Clientes.html', {'clientes': clientes})

def home_cliente(request):
    # Verificamos si hay sesión activa
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Opcional: obtener datos del usuario
    usuario = Usuario.objects.get(id=usuario_id)
    contexto = {'usuario': usuario}

    return render(request, 'Vista_cliente/homeCliente.html', contexto)

def ubicacion(request):
    # Verificamos si hay sesión activa
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Opcional: obtener datos del usuario
    usuario = Usuario.objects.get(id=usuario_id)
    contexto = {'usuario': usuario}
    return render(request, 'Vista_cliente/ubicacion.html', contexto)

def sobre_nosotros(request):
    # Verificamos si hay sesión activa
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Opcional: obtener datos del usuario
    usuario = Usuario.objects.get(id=usuario_id)
    contexto = {'usuario': usuario}
    return render(request, 'Vista_cliente/Nosotros.html', contexto)


def mi_perfil(request):
    # Suponiendo que guardas el usuario en sesión
    user_id = request.session.get('usuario_id')  # adapta según tu login
    if not user_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=user_id)

    context = {
        'usuario': usuario
    }
    return render(request, 'Vista_cliente/perfil.html', context)
#VISTAS ACTORES
def vista_cajero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_cajero/Vista_Cajero.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})





def vista_mesero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_mesero/Vista_Mesero.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})

def vista_repartidor(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_repartidor/Vista_Repartidor.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})

# ---------------------------
# VISTAS DE PERFIL POR ROL
# ---------------------------
def perfil_cajero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_cajero/perfil_cajero.html', {'usuario': usuario, 'rol': usuario.rol})


def perfil_mesero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_mesero/perfil_mesero.html', {'usuario': usuario, 'rol': usuario.rol})


def perfil_repartidor(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vista_repartidor/perfil_repartidor.html', {'usuario': usuario, 'rol': usuario.rol})

@csrf_exempt
def actualizar_cliente(request, id):
    """Recibe datos JSON y actualiza el cliente"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            cliente = get_object_or_404(Usuario, id=id)

            cliente.cedula = data.get('cedula', cliente.cedula)
            cliente.nombre = data.get('nombre', cliente.nombre)
            cliente.apellido = data.get('apellido', cliente.apellido)
            cliente.email = data.get('email', cliente.email)
            cliente.rol = data.get('rol', cliente.rol)
            cliente.pregunta_clave = data.get('pregunta_clave', cliente.pregunta_clave)
            cliente.respuesta_clave = data.get('respuesta_clave', cliente.respuesta_clave)

            if 'contraseña' in data and data['contraseña']:
                cliente.setpassword(data['contraseña'])

            cliente.save()

            return JsonResponse({'success': True, 'message': 'Cliente actualizado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def eliminar_cliente(request, id):
    """Elimina un cliente por ID"""
    if request.method == 'POST':
        try:
            cliente = get_object_or_404(Usuario, id=id)
            cliente.delete()
            return JsonResponse({'success': True, 'message': 'Cliente eliminado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})