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



class ProductoBaseSerializer(serializers.ModelSerializer):
    categoriaProductoBase = CategoriaProductoBaseSerializer()
    articulos = ArticuloSerializer(many=True, read_only=True)
    imagen_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductoBase
        fields = '__all__'

    def get_imagen_url(self, obj):
        if obj.imagen:
            return obj.imagen.url
        return None

    # Sobrescribimos el método create para permitir la creación de fotos junto con el producto base
    def create(self, validated_data):
        fotos_data = self.context['request'].FILES.getlist(
            'fotos')  # Obtener las fotos desde los archivos
        producto_base = ProductoBase.objects.create(**validated_data)

        for foto in fotos_data:
            ProductoBaseFoto.objects.create(
                productoBase=producto_base, foto=foto)

        return producto_base

class ArticulosProductoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosProductoBase
        fields = '__all__'

class ProductoBaseFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoBaseFoto
        fields = ['id', 'foto']
       
    def validate_foto(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Cada imagen debe pesar menos de 5MB.")
        if not value.name.lower().endswith(('.jpeg', '.jpg', '.png')):
            raise serializers.ValidationError("Formato de imagen no permitido. Usa JPG o PNG.")
        return value
    
class ProductoBaseSerializer(serializers.ModelSerializer):
    fotos = ProductoBaseFotoSerializer(many=True, read_only=True)
    categoriaProductoBase = serializers.StringRelatedField()
    articulos = serializers.StringRelatedField(many=True)
    class Meta:
        model = ProductoBase
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen', 'estado', 'categoriaProductoBase', 'articulos', 'fotos']
        
    def validate_nombre(self, value):
        if not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío.")
        if ProductoBase.objects.filter(nombre=value).exists():
            raise serializers.ValidationError("Ya existe un producto base con ese nombre.")
        return value

    def create(self, validated_data):
        fotos_data = validated_data.pop('fotos', [])
        producto = ProductoBase.objects.create(**validated_data)
        for foto in fotos_data[:5]:  # Solo permitir máximo 5 imágenes
            ProductoBaseFoto.objects.create(productoBase=producto, foto=foto)
        return producto