from datetime import datetime

class Pelicula:
    def __init__(self, data_json):
        self.id_pelicula = None
        self.api_id = data_json.get("id")
        self.titulo = data_json.get("title")
        self.sinopsis = data_json.get("overview")
        self.calificacion = data_json.get("vote_average")
        self.fecha_estreno = data_json.get("release_date")
        self.idioma = data_json.get("original_language")
        self.clasificacion = "N/A"
        self.director = None
        self.duracion = None

        # Manejo seguro de imágenes (evita URLs con "None" al final)
        poster = data_json.get("poster_path")
        backdrop = data_json.get("backdrop_path")
        self.poster_url = f"https://image.tmdb.org/t/p/w500{poster}" if poster else None
        self.imagen_carru = f"https://image.tmdb.org/t/p/w1280{backdrop}" if backdrop else None

        # Guardamos los IDs , los nombres se resuelven aparte
        self.genero_ids = data_json.get("genre_ids", [])
        self.genero = "N/A"  # Se completa después con el diccionario de géneros


class Sala:
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
        self.asientos_disponibles = sala.capacidad
        self.asientos_ocupados = [] 

    def verificar_disponibilidad(self, asiento):
        return asiento not in self.asientos_ocupados and asiento <= self.sala.capacidad

    def reservar_asiento(self, asiento):
        if self.verificar_disponibilidad(asiento):
            self.asientos_ocupados.append(asiento)
            self.asientos_disponibles -= 1
            return True
        return False

    def liberar_asiento(self, asiento):
        if asiento in self.asientos_ocupados:
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

class Entrada:
    def __init__(self,asiento,usuario,funcion,precio_final):
        pass


class Compra:
    def __init__(self, precio, fecha, funcion, asientos, es_estudiante:bool):
        self.__precio = precio
        self.__fecha = fecha
        self.__funcion = funcion
        self.__asientos = asientos
        self.__es_estudiante = es_estudiante
        
    def validar_asientos(self):
        asientos_por_fila = 5
        if self.__asientos == asientos_por_fila:
            return "El número de asientos es valido."
        else:
            return "El número de asientos no es valido."
        
        
    def calcular_total(self):
        total = float(self.__precio * self.__asientos)
        if self.__es_estudiante == True:
            return total/2
        else:
            return total
        
    def generar_fecha(self,fecha_compra:str):
        # En los atributos, se debe pasar la fecha en string de la siguiente manera para convertirla: "27-5-2026 (fecha) 15:00:00 (hora)"
        fecha_convertida = datetime.strptime(fecha_compra, "%d-%m-%Y %H:%M:%S")
        return fecha_convertida


class MetodoPago:
    def __init__(self, monto, titular):
        self.__monto = monto
        self.__titular = titular


# Pago con tarjeta
class PagoTarjeta(MetodoPago):
    def __init__(self, monto, titular, numero_tarjeta):
        super().__init__(monto, titular)
        self.__numero_tarjeta = numero_tarjeta

    def procesar_pago(self):
        return f"Pago realizado con tarjeta terminada en {self.__numero_tarjeta[-4:]}"


# Pago en efectivo
class PagoEfectivo(MetodoPago):
    def __init__(self, monto, titular, entregado):
        super().__init__(monto, titular)
        self.__entregado = entregado

    def calcular_vuelto(self, monto):
        return self.__entregado - monto

    def procesar_pago(self):
        vuelto = self.calcular_vuelto(2500)
        return f"Pago en efectivo realizado. Vuelto: ${vuelto}"


# Pago por mercado pago
class PagoMercadoPago(MetodoPago):
    def __init__(self, monto, titular):
        super().__init__(monto, titular)
        self.__link = "https://link.mercadopago.com.ar/karimsilva"

    def procesar_pago(self):
        return self.__link

