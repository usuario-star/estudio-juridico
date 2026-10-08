import json
from datetime import date

from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Cliente, EstadoCaso, Caso, Expediente, Pago


def lista_clientes(request):
    clientes = Cliente.objects.all()
    return render(request, 'casos/lista_clientes.html', {'clientes': clientes})


def crear_cliente(request):
    error = None
    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()

        if not nombres or not documento or not telefono or not correo:
            error = 'Todos los campos son obligatorios.'
        elif Cliente.objects.filter(documento=documento).exists():
            error = f'Ya existe un cliente con el documento {documento}.'
        else:
            Cliente.objects.create(
                nombres=nombres,
                documento=documento,
                telefono=telefono,
                correo=correo
            )
            return redirect('lista_clientes')

    return render(request, 'casos/crear_cliente.html', {'error': error})


def editar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    error = None

    if request.method == 'POST':
        nombres = request.POST.get('nombres', '').strip()
        documento = request.POST.get('documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        correo = request.POST.get('correo', '').strip()

        if not nombres or not documento or not telefono or not correo:
            error = 'Todos los campos son obligatorios.'
        elif Cliente.objects.filter(documento=documento).exclude(id=id).exists():
            error = f'Ya existe otro cliente con el documento {documento}.'
        else:
            cliente.nombres = nombres
            cliente.documento = documento
            cliente.telefono = telefono
            cliente.correo = correo
            cliente.save()
            return redirect('lista_clientes')

    return render(request, 'casos/editar_cliente.html', {
        'cliente': cliente,
        'error': error
    })


def eliminar_cliente(request, id):
    cliente = get_object_or_404(Cliente, id=id)
    error = None

    if request.method == 'POST':
        try:
            cliente.delete()
            return redirect('lista_clientes')
        except Exception as e:
            error = f'No se puede eliminar: {e}'

    return render(request, 'casos/eliminar_cliente.html', {
        'cliente': cliente,
        'error': error
    })

def lista_casos(request):
    estado_id = request.GET.get('estado')
    if not estado_id:
        estado_id = request.COOKIES.get('ultimo_estado')

    casos = Caso.objects.select_related('cliente', 'estado').prefetch_related('abogados')
    estado_seleccionado = None
    if estado_id:
        try:
            estado_id = int(estado_id)
            casos = casos.filter(estado_id=estado_id)
            estado_seleccionado = EstadoCaso.objects.get(id=estado_id)
        except (ValueError, EstadoCaso.DoesNotExist):
            pass

    estados = EstadoCaso.objects.all()
    response = render(request, 'casos/lista_casos.html', {
        'casos': casos,
        'estados': estados,
        'estado_seleccionado': estado_seleccionado,
    })
    if estado_id:
        response.set_cookie('ultimo_estado', str(estado_id), max_age=86400)
    return response


def detalle_caso(request, id):
    caso = get_object_or_404(
        Caso.objects.select_related('cliente', 'estado').prefetch_related(
            'abogados', 'expedientes', 'pagos'
        ),
        id=id
    )
    mensaje = None
    error = None

    if request.method == 'POST' and request.POST.get('accion') == 'registrar_pago':
        monto_str = request.POST.get('monto', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        if not monto_str:
            error = 'Debe ingresar un monto.'
        else:
            try:
                monto = float(monto_str)
                if monto <= 0:
                    error = 'El monto debe ser mayor que cero.'
            except ValueError:
                error = 'El monto no es valido.'
        if not error:
            if not caso.estado.permite_pagos:
                error = (
                    f'No se puede registrar un pago porque el caso esta '
                    f"en estado '{caso.estado.nombre}', "
                    f'el cual no permite pagos.'
                )
            else:
                Pago.objects.create(
                    caso=caso, monto=monto,
                    fecha=date.today(), descripcion=descripcion
                )
                mensaje = f'Pago de S/ {monto:.2f} registrado exitosamente.'
                caso.refresh_from_db()

    if request.method == 'POST' and request.POST.get('accion') == 'subir_documento':
        expediente_id = request.POST.get('expediente_id')
        archivo = request.FILES.get('documento')
        if not expediente_id:
            error = 'Debe seleccionar un expediente.'
        elif not archivo:
            error = 'Debe seleccionar un archivo.'
        else:
            try:
                expediente = Expediente.objects.get(id=int(expediente_id), caso=caso)
                expediente.documento = archivo
                expediente.save()
                mensaje = (
                    f'Documento "{archivo.name}" subido al '
                    f'expediente {expediente.numero}.'
                )
            except (ValueError, Expediente.DoesNotExist):
                error = 'El expediente seleccionado no es valido.'

    return render(request, 'casos/detalle_caso.html', {
        'caso': caso, 'mensaje': mensaje, 'error': error,
    })


def api_caso(request, id):
    caso = get_object_or_404(
        Caso.objects.select_related('cliente', 'estado').prefetch_related(
            'abogados', 'expedientes'
        ),
        id=id
    )
    data = {
        'codigo': caso.codigo,
        'titulo': caso.titulo,
        'cliente': caso.cliente.nombres,
        'estado': caso.estado.nombre,
        'abogados': [
            abg.get_full_name() or abg.username
            for abg in caso.abogados.all()
        ],
        'numero_expedientes': caso.expedientes.count(),
        'total_pagado': float(caso.total_pagado()),
    }
    return JsonResponse(data)
