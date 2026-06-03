from werkzeug.security import check_password_hash, generate_password_hash
from cartelera import Funcion, compra, MetodoPago
from datetime import datetime


class Usuario():
    def __init__(self,nombre,email,contraseña):
        self.__nombre = nombre
        self.__email = email
        self. __contraseña = contraseña
    
    def get_nombre(self):
        return self.__nombre
    
    def set_nombre(self, nombre):
        self.__nombre = nombre

    def get_email(self):
        return self.__email
    
    def set_email(self,email):
        self.__email = email

    def get_contraseña(self):
        return self.__contraseña
    
    def set_contraseña(self, contraseña):
        self.__contraseña = contraseña

    

    def iniciar_sesion(self,contraseña_ingresada):
        if check_password_hash(self.__contraseña, contraseña_ingresada):
            return True
        return False




class Administrador(Usuario):
    def __init__(self,nombre, email, contraseña):
        super().__init__(nombre,email,contraseña)

    def selecionar_peliculas(self):
        pass

    def destacar_pelicula(self):
        pass

    def modificar_precios(self,conexion):
        pass

    def administrar_salas(self):
        pass

    def gestionar_horarios(self):
        pass
    


class Cliente(Usuario):
    def __init__(self,nombre, email, contraseña):
        super().__init__(nombre,email, contraseña)

    def comprar_entradas(self,funcion,asiento,metodo_pago):
        asiento_reservado = self.seleccionar_asiento(funcion, asiento)
        if asiento_reservado:
            pago = self.elegir_metodo_pago(metodo_pago)
            return self.confirmar_compra(funcion,asiento,pago)
        return "No se pudo completar la compra"
        

    def elegir_funciones(self,funciones):
        return funciones

    def seleccionar_asiento(self,funcion,asiento):
        return funcion.reservar_asientos(asiento)

    def elegir_metodo_pago(self,metodo_pago):
        return metodo_pago.procesar_pago()
      

    def confirmar_compra(self,funcion,asiento,pago):
        nueva_compra = compra(
            precio= funcion.precio,
            fecha= datetime.now(),
            funcion= funcion,
            asientos= asiento
        )
        total = nueva_compra.calcular_total()
        return {
            "total": total,
            "pago": pago,
            "funcion": funcion.mostrar_funcion()
        }
        