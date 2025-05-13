from rest_framework import serializers
from .models import (Rol, Persona, Usuario, CategoriaArticulo, Articulo, CategoriaProductoBase, ProductoBase, ProductoBaseFoto, ArticulosProductoBase, Order, OrderItem)

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'

class CategoriaArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaArticulo
        fields = ['id', 'nombre', 'estado']

class CategoriaProductoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaProductoBase
        fields = '__all__'

class ArticuloSerializer(serializers.ModelSerializer):
    categoriaArticulo = CategoriaArticuloSerializer(read_only=True)
    class Meta:
        model = Articulo
        fields = '__all__'

class OrderItemSerializer(serializers.ModelSerializer):
    articulo = ArticuloSerializer()

    class Meta:
        model = OrderItem
        fields = ['articulo', #'quantity',
                   #'price'
                   ]

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'total_amount', 'status', 'items']

class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source='rol.nombre')
    orders = OrderSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ['id','nombre_completo', 'correo', 'telefono', 'direccion', 'document_number', 'rol', 'orders']

class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre_completo', 'correo', 'telefono', 'direccion', 'document_number', 'rol', 'estado']

class ProductoBaseFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoBaseFoto
        fields = ['foto']


class ProductoBaseSerializer(serializers.ModelSerializer):
    categoriaProductoBase = CategoriaProductoBaseSerializer()
    articulos = ArticuloSerializer(many=True, read_only=True)
    imagen_url = serializers.SerializerMethodField()
    fotos = ProductoBaseFotoSerializer(many=True, read_only=True)

    class Meta:
        model = ProductoBase
        fields = '__all__'

    def get_imagen_url(self, obj):
        if obj.imagen:
            return obj.imagen.url
        return None


    # Sobrescribimos el método create para permitir la creación de fotos junto con el producto base
    def create(self, validated_data):
    # Extraer la imagen manualmente
        imagen = validated_data.pop('imagen', None)
        fotos_data = self.context['request'].FILES.getlist('fotos')

        producto_base = ProductoBase.objects.create(imagen=imagen, **validated_data)

        for foto in fotos_data:
            ProductoBaseFoto.objects.create(productoBase=producto_base, foto=foto)

        return producto_base


class ArticulosProductoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosProductoBase
        fields = '__all__'