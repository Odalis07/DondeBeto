from django.shortcuts import render

def login_view(request):
    return render(request, 'usuario/login.html')

def registro_view(request):
    return render(request, 'usuario/registro.html')

