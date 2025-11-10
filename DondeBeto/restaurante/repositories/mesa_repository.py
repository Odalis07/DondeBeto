# restaurante/repositories/mesa_repository.py
from ..models import Mesa

class MesaRepository:

    def listar(self):
        return Mesa.objects.all()

    def obtener(self, id):
        return Mesa.objects.filter(id=id).first()

    def obtener_por_numero(self, numero):
        return Mesa.objects.filter(numero=numero).first()

    def listar_disponibles(self):
        return Mesa.objects.filter(estado='Libre')

    def actualizar(self, mesa, data):
        for campo, valor in data.items():
            setattr(mesa, campo, valor)
        mesa.save()
        return mesa

    def crear(self, data):
        return Mesa.objects.create(**data)

    def eliminar(self, id):
        Mesa.objects.filter(id=id).delete()