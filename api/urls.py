from django.urls import path, include
from rest_framework import routers
from api import views
from django.conf import settings
from django.conf.urls.static import static
from .views import OrderDetailView, OrderListView, ProfileView, ClientOrderDetailView, SalesReportView, UpdateOrderStatusView,VerifyPaymentView
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
    path('articulos-por-categoria/<int:categoria_id>/', views.ArticulosPorCategoria.as_view(), name='articulos-por-categoria'),
    path('editar-articulo/<int:articulo_id>/', views.EditarArticulo.as_view(), name='editar-articulo'),
    path('cambiar_estado_articulo/<int:articulo_id>/', views.CambiarEstadoArticulo.as_view(), name='cambiar-estado-articulo'),
    
    #URL categorias producto base
    path('crear-categoria-producto-base/', views.CrearCategoriaProductoBase.as_view(), name='crear-categoria-producto-base'),
    path('listar-categoria-producto-base/', views.ListarCategoriaProductoBase.as_view(), name='listar-categoria-producto-base'),
    path('cambiar-estado-categoria-producto-base/<int:categoria_pb_id>/', views.CambiarEstadoCategoriaProductoBase.as_view(), name='cambiar-estado-categoria-producto-base'),
    path('editar-categoria-producto-base/<int:categoria_PB_id>/', views.EditarCategoriaProductoBase.as_view(), name='editar-categoria-producto-base'),
    
    #URL productos base
    path('crear-producto-base/', views.CrearProductoBase.as_view(), name='crear-producto-base'),
    path('listar-producto-base/', views.ListarProductoBase.as_view(), name='listar-producto-base'),
    path('cambiar_estado_producto/<int:producto_id>/', views.CambiarEstadoProductoBase.as_view(), name='cambiar-estado-producto-base'),
    path('editar-producto-base/<int:producto_id>/', views.EditarProductoBase.as_view(), name='editar-producto-base'),
    path('productos-por-categoria/<int:categoria_id>/', views.ProductosPorCategoria.as_view(), name='productos-por-categoria'),
    path('foto-producto/<int:foto_id>/', views.EliminarFotoProducto.as_view()),
    path("eliminar-producto-base/<int:producto_id>/", views.EliminarProductoBase.as_view()),
    
    #URL clientes
    path('listar-clientes/', views.ListarClientes.as_view(), name='listar-clientes'),
    path('editar-cliente/<int:cliente_id>/', views.EditarCliente.as_view(), name='editar-cliente'),
    path('cliente/pedidos/<int:order_id>/', ClientOrderDetailView.as_view(), name='cliente-order-detail'),
    #URL Vendedores
    path('crear-vendedor/', views.CrearVendedor.as_view(), name='crear-vendedor'),
    path('listar-vendedores/', views.ListarVendedores.as_view(), name='listar-vendedores'),
    path('cambiar-estado-vendedor/<int:vendedor_id>/', views.CambiarEstadoVendedor.as_view(), name='cambiar-estado-vendedor'),
    path('editar-vendedor/<int:vendedor_id>/', views.EditarVendedor.as_view(), name='editar-vendedor'),
    
    


    #CART
    path('add-to-cart/', views.AddToCart, name="add-to-cart"),
    path('cart/', views.CartView.as_view(), name="cart"),
    path('delete-from-cart/', views.DeleteFromCart, name="delete-from-cart"),
    path('update-cart/', views.UpdateCart, name="update-cart"),

    #PEDIDOS
    path('crear-pedido/', views.CreateOrderView.as_view(), name="crear-pedido"),
    path('listar-pedidos/', OrderListView.as_view(), name='listar-pedidos'),
    path('detalle-pedido/<int:order_id>/', OrderDetailView.as_view(), name='detalle-pedido'),
    path('informe-ventas/', SalesReportView.as_view(), name='informe-ventas'),
    path('verificar-pago/<int:order_id>/', VerifyPaymentView.as_view(), name='verify-payment'),
    path('actualizar-estado-pedido/<int:order_id>/', UpdateOrderStatusView.as_view(), name='actualizar-estado-pedido'),
    # Endpoint para refrescar tokens
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    #Catalogo-clientes
    path('catalogo-productos/', views.CatalogoProductoBase.as_view(), name='catalogo-productos'),
    path('producto/<int:producto_id>/', views.DetalleProductoBase.as_view(), name='detalle-producto'),


] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
