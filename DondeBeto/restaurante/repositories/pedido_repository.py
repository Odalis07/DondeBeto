# restaurante/repositories/pedido_repository.py
from ..models import Pedido

class PedidoRepository:

    def listar(self):
        return Pedido.objects.all()

    def listar_por_usuario(self, usuario):
        return Pedido.objects.filter(usuario=usuario)

    def listar_por_estado(self, estado):
        return Pedido.objects.filter(estado=estado)

    def obtener(self, id):
        return Pedido.objects.filter(id=id).first()

    def guardar(self, pedido):
        pedido.save()
        return pedido

    def actualizar(self, pedido, data):
        for campo, valor in data.items():
            setattr(pedido, campo, valor)
        pedido.save()
        return pedido

    def eliminar(self, id):
        Pedido.objects.filter(id=id).delete()
