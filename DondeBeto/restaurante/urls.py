from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('registro_2/', views.registro_2_view, name='registro_2'),
    path('clave_olvidada/', views.claveOlvidada_view, name='Clave_Olvidada'),
]
