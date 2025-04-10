from django.db import models
from django.contrib.auth.models import AbstractUser


class Rol(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Persona(models.Model):
    nombre_completo = models.CharField(max_length=150)
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=255)

    class Meta:
        abstract = True
    

class Usuario(AbstractUser, Persona):
    correo = models.EmailField(unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)  

    USERNAME_FIELD = 'correo'  
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.correo

    @classmethod
    def obtener_clientes(cls):
        cliente_rol = Rol.objects.get(nombre="cliente")
        return cls.objects.filter(rol=cliente_rol)

    @classmethod
    def obtener_vendedores(cls):
        vendedor_rol = Rol.objects.get(nombre="vendedor")
        return cls.objects.filter(rol=vendedor_rol)