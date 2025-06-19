# trabajos/views.py - ACTUALIZAR LOS IMPORTS
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
import re

# IMPORTAR TODOS LOS MODELOS
from .models import (
    Vacante, 
    Empresa, 
    TipoRegimen, 
    Documentos, 
    RegimenDocumentos,
    UsuarioPerfil,  # ← AGREGAR ESTE
    UsuarioVacante,  # ← AGREGAR ESTE
    EmpresaDocumentos
)

def inicio(request):
    """
    Vista principal - página de inicio
    """
    return render(request, 'inicio.html')

def lista_vacantes(request):
    """
    Vista para mostrar todas las vacantes con filtros
    """
    # Obtener todas las vacantes activas
    vacantes = Vacante.objects.filter(
        activa=True,
        fecha_expiracion__gte=timezone.now().date(),
        empresa__activo=True
    ).select_related('empresa').order_by('-fecha_publicacion')
    
    # Filtros de búsqueda
    search = request.GET.get('search')
    area = request.GET.get('area')
    clasificacion = request.GET.get('clasificacion')
    
    if search:
        vacantes = vacantes.filter(
            Q(nombre_vacante__icontains=search) |
            Q(empresa__nombre_empresa__icontains=search) |
            Q(area_desempeno__icontains=search)
        )
    
    if area:
        vacantes = vacantes.filter(area_desempeno__icontains=area)
    
    if clasificacion == 'mujeres':
        vacantes = vacantes.filter(vacante_mujer=True)
    elif clasificacion == 'discapacidad':
        vacantes = vacantes.filter(personas_discapacidad=True)
    
    # Paginación
    paginator = Paginator(vacantes, 12)  # 12 vacantes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener opciones para filtros
    areas_disponibles = Vacante.objects.filter(
        activa=True,
        area_desempeno__isnull=False
    ).values_list('area_desempeno', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'total_vacantes': vacantes.count(),
        'areas_disponibles': areas_disponibles,
        'search': search,
        'area': area,
        'solo_mujeres': False,  # Para el template
    }
    
    return render(request, 'lista_vacantes.html', context)

def vacantes_mujeres(request):
    """
    Vista para mostrar solo vacantes para mujeres
    """
    # Obtener solo vacantes para mujeres
    vacantes = Vacante.objects.filter(
        activa=True,
        fecha_expiracion__gte=timezone.now().date(),
        empresa__activo=True,
        vacante_mujer=True
    ).select_related('empresa').order_by('-fecha_publicacion')
    
    # Solo filtros de búsqueda y área para mujeres
    search = request.GET.get('search')
    area = request.GET.get('area')
    
    if search:
        vacantes = vacantes.filter(
            Q(nombre_vacante__icontains=search) |
            Q(empresa__nombre_empresa__icontains=search) |
            Q(area_desempeno__icontains=search)
        )
    
    if area:
        vacantes = vacantes.filter(area_desempeno__icontains=area)
    
    # Paginación
    paginator = Paginator(vacantes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener opciones para filtros (solo áreas para mujeres)
    areas_disponibles = Vacante.objects.filter(
        activa=True,
        vacante_mujer=True,
        area_desempeno__isnull=False
    ).values_list('area_desempeno', flat=True).distinct()
    
    context = {
        'page_obj': page_obj,
        'total_vacantes': vacantes.count(),
        'areas_disponibles': areas_disponibles,
        'search': search,
        'area': area,
        'solo_mujeres': True,  # Flag para el template
    }
    
    return render(request, 'lista_vacantes.html', context)

def detalle_vacante(request, id):
    """
    Vista para mostrar el detalle de una vacante específica
    """
    vacante = get_object_or_404(Vacante, id=id, activa=True)
    
    # Verificar si el usuario ya aplicó (si está logueado)
    ya_aplico = False
    puede_aplicar = True
    
    if request.user.is_authenticated:
        # Verificar si ya aplicó
        from .models import UsuarioVacante
        ya_aplico = UsuarioVacante.objects.filter(
            usuario=request.user,
            vacante=vacante
        ).exists()
        
        # Verificar si puede aplicar (validaciones)
        if vacante.vacante_mujer and hasattr(request.user, 'usuarioperfil'):
            if request.user.usuarioperfil.sexo != 'F':
                puede_aplicar = False
    
    # Vacantes relacionadas de la misma empresa
    vacantes_relacionadas = Vacante.objects.filter(
        empresa=vacante.empresa,
        activa=True,
        fecha_expiracion__gte=timezone.now().date()
    ).exclude(id=vacante.id)[:3]
    
    context = {
        'vacante': vacante,
        'ya_aplico': ya_aplico,
        'puede_aplicar': puede_aplicar,
        'vacantes_relacionadas': vacantes_relacionadas,
    }
    
    return render(request, 'detalle_vacante.html', context)

def login_empresa(request):
    """
    Vista para login y registro de empresas
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'login':
            # Procesar login
            correo = request.POST.get('correo_admin')
            password = request.POST.get('password')
            
            try:
                empresa = Empresa.objects.get(correo_administrador=correo, activo=True)
                if check_password(password, empresa.password):
                    # Guardar en sesión
                    request.session['empresa_id'] = empresa.id
                    request.session['empresa_nombre'] = empresa.nombre_empresa
                    messages.success(request, f'Bienvenido {empresa.nombre_empresa}')
                    return redirect('dashboard_empresa')
                else:
                    messages.error(request, 'Contraseña incorrecta')
            except Empresa.DoesNotExist:
                messages.error(request, 'Empresa no encontrada')
        
        elif action == 'register':
            # Procesar registro
            try:
                # Datos básicos
                nombre_empresa = request.POST.get('nombre_empresa')
                url_bolsa = request.POST.get('url_bolsa_trabajo')
                correo_contacto = request.POST.get('correo_contacto')
                correo_admin = request.POST.get('correo_administrador')
                password = request.POST.get('password')
                regimen_id = request.POST.get('regimen')
                
                # Verificar si ya existe
                if Empresa.objects.filter(correo_administrador=correo_admin).exists():
                    messages.error(request, 'Ya existe una empresa con este correo de administrador')
                else:
                    # Crear empresa
                    empresa = Empresa.objects.create(
                        nombre_empresa=nombre_empresa,
                        url_bolsa_trabajo=url_bolsa,
                        correo_contacto=correo_contacto,
                        correo_administrador=correo_admin,
                        password=make_password(password),
                        regimen_id=regimen_id,
                        logo_empresa=request.FILES.get('logo_empresa'),
                        carta_compromiso=request.FILES.get('carta_compromiso')
                    )
                    
                    # Guardar documentos subidos
                    regimen = TipoRegimen.objects.get(id=regimen_id)
                    documentos_requeridos = RegimenDocumentos.objects.filter(regimen=regimen)
                    
                    for req_doc in documentos_requeridos:
                        file_key = f'documento_{req_doc.documento.id}'
                        if file_key in request.FILES:
                            from .models import EmpresaDocumentos
                            EmpresaDocumentos.objects.create(
                                empresa=empresa,
                                documento=req_doc.documento,
                                archivo=request.FILES[file_key]
                            )
                    
                    messages.success(request, 'Empresa registrada exitosamente. Ahora puedes iniciar sesión.')
                    return redirect('empresas')
                    
            except Exception as e:
                messages.error(request, f'Error al registrar empresa: {str(e)}')
    
    # GET request - mostrar formulario
    tipos_regimen = TipoRegimen.objects.all()
    context = {
        'tipos_regimen': tipos_regimen,
    }
    
    return render(request, 'login_empresa.html', context)

def get_documentos_regimen(request):
    """
    Vista AJAX para obtener documentos según régimen
    """
    regimen_id = request.GET.get('regimen_id')
    if regimen_id:
        documentos = RegimenDocumentos.objects.filter(
            regimen_id=regimen_id
        ).select_related('documento')
        
        data = {
            'documentos': [
                {
                    'id': rd.documento.id,
                    'nombre': rd.documento.nombre_documento,
                    'obligatorio': rd.obligatorio
                }
                for rd in documentos
            ]
        }
        return JsonResponse(data)
    
    return JsonResponse({'documentos': []})

def dashboard_empresa(request):
    """
    Vista del dashboard de la empresa
    """
    # Verificar si hay sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        messages.error(request, 'Debes iniciar sesión como empresa')
        return redirect('empresas')
    
    empresa = get_object_or_404(Empresa, id=empresa_id, activo=True)
    
    # Obtener vacantes de la empresa
    vacantes = Vacante.objects.filter(empresa=empresa).order_by('-fecha_publicacion')
    
    # Estadísticas
    stats = {
        'total_vacantes': vacantes.count(),
        'vacantes_activas': vacantes.filter(activa=True).count(),
        'vacantes_expiradas': vacantes.filter(
            fecha_expiracion__lt=timezone.now().date()
        ).count(),
        'total_aplicaciones': 0  # Se calculará después si es necesario
    }
    
    context = {
        'empresa': empresa,
        'vacantes': vacantes,
        'stats': stats,
    }
    
    return render(request, 'dashboard_empresa.html', context)

# Agregar estas vistas al archivo trabajos/views.py

from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime

def crear_vacante(request):
    """
    Vista para crear una nueva vacante
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        
        # Obtener datos del formulario
        data = request.POST
        
        # Validar campos requeridos
        if not data.get('nombre_vacante') or not data.get('fecha_expiracion'):
            return JsonResponse({'success': False, 'message': 'Faltan campos requeridos'})
        
        # Procesar sueldo
        sueldo = None
        if data.get('sueldo'):
            try:
                sueldo = Decimal(data.get('sueldo'))
            except (InvalidOperation, ValueError):
                return JsonResponse({'success': False, 'message': 'Sueldo inválido'})
        
        # Procesar edades
        edad_min = None
        edad_max = None
        if data.get('edad_min'):
            try:
                edad_min = int(data.get('edad_min'))
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Edad mínima inválida'})
        
        if data.get('edad_max'):
            try:
                edad_max = int(data.get('edad_max'))
            except ValueError:
                return JsonResponse({'success': False, 'message': 'Edad máxima inválida'})
        
        # Validar fechas
        try:
            fecha_expiracion = datetime.strptime(data.get('fecha_expiracion'), '%Y-%m-%d').date()
            if fecha_expiracion <= timezone.now().date():
                return JsonResponse({'success': False, 'message': 'La fecha de expiración debe ser futura'})
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Fecha de expiración inválida'})
        
        # Crear la vacante
        vacante = Vacante.objects.create(
            nombre_vacante=data.get('nombre_vacante'),
            empresa=empresa,
            sueldo=sueldo,
            fecha_expiracion=fecha_expiracion,
            area_desempeno=data.get('area_desempeno', ''),
            descripcion_actividades=data.get('descripcion_actividades', ''),
            edad_min=edad_min,
            edad_max=edad_max,
            titulo_requerido=data.get('titulo_requerido', ''),
            tipo_vacante=data.get('tipo_vacante', 'Tiempo completo'),
            delegacion=data.get('delegacion', ''),
            nivel_academico=data.get('nivel_academico', ''),
            estado_civil=data.get('estado_civil', 'Indistinto'),
            personas_discapacidad=data.get('personas_discapacidad') == 'on',
            adultos_mayores=data.get('adultos_mayores') == 'on',
            vacante_mujer=data.get('vacante_mujer') == 'on',
            activa=True
        )
        
        return JsonResponse({'success': True, 'message': 'Vacante creada exitosamente', 'vacante_id': vacante.id})
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al crear vacante: {str(e)}'})

def obtener_vacante(request, id):
    """
    Vista para obtener los datos de una vacante específica
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        vacante = get_object_or_404(Vacante, id=id, empresa=empresa)
        
        data = {
            'id': vacante.id,
            'nombre_vacante': vacante.nombre_vacante,
            'area_desempeno': vacante.area_desempeno,
            'sueldo': float(vacante.sueldo) if vacante.sueldo else None,
            'fecha_expiracion': vacante.fecha_expiracion.strftime('%Y-%m-%d'),
            'descripcion_actividades': vacante.descripcion_actividades,
            'edad_min': vacante.edad_min,
            'edad_max': vacante.edad_max,
            'titulo_requerido': vacante.titulo_requerido,
            'tipo_vacante': vacante.tipo_vacante,
            'delegacion': vacante.delegacion,
            'nivel_academico': vacante.nivel_academico,
            'estado_civil': vacante.estado_civil,
            'personas_discapacidad': vacante.personas_discapacidad,
            'adultos_mayores': vacante.adultos_mayores,
            'vacante_mujer': vacante.vacante_mujer,
            'activa': vacante.activa
        }
        
        return JsonResponse(data)
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al obtener vacante: {str(e)}'})

@csrf_exempt
@require_http_methods(["PUT"])
def actualizar_vacante(request, id):
    """
    Vista para actualizar una vacante existente
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        vacante = get_object_or_404(Vacante, id=id, empresa=empresa)
        
        # Parsear datos del formulario desde PUT request
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            # Para FormData, necesitamos parsear manualmente
            from urllib.parse import parse_qs
            body = request.body.decode('utf-8')
            data = {}
            
            # Si viene como FormData, parseamos diferente
            if 'multipart/form-data' in request.content_type:
                # Django no maneja bien FormData en PUT, usaremos los archivos subidos
                import django.http.request
                # Trick para manejar FormData en PUT
                put_data = request.META.get('CONTENT_TYPE', '')
                if 'multipart' in put_data:
                    data = request.POST
                else:
                    # Parsear como query string
                    parsed = parse_qs(body)
                    data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
            else:
                # Parsear como query string normal
                parsed = parse_qs(body)
                data = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        
        # Validar campos requeridos
        if not data.get('nombre_vacante') or not data.get('fecha_expiracion'):
            return JsonResponse({'success': False, 'message': 'Faltan campos requeridos'})
        
        # Procesar sueldo
        sueldo = None
        if data.get('sueldo'):
            try:
                sueldo = Decimal(str(data.get('sueldo')))
            except (InvalidOperation, ValueError):
                return JsonResponse({'success': False, 'message': 'Sueldo inválido'})
        
        # Procesar edades
        edad_min = None
        edad_max = None
        if data.get('edad_min'):
            try:
                edad_min = int(data.get('edad_min'))
            except (ValueError, TypeError):
                pass
        
        if data.get('edad_max'):
            try:
                edad_max = int(data.get('edad_max'))
            except (ValueError, TypeError):
                pass
        
        # Validar fechas
        try:
            fecha_expiracion = datetime.strptime(str(data.get('fecha_expiracion')), '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'message': 'Fecha de expiración inválida'})
        
        # Actualizar la vacante
        vacante.nombre_vacante = data.get('nombre_vacante')
        vacante.sueldo = sueldo
        vacante.fecha_expiracion = fecha_expiracion
        vacante.area_desempeno = data.get('area_desempeno', '')
        vacante.descripcion_actividades = data.get('descripcion_actividades', '')
        vacante.edad_min = edad_min
        vacante.edad_max = edad_max
        vacante.titulo_requerido = data.get('titulo_requerido', '')
        vacante.tipo_vacante = data.get('tipo_vacante', 'Tiempo completo')
        vacante.delegacion = data.get('delegacion', '')
        vacante.nivel_academico = data.get('nivel_academico', '')
        vacante.estado_civil = data.get('estado_civil', 'Indistinto')
        vacante.personas_discapacidad = data.get('personas_discapacidad') in ['on', 'true', True]
        vacante.adultos_mayores = data.get('adultos_mayores') in ['on', 'true', True]
        vacante.vacante_mujer = data.get('vacante_mujer') in ['on', 'true', True]
        
        vacante.save()
        
        return JsonResponse({'success': True, 'message': 'Vacante actualizada exitosamente'})
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al actualizar vacante: {str(e)}'})

@csrf_exempt
@require_http_methods(["DELETE"])
def eliminar_vacante(request, id):
    """
    Vista para eliminar una vacante
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        vacante = get_object_or_404(Vacante, id=id, empresa=empresa)
        
        # Eliminar la vacante
        vacante.delete()
        
        return JsonResponse({'success': True, 'message': 'Vacante eliminada exitosamente'})
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al eliminar vacante: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
def toggle_vacante(request, id):
    """
    Vista para activar/pausar una vacante
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        vacante = get_object_or_404(Vacante, id=id, empresa=empresa)
        
        # Obtener el estado deseado
        data = json.loads(request.body)
        nuevo_estado = data.get('active', not vacante.activa)
        
        # Actualizar estado
        vacante.activa = nuevo_estado
        vacante.save()
        
        estado_texto = 'activada' if nuevo_estado else 'pausada'
        return JsonResponse({'success': True, 'message': f'Vacante {estado_texto} exitosamente'})
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al cambiar estado de vacante: {str(e)}'})

# Reemplazar la función aplicaciones_vacante en trabajos/views.py

def aplicaciones_vacante(request, id):
    """
    Vista para obtener las aplicaciones de una vacante con información completa
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        vacante = get_object_or_404(Vacante, id=id, empresa=empresa)
        
        # Obtener aplicaciones con información completa del usuario
        aplicaciones = UsuarioVacante.objects.filter(
            vacante=vacante
        ).select_related('usuario', 'usuario__usuarioperfil').order_by('-fecha_aplicacion')
        
        # Formatear datos con información más completa
        data = {
            'vacante_nombre': vacante.nombre_vacante,
            'total_aplicaciones': aplicaciones.count(),
            'applications': []
        }
        
        for app in aplicaciones:
            # Información básica del usuario
            usuario_data = {
                'id': app.usuario.id,
                'first_name': app.usuario.first_name,
                'last_name': app.usuario.last_name,
                'email': app.usuario.email,
                'username': app.usuario.username,
            }
            
            # Información del perfil si existe
            if hasattr(app.usuario, 'usuarioperfil') and app.usuario.usuarioperfil:
                perfil = app.usuario.usuarioperfil
                
                # Calcular edad
                edad = None
                if perfil.fecha_nacimiento:
                    from datetime import date
                    today = date.today()
                    edad = today.year - perfil.fecha_nacimiento.year
                    if today.month < perfil.fecha_nacimiento.month or (today.month == perfil.fecha_nacimiento.month and today.day < perfil.fecha_nacimiento.day):
                        edad -= 1
                
                usuario_data.update({
                    'nombre_completo': perfil.nombre_completo,
                    'telefono': perfil.telefono or 'No especificado',
                    'nivel_academico': perfil.nivel_academico or 'No especificado',
                    'sexo': perfil.get_sexo_display() if perfil.sexo else 'No especificado',
                    'edad': f"{edad} años" if edad else 'No especificada',
                    'curp': perfil.curp or 'No especificada',
                    'cv_url': perfil.curriculum_vitae.url if perfil.curriculum_vitae else None,
                    'cv_nombre': perfil.curriculum_vitae.name.split('/')[-1] if perfil.curriculum_vitae else None,
                    'documento_url': perfil.documento_identificacion.url if perfil.documento_identificacion else None,
                    'documento_nombre': perfil.documento_identificacion.name.split('/')[-1] if perfil.documento_identificacion else None,
                })
            else:
                usuario_data.update({
                    'nombre_completo': f"{app.usuario.first_name} {app.usuario.last_name}",
                    'telefono': 'No especificado',
                    'nivel_academico': 'No especificado',
                    'sexo': 'No especificado',
                    'edad': 'No especificada',
                    'curp': 'No especificada',
                    'cv_url': None,
                    'cv_nombre': None,
                    'documento_url': None,
                    'documento_nombre': None,
                })
            
            # Agregar información de la aplicación
            aplicacion_data = {
                'id': app.id,
                'usuario': usuario_data,
                'fecha_aplicacion': app.fecha_aplicacion.strftime('%d/%m/%Y %H:%M'),
                'estado': app.estado,
            }
            
            data['applications'].append(aplicacion_data)
        
        return JsonResponse(data)
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al obtener aplicaciones: {str(e)}'})

@csrf_exempt
@require_http_methods(["POST"])
def actualizar_estado_aplicacion(request, aplicacion_id):
    """
    Vista para actualizar el estado de una aplicación
    """
    # Verificar sesión de empresa
    empresa_id = request.session.get('empresa_id')
    if not empresa_id:
        return JsonResponse({'success': False, 'message': 'No hay sesión de empresa'})
    
    try:
        empresa = Empresa.objects.get(id=empresa_id, activo=True)
        
        from .models import UsuarioVacante
        aplicacion = get_object_or_404(UsuarioVacante, id=aplicacion_id, vacante__empresa=empresa)
        
        # Obtener nuevo estado
        data = json.loads(request.body)
        nuevo_estado = data.get('estado')
        
        # Validar estado
        estados_validos = ['Pendiente', 'En revisión', 'Aceptado', 'Rechazado']
        if nuevo_estado not in estados_validos:
            return JsonResponse({'success': False, 'message': 'Estado inválido'})
        
        # Actualizar estado
        aplicacion.estado = nuevo_estado
        aplicacion.save()
        
        return JsonResponse({'success': True, 'message': f'Estado actualizado a {nuevo_estado}'})
        
    except Empresa.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Empresa no encontrada'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al actualizar estado: {str(e)}'})

def cerrar_sesion_empresa(request):
    """
    Vista para cerrar sesión de empresa
    """
    # Limpiar sesión
    if 'empresa_id' in request.session:
        del request.session['empresa_id']
    if 'empresa_nombre' in request.session:
        del request.session['empresa_nombre']
    
    messages.success(request, 'Sesión cerrada exitosamente')
    return redirect('empresas')


  # Agregar esta vista de usuarios que apliquen a la vacante
def login_usuario(request):
    """
    Vista para login y registro de usuarios
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'login':
            # Procesar login
            email = request.POST.get('email')
            password = request.POST.get('password')
            
            try:
                # Buscar usuario por email
                user = User.objects.get(email=email, is_active=True)
                
                # Autenticar con username y password
                authenticated_user = authenticate(request, username=user.username, password=password)
                
                if authenticated_user:
                 login(request, authenticated_user)
                 messages.success(request, f'¡Bienvenido {user.first_name}!')
    
                 # Redirigir al perfil del usuario después del login
                 next_url = request.GET.get('next', 'perfil_usuario')
                 return redirect(next_url)
                else:
                    messages.error(request, 'Contraseña incorrecta')
                    
            except User.DoesNotExist:
                messages.error(request, 'No existe una cuenta con este correo electrónico')
                
        elif action == 'register':
            # Procesar registro
            try:
                # Obtener datos del formulario
                nombre_completo = request.POST.get('nombre_completo', '').strip()
                curp = request.POST.get('curp', '').strip().upper()
                sexo = request.POST.get('sexo')
                telefono = request.POST.get('telefono', '').strip()
                fecha_nacimiento = request.POST.get('fecha_nacimiento')
                nivel_academico = request.POST.get('nivel_academico')
                email = request.POST.get('email', '').strip().lower()
                password = request.POST.get('password')
                password_confirm = request.POST.get('password_confirm')
                documento = request.FILES.get('documento')
                
                # Validaciones básicas
                errores = []
                
                if not nombre_completo:
                    errores.append('El nombre completo es requerido')
                
                if not curp:
                    errores.append('La CURP es requerida')
                elif len(curp) != 18:
                    errores.append('La CURP debe tener 18 caracteres')
                elif not re.match(r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}$', curp):
                    errores.append('Formato de CURP inválido')
                
                if not email:
                    errores.append('El correo electrónico es requerido')
                elif User.objects.filter(email=email).exists():
                    errores.append('Ya existe una cuenta con este correo electrónico')
                
                if not password:
                    errores.append('La contraseña es requerida')
                elif len(password) < 8:
                    errores.append('La contraseña debe tener al menos 8 caracteres')
                elif password != password_confirm:
                    errores.append('Las contraseñas no coinciden')
                
                if not sexo:
                    errores.append('El sexo es requerido')
                
                if not telefono:
                    errores.append('El teléfono es requerido')
                elif not re.match(r'^\+?1?\d{9,15}$', telefono):
                    errores.append('Formato de teléfono inválido')
                
                if not fecha_nacimiento:
                    errores.append('La fecha de nacimiento es requerida')
                else:
                    try:
                        fecha_nac = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
                        # Validar que sea mayor de edad (18 años)
                        from django.utils import timezone
                        edad = (timezone.now().date() - fecha_nac).days // 365
                        if edad < 18:
                            errores.append('Debes ser mayor de 18 años para registrarte')
                    except ValueError:
                        errores.append('Fecha de nacimiento inválida')
                
                if not nivel_academico:
                    errores.append('El nivel académico es requerido')
                
                if not documento:
                    errores.append('El documento de identificación es requerido')
                elif documento.size > 5 * 1024 * 1024:  # 5MB
                    errores.append('El archivo no puede pesar más de 5MB')
                
                # Verificar si ya existe usuario con esta CURP
                if curp and UsuarioPerfil.objects.filter(curp=curp).exists():
                    errores.append('Ya existe un usuario registrado con esta CURP')
                
                # Si hay errores, mostrarlos
                if errores:
                    for error in errores:
                        messages.error(request, error)
                    return render(request, 'loginusuario.html')
                
                # Separar nombres
                nombres_partes = nombre_completo.split()
                if len(nombres_partes) < 3:
                    errores.append('Debes ingresar nombre(s) y apellidos completos')
                    for error in errores:
                        messages.error(request, error)
                    return render(request, 'loginusuario.html')
                
                # Asumir que los últimos dos son apellidos
                apellido_materno = nombres_partes[-1]
                apellido_paterno = nombres_partes[-2]
                nombres = ' '.join(nombres_partes[:-2])
                
                # Crear username único basado en email
                username = email.split('@')[0]
                counter = 1
                original_username = username
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                # Crear usuario de Django
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=nombres,
                    last_name=f"{apellido_paterno} {apellido_materno}"
                )
                
                # Actualizar el perfil de usuario (creado automáticamente por signal)
                perfil = user.usuarioperfil
                perfil.nombres = nombres
                perfil.apellido_paterno = apellido_paterno
                perfil.apellido_materno = apellido_materno
                perfil.curp = curp
                perfil.sexo = sexo
                perfil.telefono = telefono
                perfil.fecha_nacimiento = fecha_nac
                perfil.nivel_academico = nivel_academico
                perfil.documento_identificacion = documento
                perfil.save()
                
                messages.success(request, '¡Registro exitoso! Ya puedes iniciar sesión')
                return redirect('login_usuario')
                
            except Exception as e:
                messages.error(request, f'Error en el registro: {str(e)}')
    
    # GET request - mostrar formulario
    return render(request, 'loginusuario.html')

# Actualizar la vista perfil_usuario en trabajos/views.py

@login_required
def perfil_usuario(request):
    """
    Vista para el perfil del usuario
    """
    try:
        perfil = request.user.usuarioperfil
    except UsuarioPerfil.DoesNotExist:
        # Crear perfil si no existe
        perfil = UsuarioPerfil.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Actualizar perfil
        try:
            # Obtener datos del formulario
            nombres = request.POST.get('nombres', '').strip()
            apellido_paterno = request.POST.get('apellido_paterno', '').strip()
            apellido_materno = request.POST.get('apellido_materno', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            nivel_academico = request.POST.get('nivel_academico')
            
            # Validaciones
            if not nombres or not apellido_paterno or not apellido_materno:
                messages.error(request, 'Todos los nombres son requeridos')
            else:
                # Actualizar datos básicos
                perfil.nombres = nombres
                perfil.apellido_paterno = apellido_paterno
                perfil.apellido_materno = apellido_materno
                perfil.telefono = telefono
                if nivel_academico:
                    perfil.nivel_academico = nivel_academico
                
                # Actualizar archivos si se suben nuevos
                if 'documento_identificacion' in request.FILES:
                    perfil.documento_identificacion = request.FILES['documento_identificacion']
                
                if 'curriculum_vitae' in request.FILES:
                    perfil.curriculum_vitae = request.FILES['curriculum_vitae']
                
                perfil.save()
                
                # Actualizar también el usuario de Django
                request.user.first_name = nombres
                request.user.last_name = f"{apellido_paterno} {apellido_materno}"
                request.user.save()
                
                messages.success(request, 'Perfil actualizado exitosamente')
                
        except Exception as e:
            messages.error(request, f'Error al actualizar perfil: {str(e)}')
    
    # Obtener aplicaciones recientes (últimas 3)
    aplicaciones_recientes = UsuarioVacante.objects.filter(
        usuario=request.user
    ).select_related('vacante', 'vacante__empresa').order_by('-fecha_aplicacion')[:3]
    
    # Obtener estadísticas
    total_aplicaciones = UsuarioVacante.objects.filter(usuario=request.user).count()
    aplicaciones_pendientes = UsuarioVacante.objects.filter(
        usuario=request.user, 
        estado__in=['Pendiente', 'En revisión']
    ).count()
    aplicaciones_aceptadas = UsuarioVacante.objects.filter(
        usuario=request.user, 
        estado='Aceptado'
    ).count()
    
    # Calcular porcentaje de completitud del perfil
    campos_completos = 0
    campos_totales = 8
    
    if perfil.nombres:
        campos_completos += 1
    if perfil.apellido_paterno:
        campos_completos += 1
    if perfil.apellido_materno:
        campos_completos += 1
    if perfil.curp:
        campos_completos += 1
    if perfil.telefono:
        campos_completos += 1
    if perfil.fecha_nacimiento:
        campos_completos += 1
    if perfil.nivel_academico:
        campos_completos += 1
    if perfil.documento_identificacion:
        campos_completos += 1
    
    porcentaje_completitud = round((campos_completos / campos_totales) * 100)
    
    context = {
        'perfil': perfil,
        'aplicaciones_recientes': aplicaciones_recientes,
        'total_aplicaciones': total_aplicaciones,
        'aplicaciones_pendientes': aplicaciones_pendientes,
        'aplicaciones_aceptadas': aplicaciones_aceptadas,
        'porcentaje_completitud': porcentaje_completitud,
    }
    
    return render(request, 'perfil_usuario.html', context)

@login_required
def aplicar_vacante(request, vacante_id):
    """
    Vista para aplicar a una vacante
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Método no permitido'})
    
    try:
        vacante = get_object_or_404(Vacante, id=vacante_id, activa=True)
        
        # Verificar si ya aplicó
        if UsuarioVacante.objects.filter(usuario=request.user, vacante=vacante).exists():
            return JsonResponse({'success': False, 'message': 'Ya has aplicado a esta vacante'})
        
        # Verificar si la vacante sigue vigente
        if not vacante.esta_vigente:
            return JsonResponse({'success': False, 'message': 'Esta vacante ya expiró'})
        
        # Verificar restricciones de género
        if vacante.vacante_mujer and hasattr(request.user, 'usuarioperfil'):
            if request.user.usuarioperfil.sexo != 'F':
                return JsonResponse({'success': False, 'message': 'Esta vacante es exclusiva para mujeres'})
        
        # Verificar que tenga perfil completo
        try:
            perfil = request.user.usuarioperfil
            if not perfil.nombres or not perfil.apellido_paterno:
                return JsonResponse({
                    'success': False, 
                    'message': 'Debes completar tu perfil antes de aplicar a vacantes'
                })
        except UsuarioPerfil.DoesNotExist:
            return JsonResponse({
                'success': False, 
                'message': 'Debes completar tu perfil antes de aplicar a vacantes'
            })
        
        # Crear aplicación
        aplicacion = UsuarioVacante.objects.create(
            usuario=request.user,
            vacante=vacante,
            estado='Pendiente'
        )
        
        return JsonResponse({
            'success': True, 
            'message': '¡Has aplicado exitosamente a esta vacante! La empresa podrá ver tu perfil y CV.'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error al aplicar: {str(e)}'})

@login_required
def mis_aplicaciones(request):
    """
    Vista para mostrar las aplicaciones del usuario
    """
    aplicaciones = UsuarioVacante.objects.filter(
        usuario=request.user
    ).select_related('vacante', 'vacante__empresa').order_by('-fecha_aplicacion')
    
    # Paginación
    paginator = Paginator(aplicaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_aplicaciones': aplicaciones.count(),
    }
    
    return render(request, 'mis_aplicaciones.html', context)

def logout_usuario(request):
    """
    Vista para cerrar sesión de usuario
    """
    logout(request)
    messages.success(request, 'Has cerrado sesión exitosamente')
    return redirect('inicio')

def preguntas_frecuentes(request):
    """
    Vista para mostrar la página de preguntas frecuentes
    """
    context = {
        'titulo': 'Preguntas Frecuentes',
        'descripcion': 'Encuentra respuestas a las preguntas más comunes sobre el Sistema de Bolsa de Trabajo de Atizapán de Zaragoza'
    }
    return render(request, 'preguntasFrecuentes.html', context)