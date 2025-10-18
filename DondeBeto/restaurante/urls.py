from django.urls import path
from .views import login_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
]
