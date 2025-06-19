# bolsaTrabajo/urls.py - ACTUALIZADO
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from trabajos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('vacantes/', views.lista_vacantes, name='lista_vacantes'),
    path('vacantes/mujeres/', views.vacantes_mujeres, name='vacantes_mujeres'),
    path('vacante/<int:id>/', views.detalle_vacante, name='detalle_vacante'),
    
    # URLs de usuarios
    path('login/', views.login_usuario, name='login_usuario'),
    path('logout/', views.logout_usuario, name='logout_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('mis-aplicaciones/', views.mis_aplicaciones, name='mis_aplicaciones'),
    path('aplicar/<int:vacante_id>/', views.aplicar_vacante, name='aplicar_vacante'),
    
    # URLs de empresas
    path('empresas/', views.login_empresa, name='empresas'),
    path('empresas/dashboard/', views.dashboard_empresa, name='dashboard_empresa'),
    path('empresas/documentos/', views.get_documentos_regimen, name='get_documentos_regimen'),
    path('empresas/logout/', views.cerrar_sesion_empresa, name='cerrar_sesion_empresa'),
    
    # URLs para CRUD de vacantes (Dashboard)
    path('dashboard/vacante/create/', views.crear_vacante, name='crear_vacante'),
    path('dashboard/vacante/<int:id>/', views.obtener_vacante, name='obtener_vacante'),
    path('dashboard/vacante/<int:id>/update/', views.actualizar_vacante, name='actualizar_vacante'),
    path('dashboard/vacante/<int:id>/delete/', views.eliminar_vacante, name='eliminar_vacante'),
    path('dashboard/vacante/<int:id>/toggle/', views.toggle_vacante, name='toggle_vacante'),
    path('dashboard/vacante/<int:id>/applications/', views.aplicaciones_vacante, name='aplicaciones_vacante'),
    path('dashboard/aplicacion/<int:aplicacion_id>/update/', views.actualizar_estado_aplicacion, name='actualizar_estado_aplicacion'),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)# bolsaTrabajo/urls.py - ACTUALIZADO
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from trabajos import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.inicio, name='inicio'),
    path('vacantes/', views.lista_vacantes, name='lista_vacantes'),
    path('vacantes/mujeres/', views.vacantes_mujeres, name='vacantes_mujeres'),
    path('vacante/<int:id>/', views.detalle_vacante, name='detalle_vacante'),
    
    # URLs de usuarios
    path('login/', views.login_usuario, name='login_usuario'),
    path('logout/', views.logout_usuario, name='logout_usuario'),
    path('perfil/', views.perfil_usuario, name='perfil_usuario'),
    path('mis-aplicaciones/', views.mis_aplicaciones, name='mis_aplicaciones'),
    path('aplicar/<int:vacante_id>/', views.aplicar_vacante, name='aplicar_vacante'),
    
    # URLs de empresas
    path('empresas/', views.login_empresa, name='empresas'),
    path('empresas/dashboard/', views.dashboard_empresa, name='dashboard_empresa'),
    path('empresas/documentos/', views.get_documentos_regimen, name='get_documentos_regimen'),
    path('empresas/logout/', views.cerrar_sesion_empresa, name='cerrar_sesion_empresa'),
    
    # URLs para CRUD de vacantes (Dashboard)
    path('dashboard/vacante/create/', views.crear_vacante, name='crear_vacante'),
    path('dashboard/vacante/<int:id>/', views.obtener_vacante, name='obtener_vacante'),
    path('dashboard/vacante/<int:id>/update/', views.actualizar_vacante, name='actualizar_vacante'),
    path('dashboard/vacante/<int:id>/delete/', views.eliminar_vacante, name='eliminar_vacante'),
    path('dashboard/vacante/<int:id>/toggle/', views.toggle_vacante, name='toggle_vacante'),
    path('dashboard/vacante/<int:id>/applications/', views.aplicaciones_vacante, name='aplicaciones_vacante'),
    path('dashboard/aplicacion/<int:aplicacion_id>/update/', views.actualizar_estado_aplicacion, name='actualizar_estado_aplicacion'),

    # Preguntas Frecuentes
    path('preguntas-frecuentes/', views.preguntas_frecuentes, name='preguntasFrecuentes'),
]

# Servir archivos multimedia en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)