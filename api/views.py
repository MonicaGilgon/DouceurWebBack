from rest_framework import viewsets, status
from rest_framework.views import APIView
from .serializers import (CreateOrderSerializer, OrderResponseSerializer, RolSerializer, UsuarioSerializer, CategoriaArticuloSerializer, ArticuloSerializer,  CategoriaProductoBaseSerializer, ProductoBaseSerializer, VendedorSerializer)
from .models import (Rol, Usuario, CategoriaArticulo, Articulo, CategoriaProductoBase, ProductoBase, Order, ProductoBaseFoto)
from django.http import HttpResponse, JsonResponse
from rest_framework.response import Response
from django.contrib.auth.hashers import check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.middleware.csrf import get_token
from rest_framework.permissions import AllowAny
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
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
from rest_framework import generics, permissions
from django.contrib import messages
from django.template.loader import render_to_string
from rest_framework.parsers import MultiPartParser, FormParser

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
            
            # Validar la fortaleza de la contraseña
            is_valid, error_message = validate_password_strength(password1)
            if not is_valid:
                return JsonResponse({"error": error_message}, status=400)

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
                    "rol": user.rol.nombre,
                    "telefono": user.telefono,
                    "direccion": user.direccion,
                    "estado": user.estado
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

from django.core.mail import send_mail
from django.conf import settings
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Usuario  
from django.contrib.auth.tokens import PasswordResetTokenGenerator

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

        # Asunto del correo
        subject = "Restablecer contraseña - Douceur"

        # Mensaje en texto plano (como respaldo)
        message = f"Hola {user.nombre_completo},\n\n" \
                  f"Hemos recibido una solicitud para restablecer tu contraseña. " \
                  f"Haz clic en el siguiente enlace para crear una nueva contraseña:\n\n" \
                  f"{reset_link}\n\n" \
                  f"Este enlace expirará en 15 minutos. Si no solicitaste este cambio, ignora este correo.\n\n" \
                  f"Saludos,\nEl equipo de Douceur"

        # Plantilla HTML para el correo
        html_message = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Restablecer Contraseña</title>
            <style>
                body {{
                    font-family: 'Helvetica Neue', Arial, sans-serif;
                    margin: 0;
                    padding: 0;
                    background-color: #f4f4f4;
                    line-height: 1.6;
                }}
                .container {{
                    width: 100%;
                    max-width: 600px;
                    margin: 20px auto;
                    background-color: #ffffff;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    background-color: #FDC7E7;
                    color: #333333;
                    text-align: center;
                    padding: 20px;
                }}
                .header img {{
                    width: 120px;
                    height: auto;
                    display: block;
                    margin: 0 auto;
                }}
                .content {{
                    padding: 40px 30px;
                    text-align: center;
                }}
                .content img.lock-icon {{
                    width: 80px;
                    height: auto;
                    margin-bottom: 20px;
                }}
                .content h1 {{
                    font-size: 26px;
                    color: #333333;
                    margin-bottom: 15px;
                    font-weight: 600;
                }}
                .content p {{
                    font-size: 16px;
                    color: #555555;
                    margin-bottom: 25px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    background-color: #FDC7E7;
                    color: #333333;
                    text-decoration: none;
                    border-radius: 5px;
                    font-size: 16px;
                    font-weight: 600;
                    transition: background-color 0.3s ease;
                }}
                .button:hover {{
                    background-color: #f9b3db;
                }}
                .social {{
                    text-align: center;
                    padding: 20px;
                    border-top: 1px solid #eeeeee;
                }}
                .social p {{
                    font-size: 14px;
                    color: #555555;
                    margin-bottom: 15px;
                }}
                .social a {{
                    margin: 0 10px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .social img {{
                    width: 28px;
                    height: 28px;
                    border-radius: 50%;
                }}
                .footer {{
                    background-color: #FDC7E7;
                    color: #333333;
                    text-align: center;
                    padding: 20px;
                    font-size: 14px;
                }}
                .footer a {{
                    color: #333333;
                    text-decoration: none;
                    margin: 0 10px;
                    font-weight: 500;
                }}
                .footer a:hover {{
                    text-decoration: underline;
                }}
                .footer-links {{
                    margin-top: 10px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <img src="https://res.cloudinary.com/yasstore23/image/upload/v1745567054/nlfc1k22byubnhhfm3ix.png" alt="Douceur Logo">
                </div>
                <div class="content">
                    <img src="https://res.cloudinary.com/yasstore23/image/upload/v1745566822/ejjihbr1fmlbuailcwrr.png" alt="Lock Icon" class="lock-icon">
                   <h1>¿OLVIDASTE TU CONTRASEÑA?</h1>
                   <p>Hola {user.nombre_completo},</p>
                    <p>Hemos recibido una solicitud para cambiar tu contraseña. Si no realizaste esta solicitud, ignora este correo. De lo contrario, haz clic en el botón de abajo para cambiar tu contraseña:</p>
                   <a href="{reset_link}" class="button">RESTABLECER CONTRASEÑA</a>
                   <p style="font-size: 0.9em; color: #555; margin-top: 20px;">Este enlace es válido por 15 minutos. Después de ese tiempo, tendrás que solicitar uno nuevo si necesitas restablecer tu contraseña.</p>


                </div>
                <div class="social">
                    <p>SÍGUENOS:</p>
                    <a href="https://wa.me/573124132200"><img src="https://res.cloudinary.com/yasstore23/image/upload/v1745566822/vgfmppajatgnqklsdbhk.png" alt="Whatsapp"></a>
                    <a href="https://www.instagram.com/douceur.nl/"><img src="https://res.cloudinary.com/yasstore23/image/upload/v1745566822/fyktowrszcjzeuogelsp.png" alt="Instagram"></a>
                     
                  
                </div>
                <div class="footer">
                    <p>¿TIENES PREGUNTAS? <a href="mailto:info@douceur.com">CONTÁCTANOS</a></p>
                    <div class="footer-links">
                        <a href="#">REGÍSTRATE</a> | <a href="#">BLOG</a> | <a href="#">SOBRE NOSOTROS</a>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """

        # Enviar el correo
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [user.correo]

        try:
            send_mail(
                subject=subject,
                message=message,  # Versión en texto plano
                from_email=from_email,
                recipient_list=recipient_list,
                html_message=html_message,  # Versión HTML
                fail_silently=False,
            )
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
        document_number = data.get('document_number', user.document_number)
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
        if not document_number:
            return Response({"error": "El número de documento no puede estar vacío."}, status=400)

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
        user.document_number = document_number
        user.nombre_completo = nombre_completo
        user.direccion = direccion
        user.telefono = telefono
        user.correo = correo
        user.username = correo  

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
        
class EditarCliente(APIView):
    def get(self, request, cliente_id):
        cliente = get_object_or_404(Usuario, id=cliente_id, rol__nombre='cliente')
        return JsonResponse({
            'id': cliente.id,
            'nombre': cliente.nombre_completo,
            'correo': cliente.correo,
            'telefono': cliente.telefono,
            'direccion': cliente.direccion
        })

    def post(self, request, cliente_id):
        cliente = get_object_or_404(Usuario, id=cliente_id, rol__nombre='cliente')        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)

        cliente.nombre_completo = data.get('nombre', cliente.nombre_completo)
        cliente.correo = data.get('correo', cliente.correo)
        cliente.telefono = data.get('telefono', cliente.telefono)
        cliente.direccion = data.get('direccion', cliente.direccion)
        
        try:
            cliente.save()
            return JsonResponse({'success': True, 'message': f"Cliente {cliente.nombre_completo} editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)

"""            
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

"""

#VENDEDORES
#Crear vendedor
class CrearVendedor(APIView):
    def post(self, request): 
        try:
            vendedor_rol = Rol.objects.get(nombre="vendedor")
            cedula = request.data.get('cedula')  
            nombre = request.data.get('nombre')
            correo = request.data.get('correo')
            contrasenia = request.data.get('contrasenia')
            telefono = request.data.get('telefono')
            direccion = request.data.get('direccion')            
            # Verificar si la cédula o el correo ya existen
            if Usuario.objects.filter(Q(document_number=cedula) | Q(correo=correo)).exists():
                return JsonResponse({"error": "Ya existe un usuario con esta cédula o correo."}, status=400)       
            contrasenia_encriptada = make_password(contrasenia)
            nuevo_vendedor = Usuario(
                document_number=cedula,
                nombre_completo=nombre,
                correo=correo,
                password=contrasenia_encriptada,
                telefono=telefono,
                direccion=direccion,
                rol=vendedor_rol,
                estado=True,
                username=correo
            )
            nuevo_vendedor.save()
            return JsonResponse({"success": f"Vendedor {nuevo_vendedor.nombre_completo} creado correctamente."}, status=201)
        except Rol.DoesNotExist:
            print("Error al crear el vendedor:", str(e))
            return JsonResponse({"error": "Rol de vendedor no encontrado."}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({"error": f"Error al crear el vendedor: {str(e)}"}, status=500)


# VISTA LISTAR VENDEDORES
class ListarVendedores(APIView):
    def get(self, request):
        try:
            vendedores = Usuario.obtener_vendedores()
            serializer = VendedorSerializer(vendedores, many=True)
            return Response(serializer.data, status=200)
        except Rol.DoesNotExist:
            return Response([], status=404)

class CambiarEstadoVendedor(APIView):
    def patch(self, request, vendedor_id):
        vendedor = get_object_or_404(Usuario, id=vendedor_id, rol__nombre='vendedor')
        estado = request.data.get('estado')
        if estado is not None:
            vendedor.estado = bool(estado)
            vendedor.save()
            return Response({'status': 'ok', 'activo': vendedor.estado}, status=status.HTTP_200_OK)
        return Response(
            {'status': 'error', 'message': 'El campo estado es requerido.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
class EditarVendedor(APIView):
    def get(self, request, vendedor_id):
        vendedor = get_object_or_404(Usuario, id=vendedor_id, rol__nombre='vendedor')
        return JsonResponse({
            'id': vendedor.id,
            'document_number': vendedor.document_number,
            'nombre': vendedor.nombre_completo,
            'correo': vendedor.correo,
            'telefono': vendedor.telefono,
            'direccion': vendedor.direccion,
            'estado': vendedor.estado
        })

    def post(self, request, vendedor_id):
        vendedor = get_object_or_404(Usuario, id=vendedor_id, rol__nombre='vendedor')        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
        
        vendedor.document_number = data.get('document_number', vendedor.document_number)
        vendedor.nombre_completo = data.get('nombre_completo', vendedor.nombre_completo)
        vendedor.correo = data.get('correo', vendedor.correo)
        vendedor.telefono = data.get('telefono', vendedor.telefono)
        vendedor.direccion = data.get('direccion', vendedor.direccion)
        vendedor.estado = bool(data.get('estado', vendedor.estado))
        
        try:
            vendedor.save()
            return JsonResponse({'success': True, 'message': f"Vendedor {vendedor.nombre_completo} editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)

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



class ProductosPorCategoria(APIView):
    def get(self, request, categoria_id):
        productosBase = ProductoBase.objects.filter(categoriaProductoBase=categoria_id)
        serializer = ProductoBaseSerializer(productosBase, many=True)
        return Response(serializer.data)


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



#/////////////////////////////////////////////////////////////////////////
#ARTICULOS
#Crear articulo
class CrearArticulo(APIView):
    def post(self, request): 
        try: 
            nombre = request.data.get('nombre')
            categoriaArticulo = request.data.get('categoriaArticulo')
            # Verificar si el nombre ya existe
            if Articulo.objects.filter (nombre=nombre).exists():
                return JsonResponse({"error": "Ya existe un artículo con este nombre."}, status=400)       
            nuevo_articulo = Articulo(
                nombre=nombre,              
                categoriaArticulo_id=categoriaArticulo,                
            )
            nuevo_articulo.save()
            return JsonResponse({"success": f"Artículo {nuevo_articulo.nombre} creado correctamente."}, status=201)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear el artículo: {str(e)}"}, status=500)


#Editar artículo
class EditarArticulo(APIView):
    def get(self, request, articulo_id):
        articulo = get_object_or_404(Articulo, id=articulo_id)
        csrf_token = get_token(request)
        return JsonResponse({
            'nombre': articulo.nombre,
            'categoriaArticulo': articulo.categoriaArticulo.id if articulo.categoriaArticulo else None,
            'csrf_token': csrf_token
        })

    def put(self, request, articulo_id):
        articulo = get_object_or_404(Articulo, id=articulo_id)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        nombre = data.get('nombre')    
        if not nombre:
            return JsonResponse({'error': 'El campo nombre no puede estar vacío.'}, status=400)
        
        # Actualización de campos
        articulo.nombre = nombre
       
        # Actualización de categoriaArticulo si es necesario
        categoria_id = data.get('categoriaArticulo')
        if categoria_id:
            articulo.categoriaArticulo_id = categoria_id

        try:
            articulo.save()
            return JsonResponse({'success': True, 'message': f"Artículo '{articulo.nombre}' editado correctamente."}, status=200)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    def post(self, request, articulo_id):
        return JsonResponse({'error': 'Método no permitido.'}, status=405)

class ArticuloPorCategoria(APIView):
    def get(self, request, categoria_id):
        articulos = Articulo.objects.filter(categoriaArticulo=categoria_id)
        serializer = ArticuloSerializer(articulos, many=True)
        return Response(serializer.data)




#Listar articulo
class ListarArticulos(APIView):
    def get(self, request):
        try:
            articulos = Articulo.objects.all()
            serializer = ArticuloSerializer(articulos, many=True)
            return Response(serializer.data, status=200)
        except Articulo.DoesNotExist:
            return JsonResponse([], safe=False, status=404)



class ArticulosPorCategoria(APIView):
    def get(self, request, categoria_id):
        articulos = Articulo.objects.filter(categoriaArticulo=categoria_id)
        serializer = ArticuloSerializer(articulos, many=True)
        return Response(serializer.data)



#//////////////////////////////////////////////////////////
#PRODUCTO BASE
#Crear producto base
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
import json

from .models import ProductoBase, ProductoBaseFoto, CategoriaProductoBase, Articulo
from .serializers import ProductoBaseSerializer

class CrearProductoBase(APIView):
    parser_classes = [MultiPartParser, FormParser] 
    def post(self, request):
        try:
            nombre = request.data.get('nombre')
            descripcion = request.data.get('descripcion')
            precio = request.data.get('precio')
            imagen = request.FILES.get('imagen')
            categoriaProductoBase_id = request.data.get('categoriaProductoBase') 
            articulos_ids = request.data.get('articulos', '[]')
            imagenes = request.FILES.getlist('fotos') 

             # Validaciones nombre
            if not nombre:
                return JsonResponse({"error": "El nombre no puede estar vacío."}, status=400)
            if ProductoBase.objects.filter(nombre=nombre).exists():
                return JsonResponse({"error": "Ya existe un producto con ese nombre."}, status=400)

            # Validaciones descripción y precio
            if not descripcion:
                return JsonResponse({"error": "La descripción es obligatoria."}, status=400)
            try:
                precio = float(precio)
                if precio <= 0:
                    return JsonResponse({"error": "El precio debe ser mayor que 0."}, status=400)
            except:
                return JsonResponse({"error": "Precio inválido."}, status=400)

            # Validar y parsear IDs de artículos
            articulos_ids = json.loads(articulos_ids) if isinstance(articulos_ids, str) else articulos_ids
            articulos = Articulo.objects.filter(id__in=articulos_ids)
            if len(articulos) != len(articulos_ids):
                return JsonResponse({"error": "Uno o más artículos no existen."}, status=400)

            # Verificar que las claves foráneas existen
            try:
                categoriaProductoBase = CategoriaProductoBase.objects.get(id=categoriaProductoBase_id)
            except CategoriaProductoBase.DoesNotExist:
                return JsonResponse({"error": "La categoría proporcionada no existe."}, status=400)
            
            for img in imagenes:
                if not img.name.lower().endswith(('.jpg', '.jpeg', '.png')):
                    return JsonResponse({"error": f"La imagen '{img.name}' no es JPG o PNG."}, status=400)
                if img.size > 5 * 1024 * 1024:
                    return JsonResponse({"error": f"La imagen '{img.name}' supera los 5MB."}, status=400)
            
            # Crear el producto base
            nuevo_producto_base = ProductoBase(
                nombre=nombre,
                descripcion=descripcion,
                precio=precio,
                estado=True,
                categoriaProductoBase=categoriaProductoBase,
                imagen=imagen  # ✅ Aquí está la solución
            )
            nuevo_producto_base.save()
            
            # Asociar categorías de artículo
            categorias_ids = request.data.get('categorias_articulo', '[]')
            categorias_ids = json.loads(categorias_ids) if isinstance(categorias_ids, str) else categorias_ids
            categorias = CategoriaArticulo.objects.filter(id__in=categorias_ids)
            if len(categorias) != len(categorias_ids):
                return JsonResponse({"error": "Una o más categorías de artículo no existen."}, status=400)
            nuevo_producto_base.categorias_articulo.set(categorias)

            # Asociar artículos
            nuevo_producto_base.articulos.set(articulos)
            
            # Guardar imágenes
            for img in imagenes:
                ProductoBaseFoto.objects.create(productoBase=nuevo_producto_base, foto=img)

            return JsonResponse({"success": f"Producto '{nuevo_producto_base.nombre}' creado correctamente."}, status=201)
        except Exception as e:
            return JsonResponse({"error": f"Error al crear el producto base: {str(e)}"}, status=500)

def product_detail(request, id):
    producto = get_object_or_404(ProductoBase, id=id)
    return render(request, 'products/detalleProducto.html', {'producto': producto})



#Listar producto base
class ListarProductoBase(APIView):
    def get(self, request):
        try:
            productoBase = ProductoBase.objects.filter(estado=True)
            serializer = ProductoBaseSerializer(productoBase, many=True)
            return Response(serializer.data, status=200)
        except Exception as e:
            return JsonResponse({"error": f"Error al obtener productos: {str(e)}"}, status=500)

def products_list_views(request):
    # Filtrar productos con estado=True
    products = ProductoBase.objects.filter(estado=True)

    context = {
        "products": products, 
    }
    #return render(request, '/index.html', context)



class EditarProductoBase(APIView):
    parser_classes = [MultiPartParser, FormParser]  # ✅ Habilita archivos

    def get(self, request, producto_id):
        producto_base = get_object_or_404(ProductoBase, id=producto_id)
        csrf_token = get_token(request)
        return JsonResponse({
            'nombre': producto_base.nombre,
            'descripcion': producto_base.descripcion,
            'precio': producto_base.precio,
            'estado': producto_base.estado,
            'categoriaProductoBase': producto_base.categoriaProductoBase.id,
            'articulos': list(producto_base.articulos.values('id', 'nombre')),
            'categorias_articulo': list(producto_base.categorias_articulo.values('id', 'nombre')),
            'imagen': producto_base.imagen.url if producto_base.imagen else None,
            'csrf_token': csrf_token,
            'fotos': [
                {"id": foto.id, "url": foto.foto.url}
                for foto in producto_base.fotos.all()
            ],
        })


    def put(self, request, producto_id):
        producto_base = get_object_or_404(ProductoBase, id=producto_id)

        try:
            nombre = request.data.get("nombre")
            descripcion = request.data.get("descripcion")
            precio = request.data.get("precio")
            estado_raw = request.data.get("estado", "true")
            estado = estado_raw.lower() == "true" if isinstance(estado_raw, str) else bool(estado_raw)

            categoria_id = request.data.get("categoriaProductoBase")
            articulos_raw = request.data.get("articulos", "[]")
            imagen = request.FILES.get("imagen")  # ✅ Aquí tomamos la imagen correctamente

            # Parsear artículos
            articulos = json.loads(articulos_raw) if isinstance(articulos_raw, str) else articulos_raw

            if not nombre:
                return JsonResponse({"error": "El nombre no puede estar vacío."}, status=400)

            if ProductoBase.objects.filter(nombre=nombre).exclude(id=producto_base.id).exists():
                return JsonResponse({"error": "Ya existe un producto con ese nombre."}, status=400)

            categoria = get_object_or_404(CategoriaProductoBase, id=categoria_id)

            producto_base.nombre = nombre
            producto_base.descripcion = descripcion
            producto_base.precio = precio
            producto_base.estado = estado
            producto_base.categoriaProductoBase = categoria
            producto_base.articulos.set(articulos)

            if imagen:
                producto_base.imagen = imagen

            producto_base.save()
            
            # Actualizar categorías de artículo
            categorias_ids = request.data.get('categorias_articulo', '[]')
            categorias_ids = json.loads(categorias_ids) if isinstance(categorias_ids, str) else categorias_ids
            categorias = CategoriaArticulo.objects.filter(id__in=categorias_ids)
            if len(categorias) != len(categorias_ids):
                return JsonResponse({"error": "Una o más categorías de artículo no existen."}, status=400)
            producto_base.categorias_articulo.set(categorias)             
            
            fotos_nuevas = request.FILES.getlist("fotos")
            for foto in fotos_nuevas:
                ProductoBaseFoto.objects.create(productoBase=producto_base, foto=foto)

            serializer = ProductoBaseSerializer(producto_base)
            return JsonResponse(serializer.data, safe=False, status=200)

        except CategoriaProductoBase.DoesNotExist:
            return JsonResponse({'error': 'La categoría especificada no existe.'}, status=400)
        except IntegrityError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({'error': f"Error al actualizar: {str(e)}"}, status=500)

class EliminarFotoProducto(APIView):
    def delete(self, request, foto_id):
        try:
            foto = ProductoBaseFoto.objects.get(id=foto_id)
            foto.delete()
            return JsonResponse({"success": "Imagen eliminada correctamente."}, status=200)
        except ProductoBaseFoto.DoesNotExist:
            return JsonResponse({"error": "Imagen no encontrada."}, status=404)

#CARRITO DE COMPRAS
def AddToCart(request):
    product_id = request.GET.get('id')
    title = request.GET.get('title')
    qty = request.GET.get('qty')
    price = request.GET.get('price')

    if not all([product_id, title, qty, price]):
        return JsonResponse({'error': 'Faltan parAmetros requeridos'}, status=400)


    cart_product = {
        str(product_id): {
            'title': title,
            'qty': qty,
            'price': price,
        }
    }

    if 'cart_data_obj' in request.session:
        cart_data = request.session['cart_data_obj']
        if str(product_id) in cart_data:
            cart_data[str(product_id)]['qty'] = int(qty)
        else:
            cart_data.update(cart_product)
        request.session['cart_data_obj'] = cart_data
    else:
        request.session['cart_data_obj'] = cart_product

    return JsonResponse({
        "data": request.session['cart_data_obj'],
        'totalcartitems': len(request.session['cart_data_obj'])
    })


class CartView(APIView):
    def get(self, request, *args, **kwargs):
        cart_data = request.session.get('cart', {})
        cart_total_amount = sum(
            float(item['price']) * item['qty'] for item in cart_data.values()
        )
        return Response({
            'cart': cart_data,
            'total': round(cart_total_amount, 2)
        })
    

def DeleteFromCart(request):
    product_id = request.GET.get('id')
    
    if not product_id:
        return JsonResponse({'error': 'No se proporcionO el ID del producto'}, status=400)

    cart_data = request.session.get('cart_data_obj', {})
    
    if product_id in cart_data:
        del cart_data[product_id]
        request.session['cart_data_obj'] = cart_data
    
    cart_total_amount = sum(int(item['qty']) * float(item['price']) for item in cart_data.values())

    context = render_to_string("polls/cart.html", {
        "cart_data": cart_data,
        'totalcartitems': len(cart_data),
        'cart_total_amount': cart_total_amount
    })

    return JsonResponse({
        "data": context,
        'totalcartitems': len(cart_data)
    })
        


def UpdateCart(request):
    product_id = request.GET.get('id')
    product_qty = request.GET.get('qty')

    if not product_id or not product_qty:
        return JsonResponse({'error': 'Faltan parAmetros "id" o "qty".'}, status=400)

    try:
        product_qty = int(product_qty)
    except ValueError:
        return JsonResponse({'error': 'El paráAetro "qty" debe ser un nUmero entero.'}, status=400)

    if 'cart_data_obj' in request.session:
        if product_id in request.session['cart_data_obj']:
            cart_data = request.session['cart_data_obj']
            cart_data[product_id]['qty'] = product_qty  # Actualiza la cantidad
            request.session['cart_data_obj'] = cart_data

    # Recalcular el total del carrito
    cart_total_amount = 0
    updated_subtotal = 0
    if 'cart_data_obj' in request.session and product_id in request.session['cart_data_obj']:
        item = request.session['cart_data_obj'][product_id]
        updated_subtotal = item['price'] * item['qty']
        for item in request.session['cart_data_obj'].values():
            cart_total_amount += item['price'] * item['qty']

    return JsonResponse({
        'message': 'Carrito actualizado correctamente.',
        'subtotal': updated_subtotal,
        'total': cart_total_amount
    })

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from decimal import Decimal
from django.db.models.functions import TruncDate
from django.db.models import Sum, Count, Avg
from datetime import datetime
from .models import Order, OrderItem
from .serializers import OrderResponseSerializer

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        serializer = CreateOrderSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            order = serializer.save()
            
            # Usar el serializador de respuesta para devolver los datos
            response_serializer = OrderResponseSerializer(order)
            
            return Response({
                'order': response_serializer.data,
                'message': 'Pedido creado exitosamente'
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class OrderListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        status_filter = request.query_params.get('status')
        
        orders = Order.objects.all().select_related('user', 'shipping_info')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
            
        serializer = OrderResponseSerializer(orders, many=True)
        return Response(serializer.data)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderResponseSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class UpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id)
            
            new_status = request.data.get('status')
            if not new_status or new_status not in [s[0] for s in Order.STATUS_CHOICES]:
                return Response(
                    {"error": "Estado no válido"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            order.status = new_status
            order.save()
            
            serializer = OrderResponseSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class SalesReportView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not start_date or not end_date:
            return Response(
                {"error": "Se requieren fechas de inicio y fin"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return Response(
                {"error": "Formato de fecha inválido. Use YYYY-MM-DD"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Filtrar pedidos por rango de fechas
        orders = Order.objects.filter(
            order_date__date__gte=start_date,
            order_date__date__lte=end_date
        )
        
        # Calcular estadísticas
        total_orders = orders.count()
        total_sales = orders.aggregate(total=Sum('total_amount'))['total'] or 0
        delivered_orders = orders.filter(status='entregado').count()
        average_order_value = orders.aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Ventas por día
        sales_by_date = orders.annotate(
            date=TruncDate('order_date')
        ).values('date').annotate(
            total=Sum('total_amount'),
            count=Count('id')
        ).order_by('date')
        
        # Pedidos por estado
        sales_by_status = orders.values('status').annotate(
            count=Count('id'),
            total=Sum('total_amount')
        ).order_by('status')
        
        # Formatear datos para la respuesta
        sales_by_date_formatted = [
            {
                'date': item['date'].strftime('%Y-%m-%d'),
                'total': float(item['total']),
                'count': item['count']
            }
            for item in sales_by_date
        ]
        
        sales_by_status_formatted = [
            {
                'status': item['status'],
                'count': item['count'],
                'total': float(item['total'])
            }
            for item in sales_by_status
        ]
        
        return Response({
            'total_orders': total_orders,
            'total_sales': float(total_sales),
            'delivered_orders': delivered_orders,
            'average_order_value': float(average_order_value),
            'sales_by_date': sales_by_date_formatted,
            'sales_by_status': sales_by_status_formatted
        })
    
class VendedorOrderListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Verificar que el usuario sea vendedor
        if request.user.rol != 'vendedor' and request.user.rol != 'admin':
            return Response(
                {"error": "No tienes permisos para ver los pedidos"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        status_filter = request.query_params.get('status')
        
        orders = Order.objects.all().select_related('user', 'shipping_info')
        
        if status_filter:
            orders = orders.filter(status=status_filter)
            
        serializer = OrderResponseSerializer(orders, many=True)
        return Response(serializer.data)

class VendedorOrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):
        # Verificar que el usuario sea vendedor
        if request.user.rol != 'vendedor' and request.user.rol != 'admin':
            return Response(
                {"error": "No tienes permisos para ver los detalles del pedido"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            order = Order.objects.get(id=order_id)
            serializer = OrderResponseSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class VendedorUpdateOrderStatusView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, order_id):
        # Verificar que el usuario sea vendedor
        if request.user.rol != 'vendedor' and request.user.rol != 'admin':
            return Response(
                {"error": "No tienes permisos para actualizar el estado del pedido"}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        try:
            order = Order.objects.get(id=order_id)
            
            new_status = request.data.get('status')
            current_status = order.status
            
            # Vendedores solo pueden actualizar de pendiente a enviado, o de enviado a entregado
            allowed_transitions = {
                'pendiente': ['enviado'],
                'enviado': ['entregado']
            }
            
            if (current_status not in allowed_transitions or 
                new_status not in allowed_transitions.get(current_status, [])):
                return Response(
                    {"error": "No puedes cambiar el estado del pedido a " + new_status}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
            order.status = new_status
            order.save()
            
            serializer = OrderResponseSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response(
                {"error": "Pedido no encontrado"}, 
                status=status.HTTP_404_NOT_FOUND
            )