from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# ------------------------------
# Modelo Usuario
# ------------------------------
class Usuario(models.Model):
    cedula = models.CharField(max_length=10, null=False, blank=False)
    nombre = models.CharField(max_length=100, null=False, blank=False)
    apellido = models.CharField(max_length=100, null=False, blank=False)
    email = models.EmailField(unique=True, null=False, blank=False)
    contraseña = models.CharField(max_length=128, null=False, blank=False)
    rol = models.CharField(default='usuario', max_length=20)
    pregunta_clave = models.CharField(max_length=255, null=True, blank=True)
    respuesta_clave = models.CharField(max_length=255, null=True, blank=True)

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


# ------------------------------
# Modelo Mesa
# ------------------------------
class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    capacidad = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, default='disponible')  # disponible / ocupada / reservada

    class Meta:
        db_table = "mesa"
        verbose_name = "Mesa"
        verbose_name_plural = "Mesas"

    def __str__(self):
        return f"Mesa {self.numero} ({self.estado})"


# ------------------------------
# Modelo Categoria y Producto
# ------------------------------
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = "categoria"
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    categoria = models.ForeignKey(Categoria, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return self.nombre


# ------------------------------
# Modelo Pedido
# ------------------------------
class Pedido(models.Model):
    TIPO_CHOICES = [
        ('local', 'En el local'),
        ('domicilio', 'Domicilio'),
        ('para_llevar', 'Para llevar'),
    ]

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True)
    tipo_pedido = models.CharField(max_length=20, choices=TIPO_CHOICES, default='local')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='pendiente')  # pendiente, en preparación, entregado, pagado

    class Meta:
        db_table = "pedido"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def __str__(self):
        return f"Pedido {self.id} ({self.tipo_pedido})"


# ------------------------------
# Modelo DetallePedido
# ------------------------------
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = "detalle_pedido"
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.producto.precio
        super().save(*args, **kwargs)


# ------------------------------
# Modelo Pago
# ------------------------------
class Pago(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    metodo = models.CharField(max_length=50)  # efectivo, tarjeta, transferencia
    monto = models.DecimalField(max_digits=8, decimal_places=2)
    direccion_entrega = models.CharField(max_length=255, blank=True, null=True)  # solo si es domicilio
    telefono_contacto = models.CharField(max_length=15, blank=True, null=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='completado')

    class Meta:
        db_table = "pago"
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    def __str__(self):
        return f"Factura #{self.id} - Pedido {self.pedido.id}"