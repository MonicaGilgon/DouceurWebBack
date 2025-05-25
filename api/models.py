from django.db import models
from django.contrib.auth.models import AbstractUser
from cloudinary_storage.storage import MediaCloudinaryStorage

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
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    correo = models.EmailField(unique=True)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, null=True)
    estado = models.BooleanField(default=True)
    document_number = models.CharField(max_length=50, blank=True, null=True)

    USERNAME_FIELD = 'correo'
    REQUIRED_FIELDS = ['username']

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
    categoriaArticulo = models.ForeignKey(CategoriaArticulo, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
    

class Order(models.Model):
    STATUS_CHOICES = (
        ('pendiente', 'Pendiente'),
        ('pago_confirmado', 'Pago Confirmado'),
        ('rechazado', 'Rechazado'),
        ('en_preparacion', 'En Preparación'),
        ('enviado', 'Enviado'),
        ('entregado', 'Entregado'),
    )
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendiente')
    payment_proof = models.FileField(upload_to='payment_proofs/', null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.id} - {self.user.nombre_completo}"

    class Meta:
        ordering = ['-order_date']  # Ordenar por order_date descendente por defecto


class ProductoBase(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    precio = models.FloatField()
    imagen = models.ImageField(storage=MediaCloudinaryStorage(), null=True, blank=True)
    estado = models.BooleanField(default=True)
    categoriaProductoBase = models.ForeignKey(CategoriaProductoBase, on_delete=models.CASCADE)
    articulos = models.ManyToManyField('Articulo', blank=True)
    categorias_articulo = models.ManyToManyField(CategoriaArticulo, blank=True, related_name='productos')

    def __str__(self):
        return self.nombre
    
class ProductoBaseFoto(models.Model):
    productoBase = models.ForeignKey(ProductoBase, on_delete=models.CASCADE, related_name='fotos')
    foto = models.ImageField(storage=MediaCloudinaryStorage())
    def __str__(self):
        return f"Foto de {self.productoBase.nombre}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    producto = models.ForeignKey(ProductoBase, on_delete=models.CASCADE)  # Cambiado de articulo a producto
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en Pedido #{self.order.id}"
    
    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario  
     
class ShippingInfo(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='shipping_details')
    nombre_receptor = models.CharField(max_length=150)
    direccion_entrega = models.CharField(max_length=255)
    telefono_contacto = models.CharField(max_length=15)
    correo_electronico = models.EmailField()
    horario_entrega = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Información de envío para Pedido #{self.order.id}"

