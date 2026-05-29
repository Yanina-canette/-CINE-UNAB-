class Pelicula:
    def __init__(self, data_json):
        # Asignación automática usando .get() para evitar errores si falta algo
        self.id_pelicula = None 
        self.api_id = data_json.get("id")
        self.titulo = data_json.get("title")
        self.sinopsis = data_json.get("overview")
        self.calificacion = data_json.get("vote_average")
        self.fecha_estreno = data_json.get("release_date")
        self.imagen = f"https://image.tmdb.org/t/p/w500{data_json.get('poster_path')}"
        
        # Atributos con valores por defecto si no vienen en este endpoint
        self.genero = data_json.get("genre_ids", "N/A")
        self.director = "Pendiente" 
        self.duracion = 0
        self.idioma = data_json.get("original_language")
        self.clasificacion = "N/A"

    def obtenerDetalles(self):
        return f"{self.titulo} ({self.fecha_estreno[:4]})"

# --- Así queda tu lógica principal mucho más limpia ---
peliculas = []
for item in data["results"]:
    nueva_peli = Pelicula(item)
    peliculas.append(nueva_peli)
    

class sala:
    def __init__(self, numero_sala,capacidad, tipo_sala):
        self.numero_sala = numero_sala
        self.capacidad = capacidad
        self.tipo_sala = tipo_sala

        # lista de asientos en la sala
        self.asientos = []

        for numero in range (1, capacidad + 1):

            asiento = {
                "numero": numero,
                "ocupado": False
            }

            self.asientos.append(asiento)

    def mostrar_asientos(self):

        return self.asientos

    def reservar_asiento(self, numero_asiento):

        for asiento in self.asientos:

            if asiento ["numero"] == numero_asiento:
                if asiento ["ocupado"] == False:

                    asiento ["ocupado"] = True
                    return "Asiento reservado" 

                else: return "Asiento ocupado"       


class Funcion:
    def __init__(self,fecha,horario,sala,pelicula,precio):
        self.fecha = fecha
        self.horario = horario
        self.sala = sala
        self.pelicula = pelicula
        self.precio = precio
        self.asientos_disponibles = sala.cantidad_asientos
        self.asientos_ocupados = [] 

    def verificar_disponibilidad(self, asiento):
        return asiento not in self.asientos_ocupados and asiento <= self.sala.cantidad_asientos

    def reservar_asiento(self, asiento):
        if self.verificar_disponibilidad(asiento):
            self.asientos_ocupados.append(asiento)
            self.asientos_disponibles -= 1
            return True
        return False

    def liberar_asiento(self, asiento):
        if asiento in self.asiento_ocupados:
            self.asientos_ocupados.remove(asiento)
            self.asientos_disponibles += 1
            return True
        return False


    def mostrar_funcion(self):

        print("Película:", self.pelicula)
        print("Fecha:", self.fecha)
        print("Horario:", self.horario)
        print("Sala:", self.sala)
        print("Precio:", self.precio)

class entrada:
    def _init_(self,asiento,usuario,funcion,precio_final):
        pass

import datetime
#Se importa datetime para las fechas.

class compra:
    def _init_(self, precio, fecha, funcion, asientos):
        self.__precio = precio
        self.__fecha = fecha
        self.__funcion = funcion
        self.__asientos = asientos
        
    def validar_asientos(self):
        asientos_por_fila = 5
        if self.__asientos == asientos_por_fila:
            return "El número de asientos es valido."
        else:
            return "El número de asientos no es valido."
        
        
    def calcular_total(self):
        total = float(self_precio * self_asientos)
        return total
        
    def generar_fecha(fecha_compra:str):
        # En los atributos, se debe pasar la fecha en string de la siguiente manera para convertirla: "27-5-2026 (fecha) 15:00:00 (hora)"
        fecha_convertida = datetime.strptime(fecha_compra, "%d-%m-%Y %H:%M:%S")
        return fecha_convertida


class metodo_pago:
    def _init(self,efectivo,tarjeta_deb,tarjeta_cred,mercado_pago):
        pass

    def elegir_pago(self):
        pass

    def aprobar_compra(self):
        pass