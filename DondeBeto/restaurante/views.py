from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Usuario, Producto, Categoria, Mesa


# ---------------------------
# LOGIN VIEW
# ---------------------------
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        contraseña = request.POST.get("contraseña")

        try:
            usuario = Usuario.objects.get(email=email)
            if usuario.checkpassword(contraseña):
                request.session['usuario_id'] = usuario.id
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

    return render(request, 'Login/login.html')


def registro_view(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol')
        pregunta_clave = request.POST.get('pregunta_clave')
        respuesta_clave = request.POST.get('respuesta_clave')

        usuario = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),
            rol=rol,
            pregunta_clave=pregunta_clave,
            respuesta_clave=respuesta_clave
        )
        usuario.save()
        request.session['usuario_id'] = usuario.id
        messages.success(request, '¡Registro exitoso! Ahora puedes iniciar sesión.')
        return redirect('login')

    return render(request, 'Login/registro.html')


def clave_olvidada(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        respuesta = request.POST.get('respuesta')

        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            messages.error(request, 'No se encuentra un usuario con ese correo electrónico.')
            return render(request, 'Login/clave_olvidada.html')

        if respuesta:
            if usuario.respuesta_clave.strip().lower() == respuesta.strip().lower():
                return redirect('clave_cambiada')
            else:
                messages.error(request, 'La respuesta a la pregunta de seguridad es incorrecta.')
                return render(request, 'Login/clave_olvidada.html', {
                    'email': email,
                    'pregunta_clave': usuario.pregunta_clave,
                })
        else:
            return render(request, 'Login/clave_olvidada.html', {
                'email': email,
                'pregunta_clave': usuario.pregunta_clave,
            })

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

    return render(request, 'Vista_Adm/Vista_Adm.html', {'usuario': usuario, 'rol': usuario.rol if usuario else None})


def usuarios_view(request):
    rol_seleccionado = request.GET.get('rol', 'Todos').lower()
    if rol_seleccionado == 'todos':
        usuarios = Usuario.objects.exclude(rol='cliente')
    elif rol_seleccionado in ['cajero', 'mesero', 'repartidor', 'administrador']:
        usuarios = Usuario.objects.filter(rol=rol_seleccionado)
    else:
        usuarios = Usuario.objects.all()

    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.filter(id=usuario_id).first() if usuario_id else None

    return render(request, 'Vista_Adm/Usuarios.html', {
        'usuario': usuario,
        'usuarios': usuarios,
        'rol_seleccionado': rol_seleccionado,
        'rol': usuario.rol if usuario else None
    })


def registrar_usuario_view(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        rol = request.POST.get('rol').lower()
        pregunta_clave = request.POST.get('pregunta_clave')
        respuesta_clave = request.POST.get('respuesta_clave')

        roles_validos = ['cajero', 'mesero', 'repartidor', 'administrador']
        if rol not in roles_validos:
            messages.error(request, 'Rol no válido para trabajadores.')
            return redirect('usuarios')

        if Usuario.objects.filter(cedula=cedula).exists():
            messages.error(request, 'Ya existe un usuario con esa cédula.')
            return redirect('usuarios')

        usuario = Usuario(
            cedula=cedula,
            nombre=nombre,
            apellido=apellido,
            email=email,
            contraseña=make_password(password),
            rol=rol,
            pregunta_clave=pregunta_clave,
            respuesta_clave=respuesta_clave
        )
        usuario.save()
        messages.success(request, f'Trabajador {nombre} {apellido} registrado correctamente.')
        return redirect('usuarios')

    return redirect('usuarios')


def clientes_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.filter(id=usuario_id).first() if usuario_id else None
    clientes = Usuario.objects.filter(rol='cliente')
    return render(request, 'Vista_Adm/Clientes.html', {'usuario': usuario, 'clientes': clientes, 'rol': usuario.rol if usuario else None})


def registrar_cliente_view(request):
    if request.method == 'POST':
        cedula = request.POST.get('cedula')
        nombre = request.POST.get('nombre')
        apellido = request.POST.get('apellido')
        email = request.POST.get('email')
        password = request.POST.get('password')
        pregunta_clave = request.POST.get('pregunta_clave')
        respuesta_clave = request.POST.get('respuesta_clave')

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
        return redirect('clientes')

    return redirect('clientes')


# ---------------------------
# CLIENTE Y OTRAS VISTAS
# ---------------------------
def home_cliente(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_cliente/homeCliente.html', {'usuario': usuario})


def ubicacion(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_cliente/ubicacion.html', {'usuario': usuario})


def sobre_nosotros(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_cliente/Nosotros.html', {'usuario': usuario})


def mi_perfil(request):
    user_id = request.session.get('usuario_id')
    if not user_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=user_id)
    return render(request, 'Vista_cliente/perfil.html', {'usuario': usuario})


# ---------------------------
# VISTAS POR ROL
# ---------------------------
def vista_cajero(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_cajero/Vista_Cajero.html', {'usuario': usuario, 'rol': usuario.rol})


def vista_mesero(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_mesero/Vista_Mesero.html', {'usuario': usuario, 'rol': usuario.rol})


def vista_repartidor(request):
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')
    usuario = Usuario.objects.get(id=usuario_id)
    return render(request, 'Vista_repartidor/Vista_Repartidor.html', {'usuario': usuario, 'rol': usuario.rol})


# ---------------------------
# MESAS
# ---------------------------
def mesas_view(request):
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.filter(id=usuario_id).first() if usuario_id else None

    estado = request.GET.get('estado')
    if estado in ['disponible', 'ocupada', 'reservada']:
        mesas = Mesa.objects.filter(estado=estado)
    else:
        mesas = Mesa.objects.all()

    context = {
        'usuario': usuario,
        'rol': usuario.rol if usuario else None,
        'mesas': mesas,
        'estado_filtro': estado
    }
    return render(request, 'Vista_adm/Mesas.html', context)


def registrar_mesa_view(request):
    if request.method == 'POST':
        numero = request.POST.get('numero')
        capacidad = request.POST.get('capacidad')
        estado = request.POST.get('estado')
        Mesa.objects.create(numero=numero, capacidad=capacidad, estado=estado)
        messages.success(request, '¡Mesa registrada exitosamente!')
    return redirect('mesas')
