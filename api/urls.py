from django.urls import path, include
from rest_framework import routers
from api import views
from django.conf import settings
from django.conf.urls.static import static
from .views import ProfileView, CrearProductoBase, ListarProductoBase
from rest_framework_simplejwt.views import TokenRefreshView

app_name = "api"
router=routers.DefaultRouter()
router.register(r'rol' ,views.RolViewSet)
router.register(r'usuario',views.UsuarioViewSet)
urlpatterns=[
    path('', views.index, name=""),

    #URLS LOGIN
    path("sign-up/", views.CrearCliente.as_view(), name="sign-up"),
    path("sign-in/", views.LoginView.as_view(), name="sign-in"),
    path('profile/', ProfileView.as_view(), name='profile'),

    # URLS recuperación de contraseña
    path("recover-password/", views.RecoverPasswordView.as_view(), name="recover-password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),

    #URL categoría-artículo
    path('crear-categoria-articulo/', views.CrearCategoriaArticulo.as_view(), name='crear-categoria-articulo'),
    path('listar-categoria-articulo/', views.ListarCategoriaArticulo.as_view(), name='listar-categoria-articulo'),
    path('cambiar-estado-categoria-articulo/<int:categoria_articulo_id>/', views.CambiarEstadoCategoriaArticulo.as_view(), name='cambiar-estado-categoria-articulo'),
    path('editar-categoria-articulo/<int:categoria_articulo_id>/', views.EditarCategoriaArticulo.as_view(), name='editar-categoria-articulo'),
    #path('articulos/cambio_estado/<int:articulo_id>/', views.ToggleArticuloEstadoAPIView.as_view(), name='toggle-articulo-estado'),
    
    # Ruta artículo
    path('crear-articulo/', views.CrearArticulo.as_view(), name='crear-articulo'),
    path('listar-articulos/', views.ListarArticulos.as_view(), name='listar-articulos'),
    #falta cambiar estado articulo
    #path('editar_articulo/<int:articulo_id>/', views.EditarArticulo.as_view(), name='editar_articulo'),
    #path('articulo/<int:id>/', views.ArticuloDetailView.as_view(), name='articulo-detail'),
    #path('articulos_por_categoria/<int:categoria_id>/', views.ArticuloPorCategoria.as_view(), name='articulos_por_categoria'),


    #URL categorias producto base
    path('crear-categoria-producto-base/', views.CrearCategoriaProductoBase.as_view(), name='crear-categoria-producto-base'),
    path('listar-categoria-producto-base/', views.ListarCategoriaProductoBase.as_view(), name='listar-categoria-producto-base'),
    path('cambiar-estado-categoria-producto-base/<int:categoria_articulo_id>/', views.CambiarEstadoCategoriaProductoBase.as_view(), name='cambiar-estado-categoria-producto-base'),
    path('editar-categoria-producto-base/<int:categoria_PB_id>/', views.EditarCategoriaProductoBase.as_view(), name='editar-categoria-producto-base'),
    
    #URL productos base
    path('crear-producto-base/', views.CrearProductoBase.as_view(), name='crear-producto-base'),
    path('listar-producto-base/', views.ListarProductoBase.as_view(), name='listar-producto-base'),
    #path('cambiar_estado_producto/<int:producto_id>/', views.CambiarEstadoProductoBase.as_view(), name='cambiar_estado_producto'),    
    #path('editar-producto-base/<int:producto_id>/', views.EditarProductoBase2.as_view(), name='editar_producto_base'),
    #path('productos_por_categoria/<int:categoria_id>/', views.ProductosPorCategoria.as_view(), name='productos_por_categoria'),


    #URL clientes
    path('listar-clientes/', views.ListarClientes.as_view(), name='listar-clientes'),
    path('editar-cliente/<int:cliente_id>/', views.EditarCliente.as_view(), name='editar-cliente'),

    #URL Vendedores
    path('listar-vendedores/', views.ListarVendedores.as_view(), name='listar-vendedores'),
    path('editar-vendedor/<int:vendedor_id>/', views.EditarVendedor.as_view(), name='editar-vendedor'),
    path('cambiar-estado-vendedor/<int:vendedor_id>/', views.CambiarEstadoVendedor.as_view(), name='cambiar-estado-vendedor'),

    # Endpoint para refrescar tokens
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
