from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('clave_olvidada/', views.clave_olvidada, name='Clave_Olvidada'),
    path('clave_cambiada/', views.clave_cambiada, name='clave_cambiada'),
path('admin/', views.vista_adm, name='vista_adm'),


]
