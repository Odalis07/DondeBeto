def rol_usuario(request):
    return {
        'rol': request.session.get('rol', None),
        'nombre_usuario': request.session.get('nombre', None)
    }