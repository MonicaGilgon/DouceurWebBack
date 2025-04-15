from rest_framework import serializers
from .models import Rol, Persona, Usuario, CategoriaArticulo, Articulo, Order, OrderItem

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
        fields = '__all__'

class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = ['nombre', 'precio']

class OrderItemSerializer(serializers.ModelSerializer):
    articulo = ArticuloSerializer()

    class Meta:
        model = OrderItem
        fields = ['articulo', 'quantity', 'price']

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
        fields = ['nombre_completo', 'correo', 'telefono', 'direccion', 'document_number', 'rol', 'orders']



