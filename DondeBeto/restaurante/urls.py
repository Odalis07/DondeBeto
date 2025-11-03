from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('clave_olvidada/', views.clave_olvidada, name='Clave_Olvidada'),
    path('clave_cambiada/', views.clave_cambiada, name='clave_cambiada'),
path('admin/', views.vista_adm, name='vista_adm'),
    path('usuarios/', views.usuarios_view, name='usuarios'),
    path('clientes/', views.clientes_view, name='clientes'),
    path('clientes/', views.lista_clientes, name='clientes'),
    path('clientes/registrar/', views.registrar_cliente_view, name='registrar_cliente'),
path('usuarios/registrar/', views.registrar_usuario_view, name='registrar_usuario'),
path('home-Vista_cliente/', views.home_cliente, name='home_cliente'),
path('ubicacion/', views.ubicacion, name='ubicacion'),
path('sobre-nosotros/', views.sobre_nosotros, name='sobre_nosotros'),
    path('perfil/', views.mi_perfil, name='mi_perfil'),
]
