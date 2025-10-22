from django.shortcuts import render

def login_view(request):
    return render(request, 'usuario/login.html')

def registro_view(request):
    return render(request, 'usuario/registro.html')


def registro_2_view(request):

    return render(request, 'usuario/registro_dos.html')

def claveOlvidada_view(request):

    return render(request, 'usuario/clave_olvidada.html')

