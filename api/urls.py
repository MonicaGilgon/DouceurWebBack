from django.urls import path, include
from rest_framework import routers
from api import views
from django.contrib import admin
from .models import Usuario
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views


app_name = "api"
router=routers.DefaultRouter()
router.register(r'rol' ,views.RolViewSet)
router.register(r'usuario',views.UsuarioViewSet)
urlpatterns=[
    path('', views.index, name=""),

    #URLS LOGIN
    path("sign-up/", views.CrearCliente.as_view(), name="sign-up"),
    path("sign-in/", views.LoginView.as_view(), name="sign-in"),
   

   #URL categoría-artículo
   path('crear-categoria-articulo/', views.CrearCategoriaArticulo.as_view(), name='crear-categoria-articulo'),
   path('listar-categoria-articulo/', views.ListarCategoriaArticulo.as_view(), name='listar-categoria-articulo'),
   path('cambiar-estado-categoria-articulo/<int:categoria_articulo_id>/', views.CambiarEstadoCategoriaArticulo.as_view(), name='cambiar-estado-categoria-articulo'),
   path('editar-categoria-articulo/<int:categoria_articulo_id>/', views.EditarCategoriaArticulo.as_view(), name='editar-categoria-articulo'),
   #path('articulos/cambio_estado/<int:articulo_id>/', views.ToggleArticuloEstadoAPIView.as_view(), name='toggle-articulo-estado'),
    
    #URL categorias producto base
    path('crear-categoria-producto-base/', views.CrearCategoriaProductoBase.as_view(), name='crear-categoria-producto-base'),
    path('listar-categoria-producto-base/', views.ListarCategoriaProductoBase.as_view(), name='listar-categoria-producto-base'),
    path('cambiar-estado-categoria-producto-base/<int:categoria_articulo_id>/', views.CambiarEstadoCategoriaProductoBase.as_view(), name='cambiar-estado-categoria-producto-base'),
    path('editar-categoria-producto-base/<int:categoria_PB_id>/', views.EditarCategoriaProductoBase.as_view(), name='editar-categoria-producto-base'),
    



] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
