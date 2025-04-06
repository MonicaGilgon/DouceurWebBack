from django.db import models

class Rol(models.Model):
    nombre = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre

class Persona(models.Model):
    nombre_completo = models.CharField(max_length=150)
    telefono = models.CharField(max_length=15)
    direccion = models.CharField(max_length=255)

    class Meta:
        abstract = True

class Usuario(Persona):
    correo = models.EmailField(unique=True)
    contrasenia = models.CharField(max_length=128)
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    estado = models.BooleanField(default=True)

    def __str__(self):
        return self.correo

    def iniciarSesion(self):
        pass

    def cerrarSesion(self):
        pass

    def reestablecerContrasenia(self, nueva_contrasenia):
        self.contrasenia = nueva_contrasenia
        self.save()

    def actualizarPerfil(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.save()