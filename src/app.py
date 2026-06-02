from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import pooling
from flask import session
import os
import requests
from cartelera import Pelicula,Sala,Funcion,Entrada,Compra, MetodoPago
from usuarios import Usuario,Administrador,Cliente




app = Flask(__name__, template_folder="templates",
            static_folder="static")

app.secret_key = os.environ.get("SECRET_KEY", "fallback_solo_en_dev")


pool = pooling.MySQLConnectionPool(
    pool_name="cine_pool",
    pool_size=5,
    host="localhost",
    user="root",
    password="mysql0610",
    database="cine_database"
    
)


@app.context_processor
def inject_es_admin():
    usuario = session.get('usuario')
    es_admin = False
    if usuario:
        try:
            conexion = get_conexion()
            cursor = conexion.cursor(dictionary=True)
            cursor.execute("SELECT es_admin FROM usuarios WHERE nombre=%s", (usuario,))
            resultado = cursor.fetchone()
            es_admin = bool(resultado and resultado['es_admin'])
            cursor.close()
            conexion.close()
        except:
            pass
    return dict(es_admin=es_admin)

def get_conexion():
    return pool.get_connection()


@app.route('/') 
def inicio():
    return redirect(url_for('peliculas'))


@app.route('/logout')
def logout():
    session.pop('usuario',None)
    return redirect(url_for('login'))


@app.route('/formulario', methods=['GET', 'POST'])
def formulario():

    if request.method == "POST":

        nombre = request.form['nombre']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        es_estudiante = True if request.form['es_estudiante'] == 'si' else False
        email = request.form['email']
        contraseña = request.form['contraseña']
        confirmar = request.form['confirmar']

        if contraseña != confirmar:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('formulario'))

        # Manejo de imagen
        imagen_path = None
        if es_estudiante and 'imagen_estudiante' in request.files:
            imagen = request.files['imagen_estudiante']
            if imagen.filename != '':
                import uuid
                extension = imagen.filename.rsplit('.', 1)[-1].lower()
                nombre_archivo = f"{uuid.uuid4().hex}.{extension}"
                carpeta = os.path.join(os.path.dirname(__file__), 'static', 'uploads')
                os.makedirs(carpeta, exist_ok=True)
                imagen.save(os.path.join(carpeta, nombre_archivo))
                imagen_path = nombre_archivo

        conexion = get_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            if cursor.fetchone():
                flash("Email ya existente")
                return redirect(url_for('formulario'))

            contraseña_hash = generate_password_hash(contraseña)
            sql = """
            INSERT INTO usuarios(nombre, apellido, telefono, es_estudiante, email, password_hash, imagen_estudiante, verificado_estudiante)
            VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
            """
            estado = 'pendiente' if es_estudiante else None
            valores = (nombre, apellido, telefono, es_estudiante, email, contraseña_hash, imagen_path, estado)
            cursor.execute(sql, valores)
            conexion.commit()
            flash("Usuario registrado correctamente")
            return redirect(url_for('login'))

        finally:
            cursor.close()
            conexion.close()

    return render_template('formulario.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email= request.form ['email']
        contraseña= request.form ['contraseña']

        conexion = get_conexion()  
        try:

            cursor = conexion.cursor()

            cursor.execute(
            "SELECT nombre, password_hash FROM usuarios WHERE email=%s",
            (email,))

            usuario = cursor.fetchone()

            if usuario:

                nombre_db = usuario[0]
                hash_db = usuario[1]

                if check_password_hash(hash_db, contraseña):
                    session ['usuario'] = nombre_db
                    flash(f"Bienvenido {nombre_db}")
                    return redirect(url_for('inicio'))
                else:
                    flash("Contraseña incorrecta")
                    return redirect(url_for('login'))

            else:
                flash("Email no registrado")
                return redirect(url_for('login'))
            
        finally:
            cursor.close()      
            conexion.close() 
        
    return render_template('login.html')

@app.route('/recuperar', methods=['GET', 'POST'])
def recuperar():
    if request.method == 'POST':
        email = request.form['email']
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']

        if nueva != confirmar:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('recuperar'))

        conexion = get_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            usuario = cursor.fetchone()

            if not usuario:
                flash("Email no registrado")
                return redirect(url_for('recuperar'))

            nueva_hash = generate_password_hash(nueva)
            cursor.execute(
                "UPDATE usuarios SET password_hash=%s WHERE email=%s",
                (nueva_hash, email)
            )
            conexion.commit()
            flash("Contraseña actualizada correctamente")
            return redirect(url_for('login'))

        finally:
            cursor.close()
            conexion.close()

    return render_template('recuperar.html')

@app.route('/peliculas')
def peliculas():
    usuario = session.get("usuario", None)
    
    url = "https://api.themoviedb.org/3/movie/now_playing?api_key=9ca3c028ce5b15354d7a635e4a9db833&language=es-ES&region=AR"
    
    try:
        respuesta = requests.get(url)  # ✅ Sacamos verify=False
        datos = respuesta.json()
        peliculas_api = datos.get("results", [])
        
        lista_peliculas = [Pelicula(p) for p in peliculas_api[:6]]  # ✅ Usamos la clase
            
    except Exception as e:
        print(f"Error al conectar con la API: {e}")
        lista_peliculas = []

    return render_template("peliculas.html", usuario=usuario, peliculas=lista_peliculas)

@app.route('/pelicula/<int:api_id>')
def detalle_pelicula(api_id):
    usuario = session.get("usuario", None)

    # 1. Traemos los detalles de la película desde TMDB
    API_KEY = "9ca3c028ce5b15354d7a635e4a9db833"
    url = f"https://api.themoviedb.org/3/movie/{api_id}?api_key={API_KEY}&language=es-ES"
    
    try:
        respuesta = requests.get(url)
        datos = respuesta.json()
        pelicula = Pelicula(datos)
        pelicula.duracion = datos.get("runtime")
    except Exception as e:
        print(f"Error al traer la película: {e}")
        return redirect(url_for('peliculas'))

    # 2. Traemos las funciones de la DB para esta película
    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id, f.fecha, f.hora, s.nombre as sala, s.capacidad
            FROM funciones f
            JOIN salas s ON f.sala_id = s.id
            JOIN peliculas p ON f.pelicula_id = p.id
            WHERE p.api_id = %s AND f.fecha >= CURDATE()
            ORDER BY f.fecha, f.hora
        """, (api_id,))
        funciones = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

    return render_template("detalle_pelicula.html", usuario=usuario, pelicula=pelicula, funciones=funciones)

@app.route('/admin')
def admin():
    usuario = session.get("usuario", None)
    
    if not usuario:
        flash("Tenés que iniciar sesión")
        return redirect(url_for('login'))
    
    # Verificamos si es admin en la DB
    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT es_admin FROM usuarios WHERE nombre=%s", (usuario,))
        resultado = cursor.fetchone()
        
        if not resultado or not resultado['es_admin']:
            flash("No tenés permisos de administrador")
            return redirect(url_for('peliculas'))
            
    finally:
        cursor.close()
        conexion.close()
    
    return render_template("admin.html", usuario=usuario)

@app.route('/admin/salas', methods=['GET', 'POST'])
def admin_salas():
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        if request.method == 'POST':
            nombre = request.form['nombre']
            capacidad = request.form['capacidad']
            cursor.execute("INSERT INTO salas (nombre, capacidad) VALUES (%s, %s)", (nombre, capacidad))
            conexion.commit()
            flash("Sala creada correctamente")

        cursor.execute("SELECT * FROM salas")
        salas = cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

    return render_template("admin_salas.html", usuario=usuario, salas=salas)

@app.route('/admin/funciones', methods=['GET', 'POST'])
def admin_funciones():
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        if request.method == 'POST':
            api_id = request.form['api_id']
            titulo = request.form['titulo']
            sala_id = request.form['sala_id']
            fecha = request.form['fecha']
            hora = request.form['hora']

            # Verificamos si la pelicula ya existe en la DB
            cursor.execute("SELECT id FROM peliculas WHERE api_id = %s", (api_id,))
            pelicula = cursor.fetchone()

            if not pelicula:
                # La guardamos en la DB
                cursor.execute("""
                    INSERT INTO peliculas (api_id, titulo, descripcion, genero, duracion_minutos, clasificacion, precio_base)
                    VALUES (%s, %s, 'N/A', 'N/A', 0, 'N/A', 1500)
                """, (api_id, titulo))
                conexion.commit()
                pelicula_id = cursor.lastrowid
            else:
                pelicula_id = pelicula['id']

            cursor.execute("""
                INSERT INTO funciones (pelicula_id, sala_id, fecha, hora)
                VALUES (%s, %s, %s, %s)
            """, (pelicula_id, sala_id, fecha, hora))
            conexion.commit()
            flash("Función creada correctamente")

        cursor.execute("SELECT * FROM salas")
        salas = cursor.fetchall()

        cursor.execute("""
            SELECT f.id, p.titulo, s.nombre as sala, f.fecha, f.hora
            FROM funciones f
            JOIN peliculas p ON f.pelicula_id = p.id
            JOIN salas s ON f.sala_id = s.id
            ORDER BY f.fecha, f.hora
        """)
        funciones = cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

    return render_template("admin_funciones.html", usuario=usuario, salas=salas, funciones=funciones)



@app.route('/perfil')
def perfil():
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre, apellido, email, telefono, es_estudiante FROM usuarios WHERE nombre=%s", (usuario,))
        datos = cursor.fetchone()

        cursor.execute("""
            SELECT c.id, c.cantidad_entradas, c.precio_total, c.fecha_compra,
                   p.titulo, f.fecha, f.hora, s.nombre as sala
            FROM compras c
            JOIN funciones f ON c.funcion_id = f.id
            JOIN peliculas p ON f.pelicula_id = p.id
            JOIN salas s ON f.sala_id = s.id
            WHERE c.usuario_id = %s
            ORDER BY c.fecha_compra DESC
        """, (datos['id'],))
        compras = cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

    return render_template("perfil.html", usuario=usuario, datos=datos, compras=compras)
    

@app.route('/admin/estudiantes')
def admin_estudiantes():
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, nombre, apellido, email, imagen_estudiante, verificado_estudiante 
            FROM usuarios 
            WHERE es_estudiante = 1 
            ORDER BY verificado_estudiante ASC
        """)
        estudiantes = cursor.fetchall()
    finally:
        cursor.close()
        conexion.close()

    return render_template('admin_estudiantes.html', usuario=usuario, estudiantes=estudiantes)


@app.route('/admin/estudiantes/<int:id>/aprobar', methods=['POST'])
def aprobar_estudiante(id):
    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE usuarios SET verificado_estudiante='aprobado' WHERE id=%s", (id,))
        conexion.commit()
        flash("Estudiante aprobado")
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for('admin_estudiantes'))


@app.route('/admin/estudiantes/<int:id>/rechazar', methods=['POST'])
def rechazar_estudiante(id):
    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("UPDATE usuarios SET verificado_estudiante='rechazado' WHERE id=%s", (id,))
        conexion.commit()
        flash("Estudiante rechazado")
    finally:
        cursor.close()
        conexion.close()
    return redirect(url_for('admin_estudiantes'))

@app.route('/comprar/<int:funcion_id>')
def seleccionar_asientos(funcion_id):
    usuario = session.get("usuario", None)
    if not usuario:
        flash("Tenés que iniciar sesión para comprar entradas")
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        
        # Traemos info de la función
        cursor.execute("""
            SELECT f.id, f.fecha, f.hora, s.nombre as sala, s.capacidad,
                   p.titulo, p.api_id
            FROM funciones f
            JOIN salas s ON f.sala_id = s.id
            JOIN peliculas p ON f.pelicula_id = p.id
            WHERE f.id = %s
        """, (funcion_id,))
        funcion = cursor.fetchone()

        # Traemos asientos ocupados para esta función
        cursor.execute("""
            SELECT numero_asiento FROM asientos_funcion
            WHERE funcion_id = %s AND ocupado = TRUE
        """, (funcion_id,))
        ocupados = [row['numero_asiento'] for row in cursor.fetchall()]

    finally:
        cursor.close()
        conexion.close()

    return render_template("seleccionar_asientos.html", 
                         usuario=usuario,
                         funcion=funcion, 
                         ocupados=ocupados)

@app.route('/pagar', methods=['GET', 'POST'])
def pagar():
    usuario = session.get("usuario", None)
    if not usuario:
        flash("Tenés que iniciar sesión para comprar entradas")
        return redirect(url_for('login'))

    funcion_id = request.form.get('funcion_id')
    asientos = request.form.get('asientos')

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id, f.fecha, f.hora, s.nombre as sala,
                   p.titulo, p.precio_base
            FROM funciones f
            JOIN salas s ON f.sala_id = s.id
            JOIN peliculas p ON f.pelicula_id = p.id
            WHERE f.id = %s
        """, (funcion_id,))
        funcion = cursor.fetchone()

        cursor.execute("SELECT es_estudiante, verificado_estudiante FROM usuarios WHERE nombre=%s", (usuario,))
        usuario_db = cursor.fetchone()
        es_estudiante = usuario_db and usuario_db['es_estudiante'] and usuario_db['verificado_estudiante'] == 'aprobado'

    finally:
        cursor.close()
        conexion.close()

    lista_asientos = [int(a) for a in asientos.split(',')]
    precio = 1500
    total = len(lista_asientos) * precio
    if es_estudiante:
        total = total / 2

    return render_template("pagar.html",
                         usuario=usuario,
                         funcion=funcion,
                         asientos=lista_asientos,
                         total=total)

@app.route('/confirmar_compra', methods=['POST'])
def confirmar_compra():
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    funcion_id = request.form.get('funcion_id')
    asientos = request.form.get('asientos')
    total = request.form.get('total')
    metodo_pago = request.form.get('metodo_pago')

    lista_asientos = [int(a) for a in asientos.split(',')]

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Traemos el id del usuario
        cursor.execute("SELECT id, es_estudiante FROM usuarios WHERE nombre=%s", (usuario,))
        usuario_db = cursor.fetchone()
        usuario_id = usuario_db['id']

        # Guardamos la compra
        cursor.execute("""
            INSERT INTO compras (usuario_id, funcion_id, cantidad_entradas, precio_total)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, funcion_id, len(lista_asientos), total))
        conexion.commit()

        # Marcamos los asientos como ocupados
        for numero in lista_asientos:
            cursor.execute("""
                INSERT INTO asientos_funcion (funcion_id, numero_asiento, ocupado)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE ocupado = TRUE
            """, (funcion_id, numero))
        conexion.commit()

        flash(f"¡Compra realizada con éxito! Método: {metodo_pago}")
        return redirect(url_for('compra_exitosa'))

    finally:
        cursor.close()
        conexion.close()


@app.route('/compra_exitosa')
def compra_exitosa():
    usuario = session.get("usuario", None)
    return render_template("compra_exitosa.html", usuario=usuario)  

@app.route('/compra_fallida')
def compra_fallida():
    usuario = session.get("usuario", None)
    return render_template("compra_fallida.html", usuario=usuario)



if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
