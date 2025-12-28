from decimal import Decimal

from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views.decorators.csrf import csrf_exempt
import json
from io import BytesIO
from .factory import PedidoFactory
from .models import Usuario, Producto, Categoria, Mesa, Pedido, DetallePedido, Pago
from restaurante.repositories.producto_repository import ProductoRepository
from restaurante.models import Categoria
#para stripe
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404, render

stripe.api_key = settings.STRIPE_SECRET_KEY

# ---------------------------
# COMPONENTE 1 - Usuario
# ---------------------------
# ---------------------------
# VISTA DE USUARIO
# ---------------------------

#Vista del login
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
                request.session['rol'] = usuario.rol
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
    return render(request, 'C1_Usuario/login.html')

# Vista registro de usuario
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

    return render(request, 'C1_Usuario/registro.html')  # Formulario de registro básico

# Vista clave olvidada de usuario
def clave_olvidada(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        respuesta = request.POST.get('respuesta')

        try:
            usuario = Usuario.objects.get(email=email)
            # Guardamos el correo en la sesión
            request.session['email_recuperacion'] = email
        except Usuario.DoesNotExist:
            messages.error(request, 'No se encuentra un usuario con ese correo electrónico.')
            return render(request, 'C1_Usuario/clave_olvidada.html')

        # Si el usuario ya está respondiendo la pregunta
        if respuesta:
            if usuario.respuesta_clave.strip().lower() == respuesta.strip().lower():
                # Redirigir si la respuesta es correcta
                return redirect('clave_cambiada')

            else:
                messages.error(request, 'La respuesta a la pregunta de seguridad es incorrecta.')
                # Volver a mostrar la pregunta
                return render(request, 'C1_Usuario/clave_olvidada.html', {
                    'email': email,
                    'pregunta_clave': usuario.pregunta_clave,
                })

        # Si solo se envió el email, mostrar la pregunta
        else:
            return render(request, 'C1_Usuario/clave_olvidada.html', {
                'email': email,
                'pregunta_clave': usuario.pregunta_clave,
            })

    # Si es GET
    return render(request, 'C1_Usuario/clave_olvidada.html')


# Vista cambio de contraseña

def clave_cambiada(request):
    if request.method == 'POST':
        nueva_clave = request.POST.get('new-password')
        repetir_clave = request.POST.get('password-repeat')
        email = request.session.get('email_recuperacion')

        if not email:
            messages.error(request, "No se encontró el correo del usuario.")
            return redirect('Clave_Olvidada')

        if not nueva_clave or not repetir_clave:
            messages.error(request, "Completa todos los campos.")
            return redirect('clave_cambiada')

        if nueva_clave != repetir_clave:
            messages.error(request, "Las contraseñas no coinciden.")
            return redirect('clave_cambiada')

        try:
            usuario = Usuario.objects.get(email=email)
            usuario.contraseña = make_password(nueva_clave)
            usuario.save()

            # Borrar el email guardado
            del request.session['email_recuperacion']

            # Enviar mensaje de éxito que se mostrará con alert JS
            messages.success(request, "Tu contraseña se cambió correctamente.")
            return redirect('login')

        except Usuario.DoesNotExist:
            messages.error(request, "Usuario no encontrado.")
            return redirect('clave_olvidada')

    return render(request, 'C1_Usuario/clave_cambiada.html')

# ---------------------------
# VITAS
# ---------------------------
# ---------------------------
# ADMINISTRADOR - VISTA
# ---------------------------

def vista_adm(request):

    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_Adm/Vista_Adm.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})


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
    return render(request, 'Vistas/Vista_Adm/Usuarios.html', {'usuario': usuario, 'usuarios': usuarios, 'rol_seleccionado': rol_seleccionado,'rol': usuario.rol if usuario else None})


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

#vista de los clientes del sistema, esto lo vera el administrador

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
    return render(request, 'Vistas/Vista_Adm/Clientes.html', {'usuario': usuario, 'clientes': clientes,'rol': usuario.rol if usuario else None})

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

# ---------------------------
# CLIENTE - VISTA
# ---------------------------
def home_cliente(request):
    categoria_seleccionada = request.GET.get('categoria', 'Todos')
    productos = Producto.objects.all()
    usuario_id = request.session.get('usuario_id')
    usuario = Usuario.objects.get(id=usuario_id)
    if categoria_seleccionada != 'Todos':
        productos = productos.filter(categoria__nombre=categoria_seleccionada)

    context = {
        'productos': productos,
        'categoria_seleccionada': categoria_seleccionada,
        'usuario': usuario,
    }

    return render(request, 'Vistas/Vista_cliente/homeCliente.html', context)

def ubicacion(request):
    # Verificamos si hay sesión activa
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Opcional: obtener datos del usuario
    usuario = Usuario.objects.get(id=usuario_id)
    contexto = {'usuario': usuario}
    return render(request, 'Vistas/Vista_cliente/ubicacion.html', contexto)

def sobre_nosotros(request):
    # Verificamos si hay sesión activa
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    # Opcional: obtener datos del usuario
    usuario = Usuario.objects.get(id=usuario_id)
    contexto = {'usuario': usuario}
    return render(request, 'Vistas/Vista_cliente/Nosotros.html', contexto)


def mi_perfil(request):
    # Suponiendo que guardas el usuario en sesión
    user_id = request.session.get('usuario_id')  # adapta según tu login
    if not user_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=user_id)

    context = {
        'usuario': usuario
    }
    return render(request, 'Vistas/Vista_cliente/perfil.html', context)

# ---------------------------
# CAJERO - VISTA
# ---------------------------
def vista_cajero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_cajero/Vista_Cajero.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})

def perfil_cajero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_cajero/perfil_cajero.html', {'usuario': usuario, 'rol': usuario.rol})


# ---------------------------
# MESERO - VISTA
# ---------------------------


def vista_mesero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_mesero/Vista_Mesero.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})

def perfil_mesero(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_mesero/perfil_mesero.html', {'usuario': usuario, 'rol': usuario.rol})

# ---------------------------
# REPARTIDOR - VISTA
# ---------------------------

def vista_repartidor(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_repartidor/Vista_Repartidor.html',{'usuario': usuario, 'rol': usuario.rol if usuario else None})


def perfil_repartidor(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    return render(request, 'Vistas/Vista_repartidor/perfil_repartidor.html', {'usuario': usuario, 'rol': usuario.rol})

#
# ---------------------------
# ACTUALIZAR CLIENTE METODO
# ---------------------------
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

# ---------------------------
# ELIMINAR CLIENTE METODO
# ---------------------------
@csrf_exempt
def eliminar_cliente(request, id):
    """Elimina un cliente por ID"""
    if request.method == 'POST':
        tiene_pedidos = Pedido.objects.filter(usuario_id=id).exists()
        if tiene_pedidos:
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar el usuario porque está relacionado con uno o más pedidos'
            })
        try:
            cliente = get_object_or_404(Usuario, id=id)
            cliente.delete()
            return JsonResponse({'success': True, 'message': 'Cliente eliminado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ---------------------------
# COMPONENTE 2 - PEDIDOS
# ---------------------------
# ---------------------------
# PRODUCTOS - VISTA
# ---------------------------
def productos(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    # 🔹 Obtener categoría desde la URL (GET)
    categoria_seleccionada = request.GET.get('categoria', 'Todos')

    categorias = Categoria.objects.all()

    # 🔹 Filtrar productos según categoría
    if categoria_seleccionada == 'Todos':
        productos = Producto.objects.all()
    else:
        productos = Producto.objects.filter(categoria__nombre=categoria_seleccionada)

    return render(request, 'C2_Pedido/Productos.html', {
        'usuario': usuario,
        'rol': usuario.rol,
        'productos': productos,
        'categorias': categorias,
        'categoria_seleccionada': categoria_seleccionada
    })


def registrar_producto(request):
    if request.method == 'POST':
        nombre = request.POST['nombre']
        descripcion = request.POST['descripcion']
        precio = request.POST['precio']
        categoria = Categoria.objects.get(id=request.POST['categoria'])
        imagen = request.FILES.get('imagen')

        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            categoria=categoria,
            imagen=imagen
        )
        return redirect('productos')

@csrf_exempt


#SE USA REPOSITORY AQUI:

def actualizar_producto(request, id):
    """Recibe datos JSON y actualiza un producto"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            producto = get_object_or_404(Producto, id=id)

            producto.nombre = data.get('nombre', producto.nombre)
            producto.descripcion = data.get('descripcion', producto.descripcion)
            producto.precio = data.get('precio', producto.precio)
            producto.categoria_id = data.get('categoria_id', producto.categoria_id)

            # Si manejas imagenes via MEDIA
            if 'imagen' in data and data['imagen']:
                producto.imagen = data['imagen']  # Asegúrate de que sea la ruta correcta

            producto.save()
            return JsonResponse({'success': True, 'message': 'Producto actualizado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def eliminar_producto(request, id):
    """Elimina un producto por ID"""
    if request.method == 'POST':
        tiene_pedidos = DetallePedido.objects.filter(producto=id).exists()
        if tiene_pedidos:
            return JsonResponse({
                'success': False,
                'error': 'No se puede eliminar el producto porque está relacionado con uno o más pedidos'
            })

        try:
            producto = get_object_or_404(Producto, id=id)
            producto.delete()
            return JsonResponse({'success': True, 'message': 'Producto eliminado correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ---------------------------
# MESAS - VISTA
# ---------------------------
def mesas_view(request):
    usuario_id = request.session.get('usuario_id')

    # Verificamos si hay un usuario en la sesión
    usuario = None
    if usuario_id:
        try:
            usuario = Usuario.objects.get(id=usuario_id)
        except Usuario.DoesNotExist:
            usuario = None

    # Obtener parámetro de filtro de estado desde la URL (?estado=ocupada)
    estado = request.GET.get('estado')  # 'disponible', 'ocupada', 'reservada', o None

    # Filtrar mesas según estado si aplica
    if estado in ['disponible', 'ocupada', 'reservada']:
        mesas = Mesa.objects.filter(estado=estado)
    else:
        mesas = Mesa.objects.all()

    context = {
        'usuario': usuario,
        'rol': usuario.rol if usuario else None,
        'mesas': mesas,
        'estado_filtro': estado  # para marcar tab activo
    }

    return render(request, 'C2_Pedido/Mesas.html', context)


# Vista para registrar nuevas mesas
def registrar_mesa_view(request):
    if request.method == 'POST':
        # Obtener los datos del formulario
        numero = request.POST.get('numero')
        capacidad = request.POST.get('capacidad')
        estado = request.POST.get('estado')

        # Crear una nueva mesa
        mesa = Mesa(
            numero=numero,
            capacidad=capacidad,
            estado=estado
        )
        mesa.save()

        messages.success(request, '¡Mesa registrada exitosamente!')
        return redirect('mesas')

    return redirect('mesas')

@csrf_exempt
def actualizar_mesa(request, id):
    """Recibe datos JSON y actualiza una mesa"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mesa = get_object_or_404(Mesa, id=id)

            mesa.numero = data.get('numero', mesa.numero)
            mesa.capacidad = data.get('capacidad', mesa.capacidad)
            mesa.estado = data.get('estado', mesa.estado)

            mesa.save()
            return JsonResponse({'success': True, 'message': 'Mesa actualizada correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@csrf_exempt
def eliminar_mesa(request, id):
    """Elimina una mesa por ID"""
    if request.method == 'POST':
        try:
            mesa = get_object_or_404(Mesa, id=id)
            mesa.delete()
            return JsonResponse({'success': True, 'message': 'Mesa eliminada correctamente'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Método no permitido'})


# ---------------------------
# PEDIDOS - VISTA
# ---------------------------
def pedidos(request):
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    try:
        usuario = Usuario.objects.get(id=usuario_id)
    except Usuario.DoesNotExist:
        return redirect('login')

    # Valor que viene en la URL (ej: "En el local", "Domicilio", "Para llevar", o "Todos")
    tipo_pedido_param = request.GET.get('tipo_pedido', 'Todos')

    # Mapeo etiqueta -> codigo interno de la DB
    etiqueta_a_codigo = {
        'En el local': 'local',
        'Domicilio': 'domicilio',
        'Para llevar': 'para_llevar',
        # También soportamos las claves internas si alguien las pasa directamente
        'local': 'local',
        'domicilio': 'domicilio',
        'para_llevar': 'para_llevar',
        'Todos': 'Todos'
    }

    # Determinar código a usar en el filtro
    codigo = etiqueta_a_codigo.get(tipo_pedido_param, 'Todos')

    if codigo == 'Todos':
        pedidos_qs = Pedido.objects.select_related('usuario', 'mesa').order_by('-fecha')
    else:
        pedidos_qs = Pedido.objects.filter(tipo_pedido=codigo).select_related('usuario', 'mesa').order_by('-fecha')

    usuarios = Usuario.objects.all()
    mesas = Mesa.objects.filter(estado='disponible')

    # Pasamos a la plantilla la etiqueta original (para que las tabs sigan comparando por texto visible)
    context = {
        'pedidos': pedidos_qs,
        'usuarios': usuarios,
        'mesas': mesas,
        'usuario': usuario,
        'rol': usuario.rol,
        'tipo_pedido_seleccionado': tipo_pedido_param,  # IMPORTANT: la plantilla usa esta variable
    }

    return render(request, 'C2_Pedido/Pedidos.html', context)

# ---- REGISTRAR PEDIDO ----


#AQUI SE USA EL FACTORY

def registrar_pedido(request):
    if request.method == 'POST':
        usuario_id = request.POST.get('usuario')
        mesa_id = request.POST.get('mesa')
        tipo_pedido = request.POST.get('tipo_pedido')

        # Recoger productos desde el formulario
        productos_info = []
        for key in request.POST:
            if key.startswith('producto_'):
                producto_id = int(key.split('_')[1])
                cantidad = int(request.POST[key])
                productos_info.append({'producto_id': producto_id, 'cantidad': cantidad})

        # Usamos el Factory para crear el pedido y sus detalles
        PedidoFactory.crear_pedido(usuario_id, tipo_pedido, productos_info, mesa_id)

        return redirect('pedidos')


# ---- ACTUALIZAR PEDIDO ----
@csrf_exempt
def actualizar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            if 'tipo_pedido' in data:
                pedido.tipo_pedido = data['tipo_pedido']
            if 'estado' in data:
                pedido.estado = data['estado']
            if 'mesa' in data:
                mesa = Mesa.objects.filter(numero=data['mesa']).first()
                pedido.mesa = mesa
            pedido.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# ---- ELIMINAR PEDIDO ----
@csrf_exempt
def eliminar_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    if request.method == 'POST':
        pedido.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

# --- VER DETALLES DE UN PEDIDO ---
def ver_detalle_pedido(request, id):
    pedido = get_object_or_404(Pedido, id=id)
    detalles_qs = DetallePedido.objects.filter(pedido=pedido).select_related('producto')
    detalles = [{
        'id': d.id,
        'producto': d.producto.nombre,
        'producto_id': d.producto.id,
        'cantidad': d.cantidad,
        'subtotal': float(d.subtotal)
    } for d in detalles_qs]
    productos = [{'id': p.id, 'nombre': p.nombre, 'precio': float(p.precio)} for p in Producto.objects.all()]
    return JsonResponse({'pedido_id': pedido.id, 'detalles': detalles, 'productos': productos})

# --- AGREGAR DETALLE A UN PEDIDO ---
@csrf_exempt
def agregar_detalle_pedido(request, id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            producto_id = data.get('producto')
            cantidad = int(data.get('cantidad', 1))
            producto = get_object_or_404(Producto, id=producto_id)
            pedido = get_object_or_404(Pedido, id=id)

            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                subtotal=cantidad * producto.precio
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

@csrf_exempt
def guardar_detalles_pedido(request, id):
    """
    Espera JSON: { items: [ { producto: <id>, cantidad: <n> }, ... ] }
    Crea los detalle_pedido correspondientes (bulk).
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        items = data.get('items', [])
        pedido = get_object_or_404(Pedido, id=id)
        created = []
        for item in items:
            producto_id = item.get('producto')
            cantidad = int(item.get('cantidad', 1))
            producto = get_object_or_404(Producto, id=producto_id)
            dp = DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                subtotal = cantidad * producto.precio
            )
            created.append(dp.id)
        return JsonResponse({'success': True, 'created': created})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


def generar_pdf(request, pedido_id):
    pedido = Pedido.objects.select_related('usuario', 'mesa').get(id=pedido_id)
    detalles = DetallePedido.objects.filter(pedido=pedido)

    # calcular total
    total = sum(d.subtotal for d in detalles)

    template = get_template("pdf/pedido.html")
    html = template.render({
        "pedido": pedido,
        "detalles": detalles,
        "total": total,  # <-- pasar al template
    })

    response = HttpResponse(content_type="application/pdf")
    response['Content-Disposition'] = f'inline; filename="pedido_{pedido.id}.pdf"'

    pisa_status = pisa.CreatePDF(html, dest=response)
    if pisa_status.err:
        return HttpResponse("Error al generar PDF", status=500)
    return response

def modificar_detalle_pedido(request, pedido_id):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        items = data.get("items", [])
        pedido = Pedido.objects.get(id=pedido_id)

        for item in items:
            detalle_id = item.get("id_existente")
            cantidad = item.get("cantidad")
            if detalle_id:
                detalle = DetallePedido.objects.get(id=detalle_id, pedido=pedido)
                detalle.cantidad = cantidad
                detalle.subtotal = detalle.producto.precio * cantidad
                detalle.save()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False, "error": "Método no permitido"})


@csrf_exempt
def guardar_carrito_ajax(request):
    """
    Recibe los datos del carrito (productos, cantidad) vía AJAX y crea un Pedido.
    Utiliza el PedidoFactory para la creación.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        # 1. Decodificar el JSON enviado desde el frontend
        data = json.loads(request.body.decode('utf-8'))

        carrito_items = data.get('carrito', [])
        tipo_pedido = data.get('tipo_pedido')
        # El frontend (cliente) solo envía null para mesa_id si el tipo_pedido no es 'local',
        # en caso de ser 'local' un mesero podría asignarlo, pero aquí asumimos un flujo de cliente.
        mesa_id = data.get('mesa_id')

        # 2. Obtener el ID del usuario actual (asumiendo que está en la sesión, como en tus otras vistas)
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)

        # 3. Validar los datos del carrito
        if not carrito_items:
            return JsonResponse({'success': False, 'error': 'El carrito está vacío.'}, status=400)

        # 4. Formatear los ítems del carrito para el PedidoFactory
        # Tu PedidoFactory espera: [{'producto_id': <id>, 'cantidad': <n>}, ...]
        productos_info = [
            {'producto_id': item['id'], 'cantidad': item['cantidad']}
            for item in carrito_items
        ]

        # 5. Usar el Factory para crear el pedido y sus detalles
        # Nota: El Factory debe manejar la lógica de obtener los objetos Usuario y Producto
        nuevo_pedido = PedidoFactory.crear_pedido(
            usuario_id=usuario_id,
            tipo_pedido=tipo_pedido,
            productos_info=productos_info,
            mesa_id=mesa_id  # Puede ser None
        )

        return JsonResponse({
            'success': True,
            'mensaje': f'¡Pedido #{nuevo_pedido.id} creado exitosamente!',
            'pedido_id': nuevo_pedido.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido.'}, status=400)
    except Exception as e:
        # Capturar errores del Factory (ej. Producto no encontrado)
        return JsonResponse({'success': False, 'error': f'Error interno al procesar el pedido: {str(e)}'}, status=500)


@csrf_exempt
def guardar_carrito_ajax(request):
    """
    Recibe los datos del carrito (productos, cantidad) vía AJAX y crea un Pedido.
    Utiliza el PedidoFactory para la creación.
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)

    try:
        # 1. Decodificar el JSON enviado desde el frontend
        data = json.loads(request.body.decode('utf-8'))

        carrito_items = data.get('carrito', [])
        tipo_pedido = data.get('tipo_pedido')
        # El frontend (cliente) solo envía null para mesa_id si el tipo_pedido no es 'local',
        # en caso de ser 'local' un mesero podría asignarlo, pero aquí asumimos un flujo de cliente.
        mesa_id = data.get('mesa_id')

        # 2. Obtener el ID del usuario actual (asumiendo que está en la sesión, como en tus otras vistas)
        usuario_id = request.session.get('usuario_id')
        if not usuario_id:
            return JsonResponse({'success': False, 'error': 'Usuario no autenticado'}, status=401)

        # 3. Validar los datos del carrito
        if not carrito_items:
            return JsonResponse({'success': False, 'error': 'El carrito está vacío.'}, status=400)

        # 4. Formatear los ítems del carrito para el PedidoFactory
        # Tu PedidoFactory espera: [{'producto_id': <id>, 'cantidad': <n>}, ...]
        productos_info = [
            {'producto_id': item['id'], 'cantidad': item['cantidad']}
            for item in carrito_items
        ]

        # 5. Usar el Factory para crear el pedido y sus detalles
        # Nota: El Factory debe manejar la lógica de obtener los objetos Usuario y Producto
        nuevo_pedido = PedidoFactory.crear_pedido(
            usuario_id=usuario_id,
            tipo_pedido=tipo_pedido,
            productos_info=productos_info,
            mesa_id=mesa_id  # Puede ser None
        )

        return JsonResponse({
            'success': True,
            'mensaje': f'¡Pedido #{nuevo_pedido.id} creado exitosamente!',
            'pedido_id': nuevo_pedido.id
        })

    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Formato JSON inválido.'}, status=400)
    except Exception as e:
        # Capturar errores del Factory (ej. Producto no encontrado)
        return JsonResponse({'success': False, 'error': f'Error interno al procesar el pedido: {str(e)}'}, status=500)


def vistaPagos(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    detalles = DetallePedido.objects.filter(pedido=pedido).select_related("producto")
    total = sum(d.subtotal for d in detalles)

    # 🔐 Stripe PaymentIntent
    intent = stripe.PaymentIntent.create(
        amount=int(total * 100),  # Stripe usa centavos
        currency="usd",
        metadata={
            "pedido_id": pedido.id
        }
    )

    carrito = [
        {
            "nombre": d.producto.nombre,
            "cantidad": d.cantidad,
            "subtotal": float(d.subtotal)

        }
        for d in detalles
    ]

    contexto = {
        "pedido": pedido,
        "detalles": detalles,
        "subtotal": sum(d.subtotal for d in detalles),
        "total": pedido.total if hasattr(pedido, "total") else sum(d.subtotal for d in detalles),
        "carrito": carrito,
        "client_secret": intent.client_secret,
        "STRIPE_PUBLIC_KEY": settings.STRIPE_PUBLIC_KEY,
    }

    return render(request, "Vistas/Vista_cliente/pago.html", contexto)


@csrf_exempt
def confirmar_pago(request, pedido_id):
    if request.method != "POST":
        return JsonResponse({"error": "Método no permitido"}, status=405)

    pedido = get_object_or_404(Pedido, id=pedido_id)
    try:
        data = json.loads(request.body)
    except Exception as e:
        return JsonResponse({"error": "JSON inválido"}, status=400)

    try:
        detalles = DetallePedido.objects.filter(pedido=pedido)
        total = 0
        for d in detalles:
            total += d.subtotal


    except Exception as e:

        return JsonResponse({
            "error": f"Error calculando total: {str(e)}"
        }, status=500)

    try:
        Pago.objects.create(
            pedido=pedido,
            metodo=data.get("metodo"),
            monto=total,
            direccion_entrega=data.get("direccion"),
            telefono_contacto=data.get("telefono"),
            estado="completado"
        )
    except Exception as e:

        return JsonResponse({
            "error": f"Error guardando pago: {str(e)}"
        }, status=500)

    return JsonResponse({"success": True})






#ESTO ES NUEVO EL MODULO DE PEDIDO SE HA MODIFICADO POR LO DE PAGO




def pedidos_list(request):

    # Verificar sesión
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol.strip().lower() != 'administrador':
        return redirect('login')

    # Filtros
    estado_filtro = request.GET.get('estado', '')
    tipo_filtro = request.GET.get('tipo', '')
    buscar = request.GET.get('buscar', '')

    pedidos = Pedido.objects.select_related('usuario', 'mesa').prefetch_related('detalles__producto').order_by('-fecha')

    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    if tipo_filtro:
        pedidos = pedidos.filter(tipo_pedido=tipo_filtro)

    if buscar:
        pedidos = pedidos.filter(
            Q(usuario__nombre__icontains=buscar) |
            Q(usuario__apellido__icontains=buscar) |
            Q(id__icontains=buscar)
        )

    # Calcular total de cada pedido
    pedidos_con_total = []
    for pedido in pedidos:
        total = sum(detalle.subtotal for detalle in pedido.detalles.all())
        pedidos_con_total.append({
            'pedido': pedido,
            'total': total
        })

    return render(request, 'C2_Pedido/pedidos_list.html', {
        'pedidos_con_total': pedidos_con_total,
        'usuario': usuario,
        'estado_filtro': estado_filtro,
        'tipo_filtro': tipo_filtro,
        'buscar': buscar
    })


def pedidos_create(request):
    """Crear nuevo pedido"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol.strip().lower() != 'administrador':
        return redirect('login')

    if request.method == 'POST':
        cliente_id = request.POST.get('cliente_id')

        # RESTRICCIÓN: el usuario no puede tener pedidos pendientes
        pedidos_pendientes = Pedido.objects.filter(usuario_id=cliente_id, estado='pendiente')
        if pedidos_pendientes.exists():
            alert_message = 'Este cliente ya tiene un pedido pendiente. No puede crear otro hasta que se pague.'
            return render(request, 'C2_Pedido/pedidos_form.html', {
                'usuario': usuario,
                'clientes': Usuario.objects.all(),
                'productos': Producto.objects.all(),
                'mesas_disponibles': Mesa.objects.filter(estado='disponible'),
                'alert_message': alert_message
            })

        try:
            # Datos del pedido
            tipo_pedido = request.POST.get('tipo_pedido')
            mesa_id = request.POST.get('mesa_id')
            estado = request.POST.get('estado', 'pendiente')

            # Validar cliente
            if not Usuario.objects.filter(id=cliente_id).exists():
                messages.error(request, 'Cliente no encontrado')
                return redirect('pedidos_create')

            # Crear pedido
            pedido = Pedido(
                usuario_id=cliente_id,
                tipo_pedido=tipo_pedido,
                estado=estado
            )

            # Asignar mesa si es tipo local
            if tipo_pedido == 'local' and mesa_id:
                pedido.mesa_id = mesa_id
                # Cambiar estado de la mesa a ocupada
                mesa = Mesa.objects.get(id=mesa_id)
                mesa.estado = 'ocupada'
                mesa.save()

            pedido.save()

            # Agregar productos (detalles del pedido)
            productos_ids = request.POST.getlist('producto_id[]')
            cantidades = request.POST.getlist('cantidad[]')

            if not productos_ids:
                messages.error(request, 'Debe agregar al menos un producto al pedido')
                pedido.delete()
                return redirect('pedidos_create')

            for producto_id, cantidad in zip(productos_ids, cantidades):
                if producto_id and cantidad:
                    producto = Producto.objects.get(id=producto_id)
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=int(cantidad),
                        subtotal=producto.precio * int(cantidad)
                    )

            messages.success(request, f'Pedido #{pedido.id} creado exitosamente')
            return redirect('pedidos_detail', id=pedido.id)

        except Exception as e:
            messages.error(request, f'Error al crear pedido: {str(e)}')

    clientes = Usuario.objects.all()
    productos = Producto.objects.all()
    mesas_disponibles = Mesa.objects.filter(estado='disponible')

    return render(request, 'C2_Pedido/pedidos_form.html', {
        'usuario': usuario,
        'clientes': clientes,
        'productos': productos,
        'mesas_disponibles': mesas_disponibles
    })

def pedidos_detail(request, id):

    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol.strip().lower() != 'administrador':
        return redirect('login')

    pedido = get_object_or_404(Pedido.objects.select_related('usuario', 'mesa'), id=id)
    detalles = pedido.detalles.select_related('producto').all()

    # Calcular total
    total = sum(detalle.subtotal for detalle in detalles)

    # Verificar si tiene pago
    try:
        pago = Pago.objects.get(pedido=pedido)
    except Pago.DoesNotExist:
        pago = None

    return render(request, 'C2_Pedido/pedidos_detail.html', {
        'usuario': usuario,
        'pedido': pedido,
        'detalles': detalles,
        'total': total,
        'pago': pago
    })


def pedidos_edit(request, id):
    """Editar pedido existente"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol.strip().lower() != 'administrador':
        return redirect('login')

    pedido = get_object_or_404(Pedido, id=id)
    detalles_actuales = pedido.detalles.all()

    if request.method == 'POST':
        try:
            # Actualizar datos básicos
            tipo_pedido = request.POST.get('tipo_pedido')
            mesa_id = request.POST.get('mesa_id')
            estado = request.POST.get('estado')

            # Liberar mesa anterior si existía
            if pedido.mesa:
                mesa_anterior = pedido.mesa
                mesa_anterior.estado = 'disponible'
                mesa_anterior.save()

            pedido.tipo_pedido = tipo_pedido
            pedido.estado = estado

            # Asignar nueva mesa si es necesario
            if tipo_pedido == 'local' and mesa_id:
                pedido.mesa_id = mesa_id
                mesa = Mesa.objects.get(id=mesa_id)
                mesa.estado = 'ocupada'
                mesa.save()
            else:
                pedido.mesa = None

            pedido.save()

            # Eliminar detalles antiguos
            pedido.detalles.all().delete()

            # Agregar nuevos productos
            productos_ids = request.POST.getlist('producto_id[]')
            cantidades = request.POST.getlist('cantidad[]')

            for producto_id, cantidad in zip(productos_ids, cantidades):
                if producto_id and cantidad:
                    producto = Producto.objects.get(id=producto_id)
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=int(cantidad),
                        subtotal=producto.precio * int(cantidad)
                    )

            messages.success(request, f'Pedido #{pedido.id} actualizado exitosamente')
            return redirect('pedidos_detail', id=pedido.id)

        except Exception as e:
            messages.error(request, f'Error al actualizar pedido: {str(e)}')

    clientes = Usuario.objects.all()
    productos = Producto.objects.all()
    mesas_disponibles = Mesa.objects.filter(estado='disponible')

    return render(request, 'C2_Pedido/pedidos_form.html', {
        'usuario': usuario,
        'pedido': pedido,
        'detalles_actuales': detalles_actuales,
        'clientes': clientes,
        'productos': productos,
        'mesas_disponibles': mesas_disponibles
    })


def pedidos_delete(request, id):
    """Eliminar pedido"""
    usuario_id = request.session.get('usuario_id')

    if not usuario_id:
        return redirect('login')

    usuario = Usuario.objects.get(id=usuario_id)
    if usuario.rol.strip().lower() != 'administrador':
        return redirect('login')

    # Obtener el pedido (antes de intentar eliminarlo)
    pedido = get_object_or_404(Pedido, id=id)

    # RESTRICCIÓN: Verificar si el pedido tiene un pago registrado antes de eliminar
    if hasattr(pedido, 'pago'):
        messages.error(request, 'No se puede eliminar este pedido porque ya tiene un pago registrado.')
        return redirect('pedidos_list')

    if request.method == 'POST':
        try:
            # Liberar mesa si está ocupada
            if pedido.mesa:
                mesa = pedido.mesa
                mesa.estado = 'disponible'
                mesa.save()

            pedido_id = pedido.id
            pedido.delete()
            messages.success(request, f'Pedido #{pedido_id} eliminado exitosamente')
        except Exception as e:
            messages.error(request, f'Error al eliminar pedido: {str(e)}')

    return redirect('pedidos_list')


def pedidos_cambiar_estado(request, id):
    """Cambiar estado del pedido (AJAX)"""
    usuario_id = request.session.get('usuario_id')
    if not usuario_id:
        return redirect('login')

    if request.method == 'POST':
        try:
            pedido = get_object_or_404(Pedido, id=id)
            nuevo_estado = request.POST.get('estado')

            pedido.estado = nuevo_estado
            pedido.save()

            # Si el estado es "entregado" y la mesa está ocupada, liberarla
            if nuevo_estado == 'entregado' and pedido.mesa:
                mesa = pedido.mesa
                mesa.estado = 'disponible'
                mesa.save()

            messages.success(request, f'Estado del pedido #{pedido.id} cambiado a "{nuevo_estado}"')
        except Exception as e:
            messages.error(request, f'Error al cambiar estado: {str(e)}')

    return redirect('pedidos_detail', id=id)
# ---------------------------
# PAGO - VISTA
# ---------------------------
def pagos_list(request):
    # Query inicial: todos los pagos ordenados por fecha descendente
    pagos = Pago.objects.select_related('pedido', 'pedido__usuario').order_by('-fecha_pago')

    # FILTROS desde GET
    cliente = request.GET.get('cliente', '').strip()
    metodo = request.GET.get('metodo', '').strip()
    fecha_inicio = request.GET.get('fecha_inicio', '').strip()
    fecha_fin = request.GET.get('fecha_fin', '').strip()

    # Filtrar por nombre o apellido del cliente
    if cliente:
        pagos = pagos.filter(
            pedido__usuario__nombre__icontains=cliente
        ) | pagos.filter(
            pedido__usuario__apellido__icontains=cliente
        )

    # Filtrar por método de pago
    if metodo:
        pagos = pagos.filter(metodo=metodo)

    # Filtrar por rango de fechas
    if fecha_inicio:
        pagos = pagos.filter(fecha_pago__gte=fecha_inicio)
    if fecha_fin:
        pagos = pagos.filter(fecha_pago__lte=fecha_fin)

    return render(request, 'C2_Pedido/pagos_list.html', {
        'pagos': pagos
    })

def registrar_pago(request, pedido_id):
    pedido = get_object_or_404(Pedido, id=pedido_id)

    if hasattr(pedido, 'pago'):
        messages.warning(request, 'Este pedido ya tiene un pago registrado.')
        return redirect('pagos_list')

    total = sum(d.subtotal for d in pedido.detalles.all())

    if request.method == 'POST':
        Pago.objects.create(
            pedido=pedido,
            metodo=request.POST['metodo'],
            monto=Decimal(total),
            direccion_entrega=request.POST.get('direccion_entrega'),
            telefono_contacto=request.POST.get('telefono_contacto')
        )

        pedido.estado = 'pagado'
        pedido.save()

        messages.success(request, 'Pago registrado correctamente.')
        return redirect('pagos_list')

    return render(request, 'C2_Pedido/pago_form.html', {
        'pedido': pedido,
        'total': total
    })


def editar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    pedido = pago.pedido

    if request.method == 'POST':
        pago.metodo = request.POST['metodo']
        pago.direccion_entrega = request.POST.get('direccion_entrega')
        pago.telefono_contacto = request.POST.get('telefono_contacto')
        pago.save()

        messages.success(request, 'Pago actualizado correctamente.')
        return redirect('pagos_list')

    return render(request, 'C2_Pedido/pago_edit.html', {
        'pago': pago,
        'pedido': pedido
    })


def eliminar_pago(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)
    pedido = pago.pedido

    if request.method == 'POST':
        if hasattr(pedido, 'pago'):
            messages.error(request, 'No se puede eliminar este pedido porque ya tiene un pago registrado.')
            return redirect('pedidos_list')
        pago.delete()
        pedido.estado = 'pendiente'
        pedido.save()

        messages.success(request, 'Pago eliminado correctamente.')
        return redirect('pagos_list')

    return render(request, 'C2_Pedido/pago_delete.html', {
        'pago': pago
    })


def imprimir_factura(request, pago_id):
    pago = get_object_or_404(Pago, id=pago_id)

    # Calcular subtotal sumando los detalles
    subtotal = sum(detalle.subtotal for detalle in pago.pedido.detalles.all())

    # Contexto para el template
    context = {
        'pago': pago,
        'subtotal': subtotal,
    }

    # Cargar el template como string
    template = get_template('C2_Pedido/factura_pdf.html')
    html = template.render(context)

    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'filename="Factura_{pago.id}.pdf"'

    # Generar PDF
    pisa_status = pisa.CreatePDF(
        src=html,
        dest=response
    )

    if pisa_status.err:
        return HttpResponse('Error al generar el PDF: %s' % pisa_status.err)

    return response