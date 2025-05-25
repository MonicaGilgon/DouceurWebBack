from decimal import Decimal
from rest_framework import serializers
from .models import (Rol, Persona, ShippingInfo, Usuario, CategoriaArticulo, Articulo, CategoriaProductoBase, ProductoBase, ProductoBaseFoto, Order, OrderItem)

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

#class OrderItemSerializer(serializers.ModelSerializer):
 #   articulo = ArticuloSerializer()
#
 #   class Meta:
  #      model = OrderItem
   #     fields = ['articulo', #'quantity',
    #               #'price'
     #              ]



class ProductoBaseFotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductoBaseFoto
        fields = ['foto']

class ProductoBaseSerializer(serializers.ModelSerializer):
    categoriaProductoBase = CategoriaProductoBaseSerializer(read_only=True)
    
    categoriaProductoBase_id = serializers.PrimaryKeyRelatedField(
        queryset=CategoriaProductoBase.objects.filter(estado=True),
        source='categoriaProductoBase',
        write_only=True
    )

    categorias_articulo = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=CategoriaArticulo.objects.filter(estado=True),
        required=False
    )
    
    articulos = ArticuloSerializer(many=True, read_only=True)
    articulos_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Articulo.objects.filter(estado=True),
        source="articulos",
        write_only=True
    )

    imagen_url = serializers.SerializerMethodField()
    fotos = ProductoBaseFotoSerializer(many=True, read_only=True)
    
    fotos_a_eliminar = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )
    eliminar_imagen_principal = serializers.BooleanField(write_only=True, required=False)

    class Meta:
        model = ProductoBase
        fields = '__all__'

    def get_imagen_url(self, obj):
        if obj.imagen:
            return obj.imagen.url
        return None

    def create(self, validated_data):
        imagen = validated_data.pop('imagen', None)
        fotos_data = self.context['request'].FILES.getlist('fotos')

        producto_base = ProductoBase.objects.create(imagen=imagen, **validated_data)

        for foto in fotos_data:
            ProductoBaseFoto.objects.create(productoBase=producto_base, foto=foto)

        return producto_base

    def update(self, instance, validated_data):
        request = self.context.get('request')
        imagen = validated_data.pop('imagen', None)
        articulos = validated_data.pop('articulos', None)
        categorias_articulo = validated_data.pop('categorias_articulo', None)
        fotos_data = request.FILES.getlist('fotos') if request else []

        fotos_a_eliminar = validated_data.pop('fotos_a_eliminar', [])
        eliminar_imagen_principal = validated_data.pop('eliminar_imagen_principal', False)
        
        if fotos_a_eliminar:
            ProductoBaseFoto.objects.filter(id__in=fotos_a_eliminar, productoBase=instance).delete()

        if eliminar_imagen_principal and instance.imagen:
            instance.imagen.delete(save=False)
            instance.imagen = None
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if imagen:
            instance.imagen = imagen

        if articulos is not None:
            instance.articulos.set(articulos if isinstance(articulos, (list, tuple)) else [articulos])

        if categorias_articulo is not None:
            instance.categorias_articulo.set(categorias_articulo if isinstance(categorias_articulo, (list, tuple)) else [categorias_articulo])

        instance.save()

        for foto in fotos_data:
            ProductoBaseFoto.objects.create(productoBase=instance, foto=foto)

        return instance

class OrderItemSerializer(serializers.ModelSerializer):
    producto = ProductoBaseSerializer(read_only=True)  # Cambiado de articulo a producto para coincidir con el modelo

    class Meta:
        model = OrderItem
        fields = ['id', 'producto', 'cantidad', 'precio_unitario', 'subtotal']   

class CreateOrderItemSerializer(serializers.Serializer):
    producto_id = serializers.IntegerField()
    cantidad = serializers.IntegerField(min_value=1)
    precio_unitario = serializers.DecimalField(max_digits=10, decimal_places=2)

class ShippingInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingInfo
        fields = ['nombre_receptor', 'direccion_entrega', 'telefono_contacto', 
                  'correo_electronico', 'horario_entrega']

class OrderSerializer(serializers.ModelSerializer):
    shipping_details = ShippingInfoSerializer()  # Incluir datos de envío

    class Meta:
        model = Order
        fields = ['id', 'user', 'order_date', 'total_amount', 'status', 'payment_proof', 'items', 'shipping_details']
class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source='rol.nombre')
    #orders = OrderSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ['id','nombre_completo', 'correo', 'telefono', 'direccion', 'document_number', 'rol']#, 'orders']

class OrderResponseSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_info = ShippingInfoSerializer(read_only=True)
    user = UsuarioSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'order_date', 'total_amount', 'status', 'items', 'shipping_info', 'user']

class CreateOrderSerializer(serializers.Serializer):
    items = CreateOrderItemSerializer(many=True)
    nombre_receptor = serializers.CharField(max_length=150)
    direccion_entrega = serializers.CharField(max_length=255)
    telefono_contacto = serializers.CharField(max_length=15)
    correo_electronico = serializers.EmailField()
    horario_entrega = serializers.CharField(max_length=100)
    
    def create(self, validated_data):
        items_data = validated_data.pop('items')
        shipping_data = {
            'nombre_receptor': validated_data.pop('nombre_receptor'),
            'direccion_entrega': validated_data.pop('direccion_entrega'),
            'telefono_contacto': validated_data.pop('telefono_contacto'),
            'correo_electronico': validated_data.pop('correo_electronico'),
            'horario_entrega': validated_data.pop('horario_entrega'),
        }
        
        user = self.context['request'].user
        
        # Calcular el monto total
        total_amount = sum(
            Decimal(item['precio_unitario']) * item['cantidad'] 
            for item in items_data
        )
        
        # Crear el pedido
        order = Order.objects.create(
            user=user,
            total_amount=total_amount,
            status='pendiente'
        )
        
        # Crear la información de envío
        ShippingInfo.objects.create(order=order, **shipping_data)
        
        # Crear los items del pedido
        for item_data in items_data:
            producto = ProductoBase.objects.get(id=item_data['producto_id'])
            OrderItem.objects.create(
                order=order,
                producto=producto,
                cantidad=item_data['cantidad'],
                precio_unitario=item_data['precio_unitario']
            )
        
        return order
    
    def to_representation(self, instance):
        """
        Sobrescribimos este método para usar OrderResponseSerializer
        para la representación del objeto creado
        """
        return OrderResponseSerializer(instance, context=self.context).data



class VendedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'nombre_completo', 'correo', 'telefono', 'direccion', 'document_number', 'rol', 'estado']


#class 
# Serializer(serializers.ModelSerializer):
 #   class Meta:
  #      model = ArticulosProductoBase
   #     fields = '__all__'

