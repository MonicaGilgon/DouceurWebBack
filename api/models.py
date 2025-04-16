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
    document_number = models.CharField(max_length=50, blank=True, null=True)

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

class CategoriaArticulo(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    


class CategoriaProductoBase(models.Model):
    nombre = models.CharField(max_length=100)
    estado = models.BooleanField(default=True)
    def __str__(self):
        return self.nombre

class Articulo(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    categoria = models.ForeignKey(CategoriaArticulo, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    

class Order(models.Model):
    STATUS_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
        ('cancelado', 'Cancelado'),
    ]
    user = models.ForeignKey('api.Usuario', on_delete=models.CASCADE, related_name='orders')
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')

    def __str__(self):
        return f"Order {self.id} by {self.user.correo}"

    class Meta:
        ordering = ['-order_date']  # Ordenar por order_date descendente por defecto

class OrderItem(models.Model):
     order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
     articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)



