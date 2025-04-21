from django.urls import path, include
from rest_framework import routers
from api import views
from django.contrib import admin
from .models import Usuario
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from .views import CustomRegisterView


app_name = "api"
router=routers.DefaultRouter()
router.register(r'rol' ,views.RolViewSet)
router.register(r'usuario',views.UsuarioViewSet)
urlpatterns=[
    path('', views.index, name=""),

    #URL REGISTRO
    path('auth/registro/', CustomRegisterView.as_view(), name='custom_register'),

   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
