from dj_rest_auth.serializers import UserDetailsSerializer
from dj_rest_auth.registration.serializers import RegisterSerializer
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import (Rol, Persona, Usuario)

User = get_user_model()

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class PersonaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Persona
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    rol = serializers.CharField(source='rol.nombre', read_only=True)

    class Meta(UserDetailsSerializer.Meta):
        model = Usuario
        fields = ('id', 'correo', 'nombre_completo', 'telefono', 'direccion', 'rol')



class CustomRegisterSerializer(RegisterSerializer):
    nombre_completo = serializers.CharField()
    telefono = serializers.CharField()
    direccion = serializers.CharField()

    def get_cleaned_data(self):
        # Obtener los datos que normalmente recoge RegisterSerializer
        data = super().get_cleaned_data()
        data['nombre_completo'] = self.validated_data.get('nombre_completo', '')
        data['telefono'] = self.validated_data.get('telefono', '')
        data['direccion'] = self.validated_data.get('direccion', '')
        return data

    def save(self, request):
        data = self.get_cleaned_data()

        try:
            rol_cliente = Rol.objects.get(nombre="cliente")
        except Rol.DoesNotExist:
            raise serializers.ValidationError({'rol': "El rol 'cliente' no existe."})

        # Creamos el usuario manualmente para asegurarnos que se asigne todo antes de guardar
        user = User(
            email=data['email'],
            nombre_completo=data['nombre_completo'],
            telefono=data['telefono'],
            direccion=data['direccion'],
            rol=rol_cliente,
        )
        user.username = data['email']  # O genera algo único si prefieres
        user.set_password(data['password1'])
        user.save()

        return user