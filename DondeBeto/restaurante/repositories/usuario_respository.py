from ..models import Usuario
from django.contrib.auth.hashers import make_password

class UsuarioRepository:

    def obtener_por_email(self, email):
        try:
            return Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return None

    def obtener_por_id(self, id):
        return Usuario.objects.filter(id=id).first()

    def listar_por_rol(self, rol):
        return Usuario.objects.filter(rol=rol)

    def crear(self, data):
        data["contraseña"] = make_password(data["contraseña"])
        return Usuario.objects.create(**data)

    def actualizar(self, usuario, data):
        for campo, valor in data.items():
            setattr(usuario, campo, valor)
        usuario.save()
        return usuario

    def eliminar(self, id):
        Usuario.objects.filter(id=id).delete()