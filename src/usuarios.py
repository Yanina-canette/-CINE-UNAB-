


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

    def cerrar_sesion(self):
        pass
    
    def actualizar_datos(self):
        pass







class Administrador(Usuario):
    def __init__(self, email, contraseña):
        super().__init__(email, contraseña)

    def selecionar_peliculas(self):
        pass

    def destacar_pelicula(self):
        pass

    def modificar_precios(self):
        pass

    def administrar_salas(self):
        pass

    def gestionar_horarios(self):
        pass
    


class Cliente(Usuario):
    def __init__(self, email, contraseña):
        super().__init__(email, contraseña)

    def comprar_entradas(self):
        pass

    def elegir_funciones(self):
        pass

    def seleccionar_asiento(self):
        pass

    def elegir_metodo_pago(self):
        pass

    def confirmar_compra(self):
        pass