from django.urls import path, include
from rest_framework import routers
from api import views
from django.contrib import admin
#from .models import Persona
from django.conf import settings
from django.conf.urls.static import static
#from django.contrib.auth import views as auth_views


app_name = "api"
router=routers.DefaultRouter()
#router.register(r'rol' ,views.RolViewSet)
#router.register(r'persona',views.PersonaViewSet)
urlpatterns=[
    path('', views.index, name=""),

    #URLS LOGIN
    #path("sign-up/", views.CrearCliente.as_view(), name="sign-up"),
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
