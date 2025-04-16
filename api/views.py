from rest_framework import viewsets, status
from rest_framework.views import APIView
from .serializers import (RolSerializer, UsuarioSerializer, CategoriaArticuloSerializer, CategoriaProductoBaseSerializer)
from .models import (Rol, Usuario, CategoriaArticulo, CategoriaProductoBase, Order)
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.shortcuts import redirect, get_object_or_404
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
import json
from django.db import IntegrityError
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
import re
from django.db.models import Q
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required

# INDEX
def index(request):
    return HttpResponse("Bienvenido a la API de Douceur")

# CLIENTES
# REGISTRO DE CLIENTES
class CrearCliente(APIView):    
    def post(self, request): 
        try:
            rol_cliente = Rol.objects.get(nombre="cliente")
            nombre = request.data.get('nombre')
            correo = request.data.get('correo')
            password1 = request.data.get('password1')
            password2 = request.data.get('password2')

            # Validar que las contraseñas coincidan
            if password1 != password2:
                return JsonResponse({"error": "Las contraseñas no coinciden."}, status=400)

            # Verificar si el correo ya existe
            if Usuario.objects.filter(correo=correo).exists():
                return JsonResponse({"error": "Ya existe un usuario con este correo."}, status=400)

            # Crear el usuario con el rol por defecto de "cliente"
            nuevo_cliente = Usuario(
                nombre_completo=nombre,
                correo=correo,
                username=correo,
                rol=rol_cliente,
                estado=True
            )
            nuevo_cliente.set_password(password1)
            nuevo_cliente.save()

            # Redirigir al inicio de sesión si el registro fue exitoso
            return JsonResponse({"success": f"Cliente {nuevo_cliente.nombre_completo} creado correctamente."}, status=201)
        except Rol.DoesNotExist:
            return JsonResponse({"error": "Rol de cliente no encontrado."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear el cliente: {str(e)}"}, status=500)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        correo = request.data.get("correo")
        password = request.data.get("password")

        if not correo:
            return Response({"error": "El correo es obligatorio."}, status=400)
        if not password:
            return Response({"error": "La contraseña es obligatoria."}, status=400)

        user = authenticate(request, username=correo, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Inicio de sesión exitoso",
                "access_token": str(refresh.access_token),
                "refresh_token": str(refresh),
                "usuario": {
                    "id": user.id,
                    "nombre": user.nombre_completo,
                    "correo": user.correo,
                    "rol": user.rol.nombre
                }
            }, status=200)
        return Response({"error": "Credenciales inválidas"}, status=401)

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

# Validar contraseña según las reglas (≥8 caracteres, 1 mayúscula, 1 minúscula, 1 número)
def validate_password_strength(password):
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres."
    if not re.search(r'[A-Z]', password):
        return False, "La contraseña debe contener al menos una letra mayúscula."
    if not re.search(r'[a-z]', password):
        return False, "La contraseña debe contener al menos una letra minúscula."
    if not re.search(r'\d', password):
        return False, "La contraseña debe contener al menos un número."
    return True, ""

class RecoverPasswordView(APIView):
    def post(self, request):
        correo = request.data.get('correo')
        if not correo:
            return Response({"error": "El correo es obligatorio."}, status=400)

        try:
            user = Usuario.objects.get(correo=correo)
        except Usuario.DoesNotExist:
            return Response({"error": "No existe un usuario con este correo."}, status=404)

        # Generar token y UID
        token_generator = PasswordResetTokenGenerator()
        token = token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))

        # Crear el enlace de restablecimiento
        reset_link = f"http://localhost:3000/reset-password?token={token}&uid={uid}"

        # Enviar el correo
        subject = "Restablecer contraseña - Douceur"
        message = f"Hola {user.nombre_completo},\n\n" \
                  f"Hemos recibido una solicitud para restablecer tu contraseña. " \
                  f"Haz clic en el siguiente enlace para crear una nueva contraseña:\n\n" \
                  f"{reset_link}\n\n" \
                  f"Este enlace expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.\n\n" \
                  f"Saludos,\nEl equipo de Douceur"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.correo]

        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            return Response({"error": f"Error al enviar el correo: {str(e)}"}, status=500)

        return Response({"message": "Se ha enviado un enlace a tu correo para restablecer la contraseña."}, status=200)

class ResetPasswordView(APIView):
    def post(self, request):
        token = request.data.get('token')
        uid = request.data.get('uid')
        password = request.data.get('password')
        password_confirm = request.data.get('password_confirm')

        if not all([token, uid, password, password_confirm]):
            return Response({"error": "Todos los campos son obligatorios."}, status=400)

        # Validar que las contraseñas coincidan
        if password != password_confirm:
            return Response({"error": "Las contraseñas no coinciden."}, status=400)

        # Validar la fuerza de la contraseña
        is_valid, error_message = validate_password_strength(password)
        if not is_valid:
            return Response({"error": error_message}, status=400)

        # Decodificar UID y obtener el usuario
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = Usuario.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
            return Response({"error": "Enlace inválido o expirado."}, status=400)

        # Validar el token
        token_generator = PasswordResetTokenGenerator()
        if not token_generator.check_token(user, token):
            return Response({"error": "Enlace inválido o expirado."}, status=400)

        # Actualizar la contraseña
        user.set_password(password)
        user.save()

        return Response({"message": "Contraseña actualizada correctamente."}, status=200)

class ProfileView(APIView):

    def get(self, request):
        user = request.user
       
        serializer = UsuarioSerializer(user)
        return Response(serializer.data, status=200)

    def patch(self, request):
        user = request.user
        data = request.data

        # Campos permitidos para actualizar
        nombre_completo = data.get('nombre_completo', user.nombre_completo)
        direccion = data.get('direccion', user.direccion)
        telefono = data.get('telefono', user.telefono)
        correo = data.get('correo', user.correo)

        # Validaciones
        # Campos no vacíos
        if not nombre_completo:
            return Response({"error": "El nombre no puede estar vacío."}, status=400)
        if not telefono:
            return Response({"error": "El teléfono no puede estar vacío."}, status=400)
        if not correo:
            return Response({"error": "El correo no puede estar vacío."}, status=400)

        # Validar formato de correo
        email_validator = EmailValidator()
        try:
            email_validator(correo)
        except ValidationError:
            return Response({"error": "El correo electrónico no tiene un formato válido."}, status=400)

        # Validar unicidad de correo y teléfono
        if correo != user.correo and Usuario.objects.filter(correo=correo).exists():
            return Response({"error": "Ya existe un usuario con este correo."}, status=400)
        if telefono != user.telefono and Usuario.objects.filter(telefono=telefono).exists():
            return Response({"error": "Ya existe un usuario con este teléfono."}, status=400)

        # Actualizar campos
        user.nombre_completo = nombre_completo
        user.direccion = direccion
        user.telefono = telefono
        user.correo = correo
        user.username = correo  # Actualizar username ya que es el mismo que correo

        try:
            user.save()
            serializer = UsuarioSerializer(user)
            return Response({"message": "Perfil actualizado correctamente.", "data": serializer.data}, status=200)
        except Exception as e:
            return Response({"error": f"Error al actualizar el perfil: {str(e)}"}, status=500)

    def post(self, request):
        user = request.user
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')

        # Validar que todos los campos estén presentes
        if not all([current_password, new_password, confirm_password]):
            return Response({"error": "Todos los campos son obligatorios."}, status=400)

        # Validar contraseña actual
        if not check_password(current_password, user.password):
            return Response({"error": "La contraseña actual es incorrecta."}, status=400)

        # Validar que las nuevas contraseñas coincidan
        if new_password != confirm_password:
            return Response({"error": "Las nuevas contraseñas no coinciden."}, status=400)

        # Validar la fuerza de la nueva contraseña
        is_valid, error_message = validate_password_strength(new_password)
        if not is_valid:
            return Response({"error": error_message}, status=400)

        # Actualizar contraseña
        user.set_password(new_password)
        user.save()

        return Response({"message": "Contraseña actualizada correctamente."}, status=200)



""" 
#CLIENTE
# Vista personalizada para listar clientes
class ListarClientes(APIView):
    def get(self, request):
        try:
            clientes = Usuario.obtener_clientes()
            serializer = UsuarioSerializer(clientes, many=True)
            return Response(serializer.data, status=200)
        except Rol.DoesNotExist:
            return Response([], status=404)
        
#///////////////////////////////////////////////////////////////////////
#VENDEDOR
# VISTA LISTAR VENDEDORES
class ListarVendedores(APIView):
    def get(self, request):
        try:
            vendedores = Usuario.obtener_vendedores()
            serializer = UsuarioSerializer(vendedores, many=True)
            return Response(serializer.data, status=200)
        except Rol.DoesNotExist:
            return Response([], status=404)


# VISTA PERSONALIZADA PARA CREAR VENDEDOR
class CrearVendedor(APIView):
    def post(self, request): 
        try:
            vendedor_rol = Rol.objects.get(nombre="vendedor")

            nombre = request.data.get('nombre')
            correo = request.data.get('correo')
            contrasenia = request.data.get('contrasenia')
            telefono = request.data.get('telefono')
            direccion = request.data.get('direccion')            

            # Validar datos obligatorios
            if not all([nombre, correo, contrasenia, telefono, direccion]):
                return JsonResponse({"error": "Todos los campos son obligatorios."}, status=400)

            # Verificar si el correo ya existe
            if Usuario.objects.filter(correo=correo).exists():
                return JsonResponse({"error": "Ya existe un usuario con este correo."}, status=400)

            contrasenia_encriptada = make_password(contrasenia)
            nuevo_vendedor = Usuario(
                nombre_completo=nombre,
                correo=correo,
                password=contrasenia_encriptada,
                telefono=telefono,
                direccion=direccion,
                rol=vendedor_rol,
                estado=True
            )
            nuevo_vendedor.save()
            return JsonResponse({"success": f"Vendedor {nuevo_vendedor.nombre_completo} creado correctamente."}, status=201)

        except Rol.DoesNotExist:
            return JsonResponse({"error": "Rol de vendedor no encontrado."}, status=400)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear el vendedor: {str(e)}"}, status=500)


#LOGIN VENDEDOR
class VendedorViewSet(viewsets.ModelViewSet):
    queryset = Vendedor.objects.all()
    serializer_class = VendedorSerializer


#CAMBIAR ESTADO VENDEDOR
class CambiarEstadoVendedor(APIView):
    def patch(self, request, vendedor_id):
        vendedor = get_object_or_404(Persona, id=vendedor_id)
        activo = request.data.get('activo')
        if activo is not None:
            vendedor.activo = bool(activo)
            vendedor.save()
            return Response({'status': 'ok', 'activo': vendedor.activo}, status=status.HTTP_200_OK)
        return Response(
            {'status': 'error', 'message': 'El campo activo es requerido.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
#EDITAR VENDEDOR
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt, name='dispatch')
class EditarVendedor(APIView):
    def get(self, request, vendedor_id):
        vendedor = get_object_or_404(Usuario, id=vendedor_id, rol__nombre='vendedor')
        return JsonResponse({
            'id': vendedor.id,
            'nombre': vendedor.nombre_completo,
            'correo': vendedor.correo,
            'telefono': vendedor.telefono,
            'direccion': vendedor.direccion
        })

    def post(self, request, vendedor_id):
        vendedor = get_object_or_404(Usuario, id=vendedor_id, rol__nombre='vendedor')        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        vendedor.nombre_completo = data.get('nombre', vendedor.nombre_completo)
        vendedor.correo = data.get('correo', vendedor.correo)
        vendedor.telefono = data.get('telefono', vendedor.telefono)
        vendedor.direccion = data.get('direccion', vendedor.direccion)
        
        try:
            vendedor.save()
            return JsonResponse({'success': True, 'message': f"Vendedor {vendedor.nombre_completo} editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)

 """
#////////////////////////////////////////////////////////// 

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer


#/////////////////////////////////////////////////
#CATEGORIA_ARTICULO
#Crear categoria articulo
class CrearCategoriaArticulo(APIView):
    def post(self, request): 
        try:
            id = request.data.get('id')  
            nombre = request.data.get('nombre')         
            # Verificar si el id o el nombre ya existen
            if CategoriaArticulo.objects.filter(Q(id=id) | Q(nombre=nombre)).exists():
                return JsonResponse({"error": "Ya existe una categoría artículo con este id o nombre."}, status=400)       
            nueva_categoria_articulo = CategoriaArticulo(
                id=id,
                nombre=nombre,
                estado=True
            )
            nueva_categoria_articulo.save()
            return JsonResponse({"success": f"Categoría artículo {nueva_categoria_articulo.nombre} creada correctamente."}, status=201)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear la categoría artículo: {str(e)}"}, status=500)
     
#Listar categoria articulo
class ListarCategoriaArticulo(APIView):     
    def get(self, request):
        try:
            categorias = CategoriaArticulo.objects.all()
            serializer = CategoriaArticuloSerializer(categorias, many=True)
            return Response(serializer.data, status=200)
        except CategoriaArticulo.DoesNotExist:
            return JsonResponse([], status=404)

    def post(self, request):
        serializer = CategoriaArticuloSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save() 
            return Response(serializer.data, status=201)  
        return Response(serializer.errors, status=400) 


#Cambiar estado categoria articulo
class CambiarEstadoCategoriaArticulo(APIView):
    def patch(self, request, categoria_articulo_id):
        categoriaArticulo = get_object_or_404(CategoriaArticulo, id=categoria_articulo_id)
        estado = request.data.get('estado')
        if estado is not None:
            categoriaArticulo.estado = bool(estado)
            categoriaArticulo.save()
            return Response({'status': 'ok', 'estado': categoriaArticulo.estado}, status=status.HTTP_200_OK)
        return Response(
            {'status': 'error', 'message': 'El campo activo es requerido.'},
            status=status.HTTP_400_BAD_REQUEST
        )


#Editar categoria articulo
class EditarCategoriaArticulo(APIView):
    def get(self, request, categoria_articulo_id):
        categoria_articulo = get_object_or_404(CategoriaArticulo, id=categoria_articulo_id)
        csrf_token = get_token(request)
        return JsonResponse({
            'id': categoria_articulo.id,
            'nombre': categoria_articulo.nombre,
            'estado': categoria_articulo.estado,
            'csrf_token': csrf_token
        })

    def put(self, request, categoria_articulo_id):
        categoria_articulo = get_object_or_404(CategoriaArticulo, id=categoria_articulo_id)        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        nombre = data.get('nombre')    
        if nombre is None:
            return JsonResponse({'error': 'El campo nombre no puede estar vacío.'}, status=400)
        
        categoria_articulo.nombre = nombre
        
        try:
            categoria_articulo.save()
            return JsonResponse({'success': True, 'message': f"Categoría Artículo {categoria_articulo.nombre} editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)        

    def post(self, request, categoria_articulo_id):
        return JsonResponse({'error': 'Método no permitido.'}, status=405)



#///////////////////////////////////////////////////////////////
#CATEGORIA PRODUCTO BASE
#Crear categoria producto base
class CrearCategoriaProductoBase(APIView):
    def post(self, request): 
        try:
            id = request.data.get('id')  
            nombre = request.data.get('nombre')     
            # Verificar si el id o el nombre ya existen
            if CategoriaProductoBase.objects.filter(Q(id=id) | Q(nombre=nombre)).exists():
                return JsonResponse({"error": "Ya existe una categoría artículo con este id o nombre."}, status=400)       
            nueva_categoria_producto_base = CategoriaProductoBase(
                id=id,
                nombre=nombre,
                estado=True
            )
            nueva_categoria_producto_base.save()
            return JsonResponse({"success": f"Categoría producto base {nueva_categoria_producto_base.nombre} creada correctamente."}, status=201)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear la categoría producto base: {str(e)}"}, status=500)
     

      
#Listar categoria producto base
class ListarCategoriaProductoBase(APIView):
    def get(self, request): 
        try:
            categorias = CategoriaProductoBase.objects.all()
            serializer = CategoriaProductoBaseSerializer(categorias, many=True)
            return Response(serializer.data, status=200)
        except CategoriaProductoBase.DoesNotExist:
            return JsonResponse([], status=404)

    def post(self, request):
        serializer = CategoriaProductoBaseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)  
        return Response(serializer.errors, status=400) 


#Cabiar estado categoria producto base
class CambiarEstadoCategoriaProductoBase(APIView):
    def patch(self, request, categoria_pb_id):
        categoriaPB = get_object_or_404(CategoriaProductoBase, id=categoria_pb_id)
        estado = request.data.get('estado')
        if estado is not None:
            categoriaPB.estado = bool(estado)
            categoriaPB.save()
            return Response({'status': 'ok', 'estado': categoriaPB.estado}, status=status.HTTP_200_OK)
        return Response(
            {'status': 'error', 'message': 'El campo activo es requerido.'},
            status=status.HTTP_400_BAD_REQUEST
        )



#Editar categoria producto base
class EditarCategoriaProductoBase(APIView):
    def get(self, request, categoria_PB_id):
        categoria_PB = get_object_or_404(CategoriaProductoBase, id=categoria_PB_id)
        csrf_token = get_token(request)
        return JsonResponse({
            'id': categoria_PB.id,
            'nombre': categoria_PB.nombre,
            'estado': categoria_PB.estado,
            'csrf_token': csrf_token
        })

    def put(self, request, categoria_PB_id):
        categoria_PB = get_object_or_404(CategoriaProductoBase, id=categoria_PB_id)        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
        nombre = data.get('nombre')    
        if nombre is None:
            return JsonResponse({'error': 'El campo nombre no puede estar vacío.'}, status=400)
        
        categoria_PB.nombre = nombre
        
        try:
            categoria_PB.save()
            return JsonResponse({'success': True, 'message': f"Categoría Artículo {categoria_PB.nombre} editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)        

    def post(self, request, categoria_PB_id):
        return JsonResponse({'error': 'Método no permitido.'}, status=405)
""" 
class ProductosPorCategoria(APIView):
    def get(self, request, categoria_id):
        productosBase = ProductoBase.objects.filter(categoriaProductoBase=categoria_id)
        serializer = ProductoBaseSerializer(productosBase, many=True)
        return Response(serializer.data)
 """





