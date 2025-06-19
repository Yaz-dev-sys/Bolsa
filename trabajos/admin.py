# trabajos/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    TipoRegimen, Documentos, RegimenDocumentos, 
    Empresa, EmpresaDocumentos, UsuarioPerfil, 
    Vacante, UsuarioVacante
)

# =============================================
# CONFIGURACIÓN PARA TIPO REGIMEN
# =============================================

@admin.register(TipoRegimen)
class TipoRegimenAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_regimen')
    search_fields = ('nombre_regimen',)
    ordering = ('nombre_regimen',)

# =============================================
# CONFIGURACIÓN PARA DOCUMENTOS
# =============================================

@admin.register(Documentos)
class DocumentosAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_documento')
    search_fields = ('nombre_documento',)
    ordering = ('nombre_documento',)

# =============================================
# CONFIGURACIÓN PARA REGIMEN DOCUMENTOS
# =============================================

@admin.register(RegimenDocumentos)
class RegimenDocumentosAdmin(admin.ModelAdmin):
    list_display = ('regimen', 'documento', 'obligatorio')
    list_filter = ('obligatorio', 'regimen')
    search_fields = ('regimen__nombre_regimen', 'documento__nombre_documento')
    ordering = ('regimen', 'documento')

# =============================================
# CONFIGURACIÓN PARA EMPRESAS
# =============================================

class EmpresaDocumentosInline(admin.TabularInline):
    model = EmpresaDocumentos
    extra = 1
    readonly_fields = ('fecha_subida',)

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ('nombre_empresa', 'correo_administrador', 'regimen', 'activo', 'fecha_registro')
    list_filter = ('activo', 'regimen', 'fecha_registro')
    search_fields = ('nombre_empresa', 'correo_administrador', 'correo_contacto')
    readonly_fields = ('fecha_registro',)
    ordering = ('-fecha_registro',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_empresa', 'correo_contacto', 'url_bolsa_trabajo')
        }),
        ('Administración', {
            'fields': ('correo_administrador', 'password')
        }),
        ('Documentos', {
            'fields': ('logo_empresa', 'carta_compromiso')
        }),
        ('Configuración', {
            'fields': ('regimen', 'activo', 'fecha_registro')
        }),
    )
    
    inlines = [EmpresaDocumentosInline]

# =============================================
# CONFIGURACIÓN PARA EMPRESA DOCUMENTOS
# =============================================

@admin.register(EmpresaDocumentos)
class EmpresaDocumentosAdmin(admin.ModelAdmin):
    list_display = ('empresa', 'documento', 'fecha_subida')
    list_filter = ('fecha_subida', 'documento')
    search_fields = ('empresa__nombre_empresa', 'documento__nombre_documento')
    readonly_fields = ('fecha_subida',)
    ordering = ('-fecha_subida',)

# =============================================
# CONFIGURACIÓN PARA PERFIL DE USUARIO
# =============================================

class UsuarioPerfilInline(admin.StackedInline):
    model = UsuarioPerfil
    can_delete = False
    verbose_name_plural = 'Perfil'
    readonly_fields = ('fecha_registro',)
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('nombres', 'apellido_paterno', 'apellido_materno', 'curp', 'sexo')
        }),
        ('Contacto', {
            'fields': ('telefono', 'fecha_nacimiento')
        }),
        ('Académico', {
            'fields': ('nivel_academico',)
        }),
        ('Documentos', {
            'fields': ('documento_identificacion', 'curriculum_vitae')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_registro')
        }),
    )

# Extender el UserAdmin para incluir el perfil
class UserAdmin(BaseUserAdmin):
    inlines = (UsuarioPerfilInline,)
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)

# Re-registrar UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(UsuarioPerfil)
class UsuarioPerfilAdmin(admin.ModelAdmin):
    list_display = ('nombre_completo', 'user', 'sexo', 'telefono', 'nivel_academico', 'activo', 'tiene_cv')
    list_filter = ('sexo', 'nivel_academico', 'activo', 'fecha_registro')
    search_fields = ('nombres', 'apellido_paterno', 'apellido_materno', 'user__username', 'user__email', 'curp')
    readonly_fields = ('fecha_registro',)
    ordering = ('-fecha_registro',)
    
    fieldsets = (
        ('Usuario Django', {
            'fields': ('user',)
        }),
        ('Información Personal', {
            'fields': ('nombres', 'apellido_paterno', 'apellido_materno', 'curp', 'sexo')
        }),
        ('Contacto', {
            'fields': ('telefono', 'fecha_nacimiento')
        }),
        ('Académico', {
            'fields': ('nivel_academico',)
        }),
        ('Documentos', {
            'fields': ('documento_identificacion', 'curriculum_vitae')
        }),
        ('Estado', {
            'fields': ('activo', 'fecha_registro')
        }),
    )
    
    def tiene_cv(self, obj):
        return bool(obj.curriculum_vitae)
    tiene_cv.boolean = True
    tiene_cv.short_description = 'Tiene CV'

# =============================================
# CONFIGURACIÓN PARA VACANTES
# =============================================

class UsuarioVacanteInline(admin.TabularInline):
    model = UsuarioVacante
    extra = 0
    readonly_fields = ('fecha_aplicacion',)
    fields = ('usuario', 'estado', 'fecha_aplicacion')

@admin.register(Vacante)
class VacanteAdmin(admin.ModelAdmin):
    list_display = ('nombre_vacante', 'empresa', 'sueldo', 'fecha_expiracion', 'vacante_mujer', 'activa', 'total_aplicaciones')
    list_filter = ('activa', 'vacante_mujer', 'tipo_vacante', 'nivel_academico', 'empresa', 'fecha_publicacion')
    search_fields = ('nombre_vacante', 'empresa__nombre_empresa', 'area_desempeno', 'delegacion')
    readonly_fields = ('fecha_publicacion',)
    ordering = ('-fecha_publicacion',)
    date_hierarchy = 'fecha_publicacion'
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_vacante', 'empresa', 'area_desempeno', 'delegacion')
        }),
        ('Detalles del Trabajo', {
            'fields': ('descripcion_actividades', 'sueldo', 'tipo_vacante')
        }),
        ('Requisitos', {
            'fields': ('titulo_requerido', 'nivel_academico', 'edad_min', 'edad_max', 'estado_civil')
        }),
        ('Inclusión', {
            'fields': ('personas_discapacidad', 'adultos_mayores', 'vacante_mujer')
        }),
        ('Estado', {
            'fields': ('fecha_expiracion', 'activa', 'fecha_publicacion')
        }),
    )
    
    inlines = [UsuarioVacanteInline]
    
    def total_aplicaciones(self, obj):
        return obj.usuariovacante_set.count()
    total_aplicaciones.short_description = 'Aplicaciones'

# =============================================
# CONFIGURACIÓN PARA APLICACIONES A VACANTES
# =============================================

@admin.register(UsuarioVacante)
class UsuarioVacanteAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'vacante', 'estado', 'fecha_aplicacion')
    list_filter = ('estado', 'fecha_aplicacion', 'vacante__empresa')
    search_fields = (
        'usuario__username', 
        'usuario__email',
        'usuario__usuarioperfil__nombres',
        'usuario__usuarioperfil__apellido_paterno',
        'vacante__nombre_vacante',
        'vacante__empresa__nombre_empresa'
    )
    readonly_fields = ('fecha_aplicacion',)
    ordering = ('-fecha_aplicacion',)
    date_hierarchy = 'fecha_aplicacion'
    
    fieldsets = (
        ('Aplicación', {
            'fields': ('usuario', 'vacante', 'estado')
        }),
        ('Información', {
            'fields': ('fecha_aplicacion',)
        }),
    )

# =============================================
# PERSONALIZACIÓN DEL ADMIN
# =============================================

# Personalizar el título del admin
admin.site.site_header = "BOLSA ATIZAPAN - Administración"
admin.site.site_title = "BOLSA ATIZAPAN Admin"
admin.site.index_title = "Panel de Administración"