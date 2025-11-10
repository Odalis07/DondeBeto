from .models import Pedido, DetallePedido, Mesa, Producto, Usuario


class PedidoFactory:
    @staticmethod
    def crear_pedido(usuario_id, tipo_pedido, productos_info, mesa_id=None):
        """
        Crea un pedido completo con detalles de productos.
        productos_info: lista de dicts -> [{'producto_id': 1, 'cantidad': 2}, ...]
        """
        usuario = Usuario.objects.get(id=usuario_id)
        mesa = Mesa.objects.get(id=mesa_id) if mesa_id else None

        # Crear pedido
        pedido = Pedido.objects.create(
            usuario=usuario,
            mesa=mesa,
            tipo_pedido=tipo_pedido,
            estado='pendiente'
        )

        # Si es "local", marcar mesa como ocupada
        if tipo_pedido == 'local' and mesa:
            mesa.estado = 'ocupada'
            mesa.save()

        # Crear detalles de pedido
        for item in productos_info:
            producto = Producto.objects.get(id=item['producto_id'])
            cantidad = item.get('cantidad', 1)
            DetallePedido.objects.create(
                pedido=pedido,
                producto=producto,
                cantidad=cantidad,
                subtotal=cantidad * producto.precio
            )

        return pedido