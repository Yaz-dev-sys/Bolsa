# trabajos/models.py
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, FileExtensionValidator

class TipoRegimen(models.Model):
    nombre_regimen = models.CharField(max_length=100, unique=True)
    
    def __str__(self):
        return self.nombre_regimen
    
    class Meta:
        db_table = 'tipo_regimen'
        verbose_name = 'Tipo de Régimen'
        verbose_name_plural = 'Tipos de Régimen'

class Documentos(models.Model):
    nombre_documento = models.CharField(max_length=150, unique=True)
    
    def __str__(self):
        return self.nombre_documento
    
    class Meta:
        db_table = 'documentos'
        verbose_name = 'Documento'
        verbose_name_plural = 'Documentos'

class RegimenDocumentos(models.Model):
    regimen = models.ForeignKey(TipoRegimen, on_delete=models.CASCADE)
    documento = models.ForeignKey(Documentos, on_delete=models.CASCADE)
    obligatorio = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'regimen_documentos'
        unique_together = ('regimen', 'documento')
        verbose_name = 'Documento por Régimen'
        verbose_name_plural = 'Documentos por Régimen'

class Empresa(models.Model):
    nombre_empresa = models.CharField(max_length=200)
    url_bolsa_trabajo = models.URLField(max_length=500, blank=True, null=True)
    correo_contacto = models.EmailField(max_length=100)
    logo_empresa = models.FileField(
        upload_to='logos_empresas/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif']),
        ]
    )
    carta_compromiso = models.FileField(
        upload_to='cartas_compromiso/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
        ]
    )
    correo_administrador = models.EmailField(max_length=100, unique=True)
    password = models.CharField(max_length=128)  # Se manejará con hash
    regimen = models.ForeignKey(TipoRegimen, on_delete=models.PROTECT)
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.nombre_empresa
    
    class Meta:
        db_table = 'empresas'
        verbose_name = 'Empresa'
        verbose_name_plural = 'Empresas'

class EmpresaDocumentos(models.Model):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    documento = models.ForeignKey(Documentos, on_delete=models.CASCADE)
    archivo = models.FileField(upload_to='documentos_empresas/')
    fecha_subida = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'empresa_documentos'
        unique_together = ('empresa', 'documento')
        verbose_name = 'Documento de Empresa'
        verbose_name_plural = 'Documentos de Empresas'

class UsuarioPerfil(models.Model):
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('Otro', 'Otro'),
    ]
    
    NIVEL_ACADEMICO_CHOICES = [
        ('Sin estudios', 'Sin estudios'),
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
        ('Preparatoria', 'Preparatoria'),
        ('Técnico', 'Técnico'),
        ('Licenciatura', 'Licenciatura'),
        ('Maestría', 'Maestría'),
        ('Doctorado', 'Doctorado'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=50)
    apellido_materno = models.CharField(max_length=50)
    curp = models.CharField(
        max_length=18, 
        unique=True, 
        blank=True, 
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z]{4}[0-9]{6}[HM][A-Z]{5}[0-9A-Z]{2}$',
                message='CURP debe tener el formato correcto'
            )
        ]
    )
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES)
    telefono = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Número de teléfono debe tener entre 9 y 15 dígitos'
            )
        ]
    )
    fecha_nacimiento = models.DateField(blank=True, null=True)
    nivel_academico = models.CharField(
        max_length=20, 
        choices=NIVEL_ACADEMICO_CHOICES,
        blank=True
    )
    documento_identificacion = models.FileField(
        upload_to='documentos_usuarios/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'jpg', 'jpeg', 'png']),
        ]
    )
    curriculum_vitae = models.FileField(
        upload_to='curriculum/',
        blank=True,
        null=True,
        validators=[
            FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx']),
        ]
    )
    activo = models.BooleanField(default=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"
    
    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellido_paterno} {self.apellido_materno}"
    
    class Meta:
        db_table = 'usuario_perfil'
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuarios'

class Vacante(models.Model):
    TIPO_VACANTE_CHOICES = [
        ('Tiempo completo', 'Tiempo completo'),
        ('Medio tiempo', 'Medio tiempo'),
        ('Por proyecto', 'Por proyecto'),
        ('Temporal', 'Temporal'),
        ('Prácticas', 'Prácticas'),
    ]
    
    NIVEL_ACADEMICO_CHOICES = [
        ('Sin estudios', 'Sin estudios'),
        ('Primaria', 'Primaria'),
        ('Secundaria', 'Secundaria'),
        ('Preparatoria', 'Preparatoria'),
        ('Técnico', 'Técnico'),
        ('Licenciatura', 'Licenciatura'),
        ('Maestría', 'Maestría'),
        ('Doctorado', 'Doctorado'),
    ]
    
    ESTADO_CIVIL_CHOICES = [
        ('Soltero', 'Soltero'),
        ('Casado', 'Casado'),
        ('Divorciado', 'Divorciado'),
        ('Viudo', 'Viudo'),
        ('Unión libre', 'Unión libre'),
        ('Indistinto', 'Indistinto'),
    ]
    
    nombre_vacante = models.CharField(max_length=200)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    sueldo = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fecha_expiracion = models.DateField()
    area_desempeno = models.CharField(max_length=150, blank=True)
    descripcion_actividades = models.TextField(blank=True)
    edad_min = models.IntegerField(blank=True, null=True)
    edad_max = models.IntegerField(blank=True, null=True)
    titulo_requerido = models.CharField(max_length=200, blank=True)
    tipo_vacante = models.CharField(
        max_length=20, 
        choices=TIPO_VACANTE_CHOICES, 
        default='Tiempo completo'
    )
    delegacion = models.CharField(max_length=100, blank=True)
    nivel_academico = models.CharField(
        max_length=20, 
        choices=NIVEL_ACADEMICO_CHOICES,
        blank=True
    )
    estado_civil = models.CharField(
        max_length=15, 
        choices=ESTADO_CIVIL_CHOICES, 
        default='Indistinto'
    )
    personas_discapacidad = models.BooleanField(default=False)
    adultos_mayores = models.BooleanField(default=False)
    vacante_mujer = models.BooleanField(default=False)
    activa = models.BooleanField(default=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.nombre_vacante} - {self.empresa.nombre_empresa}"
    
    @property
    def esta_vigente(self):
        from django.utils import timezone
        return self.fecha_expiracion >= timezone.now().date()
    
    class Meta:
        db_table = 'vacantes'
        verbose_name = 'Vacante'
        verbose_name_plural = 'Vacantes'
        ordering = ['-fecha_publicacion']

class UsuarioVacante(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('En revisión', 'En revisión'),
        ('Aceptado', 'Aceptado'),
        ('Rechazado', 'Rechazado'),
    ]
    
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    vacante = models.ForeignKey(Vacante, on_delete=models.CASCADE)
    fecha_aplicacion = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='Pendiente')
    
    def __str__(self):
        return f"{self.usuario.username} - {self.vacante.nombre_vacante}"
    
    class Meta:
        db_table = 'usuario_vacante'
        unique_together = ('usuario', 'vacante')
        verbose_name = 'Aplicación a Vacante'
        verbose_name_plural = 'Aplicaciones a Vacantes'
        ordering = ['-fecha_aplicacion']

# Signals para crear automáticamente el perfil de usuario
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def crear_perfil_usuario(sender, instance, created, **kwargs):
    if created:
        UsuarioPerfil.objects.create(user=instance)

@receiver(post_save, sender=User)
def guardar_perfil_usuario(sender, instance, **kwargs):
    if hasattr(instance, 'usuarioperfil'):
        instance.usuarioperfil.save()