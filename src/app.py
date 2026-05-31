from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import pooling
from flask import session
import os
import requests
from cartelera import Pelicula,Sala,Funcion,Entrada,Compra, Metodo_pago
from usuarios import Usuario,Administrador,Cliente
from dotenv import load_dotenv          
load_dotenv()  




app = Flask(__name__, template_folder="templates",
            static_folder="static")

app.secret_key = os.environ.get("SECRET_KEY", "fallback_solo_en_dev")


pool = pooling.MySQLConnectionPool(
    pool_name="cine_pool",
    pool_size=5,
    host=os.getenv('DB_HOST'),
    port=int(os.getenv('DB_PORT', '3306')),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),   
    use_pure=True  
)

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
            flash("las contraseñas no coinciden")
            return redirect(url_for('formulario'))
        
        conexion = get_conexion() 

        try:
            cursor = conexion.cursor()

            cursor.execute(
            "SELECT * FROM usuarios WHERE email=%s",
            (email,))

            usuario = cursor.fetchone()
        
            if usuario:
                flash("Email ya existente")
                return redirect(url_for('formulario'))
        
            contraseña_hash = generate_password_hash(contraseña)

            sql = """
            INSERT INTO usuarios(nombre,apellido,telefono,es_estudiante,email,password_hash)
            VALUES(%s,%s,%s,%s,%s,%s)
            """

            valores = (nombre, apellido, telefono, es_estudiante, email, contraseña_hash)

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
        cursor.execute("SELECT nombre, apellido, email, telefono, es_estudiante FROM usuarios WHERE nombre=%s", (usuario,))
        datos = cursor.fetchone()
    finally:
        cursor.close()
        conexion.close()

    return render_template("perfil.html", usuario=usuario, datos=datos)

if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
