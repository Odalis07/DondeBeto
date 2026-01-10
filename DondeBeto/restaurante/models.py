from django.db import models
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal

# ------------------------------
# Modelo Usuario
# ------------------------------
class Usuario(models.Model):
    cedula = models.CharField(max_length=10)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    contraseña = models.CharField(max_length=128)
    rol = models.CharField(default='usuario', max_length=20)
    pregunta_clave = models.CharField(max_length=255, null=True, blank=True)
    respuesta_clave = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        db_table = "usuario"

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
    estado = models.CharField(max_length=20, default='disponible')

    class Meta:
        db_table = "mesa"

    def __str__(self):
        return f"Mesa {self.numero} ({self.estado})"


# ------------------------------
# Modelo Categoria
# ------------------------------
class Categoria(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = "categoria"

    def __str__(self):
        return self.nombre


# ------------------------------
# Modelo Producto
# ------------------------------
class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=8, decimal_places=2)

    iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="IVA en porcentaje (ej: 15.00)"
    )

    descuento = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Descuento en porcentaje (ej: 10.00)"
    )

    stock = models.PositiveIntegerField(null=True, blank=True)

    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        db_table = "producto"

    def __str__(self):
        return self.nombre

    # ==========================
    # 🔥 CÁLCULOS CORRECTOS
    # ==========================

    @property
    def precio_con_descuento(self):
        """
        Precio final aplicando descuento (sin IVA)
        """
        if self.descuento:
            return self.precio - (self.precio * self.descuento / Decimal('100'))
        return self.precio

    @property
    def precio_con_iva(self):
        """
        Precio con IVA aplicado (sin descuento)
        """
        if self.iva:
            return self.precio + (self.precio * self.iva / Decimal('100'))
        return self.precio

    @property
    def precio_final(self):
        """
        Precio final con descuento + IVA
        """
        precio = self.precio_con_descuento

        if self.iva:
            precio += precio * self.iva / Decimal('100')

        return precio

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
    estado = models.CharField(max_length=20, default='pendiente')

    class Meta:
        db_table = "pedido"

    def __str__(self):
        return f"Pedido {self.id}"


# ------------------------------
# Modelo DetallePedido
# ------------------------------
class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    # Subtotal se guarda desde la vista
    subtotal = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        db_table = "detalle_pedido"

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


# ------------------------------
# Modelo Pago
# ------------------------------
class Pago(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    metodo = models.CharField(max_length=50)
    monto = models.DecimalField(max_digits=8, decimal_places=2)

    comprobante_transferencia = models.ImageField(
        upload_to='comprobantes/',
        null=True,
        blank=True
    )

    direccion_entrega = models.CharField(max_length=255, null=True, blank=True)
    telefono_contacto = models.CharField(max_length=15, null=True, blank=True)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='completado')

    class Meta:
        db_table = "pago"

    def __str__(self):
        return f"Pago #{self.id} - Pedido {self.pedido.id}"
