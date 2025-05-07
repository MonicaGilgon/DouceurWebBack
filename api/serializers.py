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
        fields = ['id', 'foto']

    def validate_foto(self, value):
        if value.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("Cada imagen debe pesar menos de 5MB.")
        if not value.name.lower().endswith(('.jpeg', '.jpg', '.png')):
            raise serializers.ValidationError("Formato de imagen no permitido. Usa JPG o PNG.")
        return value

class ProductoBaseUpdateSerializer(serializers.ModelSerializer):
    categoriaProductoBase = serializers.PrimaryKeyRelatedField(queryset=CategoriaProductoBase.objects.all())
    articulos = serializers.PrimaryKeyRelatedField(queryset=Articulo.objects.all(), many=True)

    class Meta:
        model = ProductoBase
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen', 'estado', 'categoriaProductoBase', 'articulos']


class ProductoBaseSerializer(serializers.ModelSerializer):
    categoriaProductoBase = CategoriaProductoBaseSerializer(read_only=True)
    articulos = ArticuloSerializer(many=True, read_only=True)
    imagen_url = serializers.SerializerMethodField()
    fotos = ProductoBaseFotoSerializer(many=True, read_only=True)

    class Meta:
        model = ProductoBase
        fields = ['id', 'nombre', 'descripcion', 'precio', 'imagen', 'imagen_url', 'estado', 'categoriaProductoBase', 'articulos', 'fotos']

    def get_imagen_url(self, obj):
        if obj.imagen:
            return obj.imagen.url
        return None

    def create(self, validated_data):
        fotos_data = self.context['request'].FILES.getlist('fotos')
        producto_base = ProductoBase.objects.create(**validated_data)

        for foto in fotos_data[:5]:
            ProductoBaseFoto.objects.create(productoBase=producto_base, foto=foto)

        return producto_base


class ArticulosProductoBaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArticulosProductoBase
        fields = '__all__'