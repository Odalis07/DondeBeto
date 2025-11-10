from ..models import Producto
class ProductoRepository:

    def listar(self):
        return Producto.objects.all()

    def listar_por_categoria(self, categoria_nombre):
        return Producto.objects.filter(categoria__nombre=categoria_nombre)

    def obtener(self, id):
        return Producto.objects.filter(id=id).first()

    def crear(self, data):
        return Producto.objects.create(**data)

    def actualizar(self, producto, data):
        for campo, valor in data.items():
            setattr(producto, campo, valor)
        producto.save()
        return producto

    def eliminar(self, id):
        Producto.objects.filter(id=id).delete()