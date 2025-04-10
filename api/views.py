from rest_framework import viewsets, status, generics
from rest_framework.views import APIView
from .serializers import (RolSerializer, UsuarioSerializer)
from .models import (Rol, Usuario)
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from rest_framework.response import Response
from django.contrib.auth.hashers import make_password
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import check_password


 #INDEX
def index(request):
    return HttpResponse("Bienvenido a la API de Douceur")


#////////////////////////////////////////////////////////
#CLIENTES
#REGISTRO DE CLIENTES
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

#LOGIN CLIENTE
class LoginView(APIView):
    def post(self, request):
        #products = ProductoBase.objects.all()
        #categories = CategoriaProductoBase.objects.all()

        if request.user.is_authenticated:
            return redirect("api:index")
    
        if request.method == "POST":
            correo = request.data.get("correo")
            password = request.data.get("password")
            try:
                # Intentamos obtener el usuario a partir del correo electrónico
                user = Usuario.objects.get(correo=correo)
                # Autenticamos al usuario usando el nombre de usuario y la contraseña
                if user.check_password(password):
                    # Autenticación manual exitosa
                    # Verificar si el vendedor está desactivado
                    #if user.is_vendedor and not user.estado:
                     #   return Response({"error": "El vendedor está deshabilitado."}, status=403)
                        #return render(request, "userauths/sign-in.html", {"products": products, "categories": categories})
                    return Response({
                        "message": "Inicio de sesión exitoso",
                        "usuario": {
                            "id": user.id,
                            "nombre": user.nombre_completo,
                            "correo": user.correo,
                            "rol": user.rol.nombre
                        }
                    }, status=200)
                else:
                    return Response({"error": "Contraseña incorrecta"}, status=401)

            except Usuario.DoesNotExist:
                return Response({"error": "No existe ninguna cuenta registrada con este correo"}, status=404)

    

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