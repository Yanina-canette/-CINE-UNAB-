class Usuario():
    def __init__(self,email,contraseña):
        self.email = email
        self. contraseña = contraseña

    def iniciar_sesion(self):
        pass

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