from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import pooling
from flask import session
import os
import requests
from cartelera import Pelicula,Sala,Funcion,Entrada,Compra,MetodoPago,PagoEfectivo,PagoMercadoPago,PagoTarjeta
from usuarios import Usuario,Administrador,Cliente
from datetime import datetime, timedelta
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature



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

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'cineunabproyecto@gmail.com'
app.config['MAIL_PASSWORD'] = 'thtyjdkawkorzktb'
app.config['MAIL_DEFAULT_SENDER'] = ('CINE UNAB', 'cineunabproyecto@gmail.com')

mail = Mail(app)


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

        conexion = get_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email=%s", (email,))
            usuario = cursor.fetchone()
        finally:
            cursor.close()
            conexion.close()

        if usuario:
            # Generar token seguro (expira en 30 min)
            s = URLSafeTimedSerializer(app.secret_key)
            token = s.dumps(email, salt='recuperar-contraseña')

            link = url_for('nueva_contraseña', token=token, _external=True)

            try:
                msg = Message(
                    subject="🔐 Recuperar contraseña — CINE UNAB",
                    recipients=[email]
                )
                msg.html = render_template('email_recuperar.html', link=link)
                
                mail.send(msg)
            except Exception as e:
                print(f"Error al enviar mail: {e}")

        # Siempre mostramos el mismo mensaje (por seguridad)
        flash("Si el email está registrado, te enviamos un link para recuperar tu contraseña.")
        return redirect(url_for('recuperar'))

    return render_template('recuperar.html')


@app.route('/nueva_contraseña/<token>', methods=['GET', 'POST'])
def nueva_contraseña(token):
    s = URLSafeTimedSerializer(app.secret_key)
    try:
        email = s.loads(token, salt='recuperar-contraseña', max_age=1800)  # 30 min
    except SignatureExpired:
        flash("El link expiró. Solicitá uno nuevo.")
        return redirect(url_for('recuperar'))
    except BadSignature:
        flash("El link no es válido.")
        return redirect(url_for('recuperar'))

    if request.method == 'POST':
        nueva = request.form['nueva']
        confirmar = request.form['confirmar']

        if nueva != confirmar:
            flash("Las contraseñas no coinciden")
            return redirect(url_for('nueva_contraseña', token=token))

        if len(nueva) < 6:
            flash("La contraseña debe tener al menos 6 caracteres")
            return redirect(url_for('nueva_contraseña', token=token))

        nueva_hash = generate_password_hash(nueva)
        conexion = get_conexion()
        try:
            cursor = conexion.cursor()
            cursor.execute(
                "UPDATE usuarios SET password_hash=%s WHERE email=%s",
                (nueva_hash, email)
            )
            conexion.commit()
        finally:
            cursor.close()
            conexion.close()

        # Enviamos email de confirmación
        try:
            msg = Message(
                subject="✅ Contraseña actualizada — CINE UNAB",
                recipients=[email]
            )
            msg.html = render_template('email_cambio_contraseña.html')
            mail.send(msg)
        except Exception as e:
            print(f"Error al enviar mail: {e}")

        flash("✅ Contraseña actualizada correctamente")
        return redirect(url_for('login'))

    return render_template('nueva_contraseña.html', token=token)


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

        # Traemos la clasificación por edad
        url_clasificacion = f"https://api.themoviedb.org/3/movie/{api_id}/release_dates?api_key={API_KEY}"
        resp_clas = requests.get(url_clasificacion)
        datos_clas = resp_clas.json()
        clasificacion = "No disponible"
        for resultado in datos_clas.get("results", []):
            if resultado["iso_3166_1"] == "AR":
                for release in resultado.get("release_dates", []):
                    if release.get("certification"):
                        clasificacion = release["certification"]
                        break
        pelicula.clasificacion = clasificacion

        # Traemos el trailer
        url_videos = f"https://api.themoviedb.org/3/movie/{api_id}/videos?api_key={API_KEY}&language=es-ES"
        resp_videos = requests.get(url_videos)
        datos_videos = resp_videos.json()
        trailer_key = None
        for video in datos_videos.get("results", []):
            if video["type"] == "Trailer" and video["site"] == "YouTube":
                trailer_key = video["key"]
                break

        if not trailer_key:
            url_videos_en = f"https://api.themoviedb.org/3/movie/{api_id}/videos?api_key={API_KEY}&language=en-US"
            resp_videos_en = requests.get(url_videos_en)
            datos_videos_en = resp_videos_en.json()
            for video in datos_videos_en.get("results", []):
                if video["type"] == "Trailer" and video["site"] == "YouTube":
                    trailer_key = video["key"]
                    break

        pelicula.trailer_key = trailer_key
        print(f"Trailer key: {trailer_key}")

    except Exception as e:
        print(f"Error al traer la película: {e}")
        return redirect(url_for('peliculas'))

    # 2. Traemos las funciones de la DB para esta película
    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("""
            SELECT f.id, f.fecha, f.hora, s.nombre as sala, s.capacidad, s.tipo, s.precio as precio_sala
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
            tipo = request.form['tipo']
            precio = request.form['precio']
            cursor.execute("INSERT INTO salas (nombre, capacidad, tipo, precio) VALUES (%s, %s, %s, %s)",
        (nombre, capacidad, tipo, precio)
    )
            conexion.commit()
            flash("Sala creada correctamente")

        cursor.execute("SELECT * FROM salas")
        salas = cursor.fetchall()

    finally:
        cursor.close()
        conexion.close()

    return render_template("admin_salas.html", usuario=usuario, salas=salas)


@app.route('/admin/salas/<int:id>/editar', methods=['POST'])
def editar_sala(id):
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))
    
    tipo = request.form['tipo']
    precio = request.form['precio']
    
    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE salas SET tipo=%s, precio=%s WHERE id=%s",
            (tipo, precio, id)
        )
        conexion.commit()
        flash("Sala actualizada correctamente")
    finally:
        cursor.close()
        conexion.close()
    
    return redirect(url_for('admin_salas'))


@app.route('/admin/salas/<int:id>/eliminar', methods=['POST'])
def eliminar_sala(id):
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM asientos WHERE sala_id=%s", (id,))
        cursor.execute("DELETE FROM salas WHERE id=%s", (id,))
        conexion.commit()
        flash("Sala eliminada correctamente")
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('admin_salas'))


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
            fechas = request.form.get('fechas','')
            hora = request.form['hora']

            # Verificamos si la pelicula ya existe en la DB
            cursor.execute("SELECT id FROM peliculas WHERE api_id = %s", (api_id,))
            pelicula = cursor.fetchone()

            if not pelicula:
                # La guardamos en la DB
                cursor.execute("""
                    INSERT INTO peliculas (api_id, titulo, descripcion, genero, duracion_minutos, clasificacion, precio_base)
                    VALUES (%s, %s, 'N/A', 'N/A', 0, 'N/A', 0)
                """, (api_id, titulo))
                conexion.commit()
                pelicula_id = cursor.lastrowid
            else:
                pelicula_id = pelicula['id']

            lista_fechas = [f.strip() for f in fechas.split(',') if f.strip()]

            if not lista_fechas:
                flash("Seleccioná al menos un día en el calendario")
                return redirect(url_for('admin_funciones'))
            
            for fecha in lista_fechas:
                cursor.execute("""
                    INSERT INTO funciones (pelicula_id, sala_id, fecha, hora)
                    VALUES (%s, %s, %s, %s)
                    """, (pelicula_id, sala_id, fecha, hora))
            conexion.commit()
            flash(f"Se crearon {len(lista_fechas)} función(es) correctamente")

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


@app.route('/admin/funciones/<int:id>/editar', methods=['POST'])
def editar_funcion(id):
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    sala_id = request.form['sala_id']
    fecha = request.form['fecha']
    hora = request.form['hora']

    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute(
            "UPDATE funciones SET sala_id=%s, fecha=%s, hora=%s WHERE id=%s",
            (sala_id, fecha, hora, id)
        )
        conexion.commit()
        flash("Función actualizada correctamente")
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('admin_funciones'))


@app.route('/admin/funciones/<int:id>/eliminar', methods=['POST'])
def eliminar_funcion(id):
    usuario = session.get("usuario", None)
    if not usuario:
        return redirect(url_for('login'))

    conexion = get_conexion()
    try:
        cursor = conexion.cursor()
        cursor.execute("DELETE FROM reservas_temporales WHERE funcion_id=%s", (id,))
        cursor.execute("DELETE FROM asientos_funcion WHERE funcion_id=%s", (id,))
        cursor.execute("DELETE FROM funciones WHERE id=%s", (id,))
        conexion.commit()
        flash("Función eliminada correctamente")
    finally:
        cursor.close()
        conexion.close()

    return redirect(url_for('admin_funciones'))


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
        
        cursor.execute("""
            SELECT f.id, f.fecha, f.hora, s.nombre as sala, s.capacidad,
                   s.precio as precio_sala, p.titulo, p.api_id
            FROM funciones f
            JOIN salas s ON f.sala_id = s.id
            JOIN peliculas p ON f.pelicula_id = p.id
            WHERE f.id = %s
        """, (funcion_id,))
        funcion = cursor.fetchone()

    finally:
        cursor.close()
        conexion.close()

    return render_template("seleccionar_asientos.html", 
                         usuario=usuario,
                         funcion=funcion)



@app.route('/reservar_asiento', methods=['POST'])
def reservar_asiento():
    usuario = session.get("usuario")
    if not usuario:
        return {"error": "no_session"}, 401

    funcion_id = request.json.get('funcion_id')
    asiento_id = request.json.get('asiento_id')

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE nombre=%s", (usuario,))
        usuario_id = cursor.fetchone()['id']

        # Limpiamos reservas expiradas
        cursor.execute("DELETE FROM reservas_temporales WHERE expira_en < NOW()")
        conexion.commit()

        # Verificamos que no esté ocupado
        cursor.execute("""
            SELECT id FROM asientos_funcion 
            WHERE funcion_id=%s AND asiento_id=%s AND ocupado=TRUE
        """, (funcion_id, asiento_id))
        if cursor.fetchone():
            return {"error": "ocupado"}, 409

        # Verificamos que no esté reservado por otro
        cursor.execute("""
            SELECT id FROM reservas_temporales 
            WHERE funcion_id=%s AND asiento_id=%s
        """, (funcion_id, asiento_id))
        if cursor.fetchone():
            return {"error": "reservado"}, 409

        # Insertamos reserva temporal (10 minutos)
        expira = datetime.now() + timedelta(minutes=10)
        cursor.execute("""
            INSERT INTO reservas_temporales (usuario_id, funcion_id, asiento_id, expira_en)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, funcion_id, asiento_id, expira))
        conexion.commit()

        return {"ok": True, "expira_en": expira.isoformat()}

    finally:
        cursor.close()
        conexion.close()


@app.route('/liberar_asiento', methods=['POST'])
def liberar_asiento():
    usuario = session.get("usuario")
    if not usuario:
        return {"error": "no_session"}, 401

    funcion_id = request.json.get('funcion_id')
    asiento_id = request.json.get('asiento_id')

    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)
        cursor.execute("SELECT id FROM usuarios WHERE nombre=%s", (usuario,))
        usuario_id = cursor.fetchone()['id']

        cursor.execute("""
            DELETE FROM reservas_temporales 
            WHERE usuario_id=%s AND funcion_id=%s AND asiento_id=%s
        """, (usuario_id, funcion_id, asiento_id))
        conexion.commit()
        return {"ok": True}

    finally:
        cursor.close()
        conexion.close()


@app.route('/estado_asientos/<int:funcion_id>')
def estado_asientos(funcion_id):
    conexion = get_conexion()
    try:
        cursor = conexion.cursor(dictionary=True)

        # Limpiamos expirados
        cursor.execute("DELETE FROM reservas_temporales WHERE expira_en < NOW()")
        conexion.commit()

        # Todos los asientos de la sala
        cursor.execute("""
            SELECT a.id, a.fila, a.numero FROM asientos a
            JOIN funciones f ON f.sala_id = a.sala_id
            WHERE f.id = %s
            ORDER BY a.fila, a.numero
        """, (funcion_id,))
        todos = cursor.fetchall()

        # Ocupados definitivamente
        cursor.execute("""
            SELECT asiento_id FROM asientos_funcion 
            WHERE funcion_id=%s AND ocupado=TRUE
        """, (funcion_id,))
        ocupados = {r['asiento_id'] for r in cursor.fetchall()}

        # Reservados temporalmente
        cursor.execute("""
            SELECT asiento_id FROM reservas_temporales WHERE funcion_id=%s
        """, (funcion_id,))
        reservados = {r['asiento_id'] for r in cursor.fetchall()}

        for a in todos:
            if a['id'] in ocupados:
                a['estado'] = 'ocupado'
            elif a['id'] in reservados:
                a['estado'] = 'reservado'
            else:
                a['estado'] = 'libre'

        return {"asientos": todos}

    finally:
        cursor.close()
        conexion.close()


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
                   p.titulo, p.precio_base , s.precio as precio_sala
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
    precio = funcion['precio_sala']
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
    usuario = session.get("usuario")
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
        cursor.execute("SELECT id FROM usuarios WHERE nombre=%s", (usuario,))
        usuario_id = cursor.fetchone()['id']

        cursor.execute("""
            INSERT INTO compras (usuario_id, funcion_id, cantidad_entradas, precio_total)
            VALUES (%s, %s, %s, %s)
        """, (usuario_id, funcion_id, len(lista_asientos), total))
        conexion.commit()
        compra_id = cursor.lastrowid
        session['ultimo_compra_id'] = compra_id

        for asiento_id in lista_asientos:
            cursor.execute("""
                INSERT INTO compra_asientos (compra_id, asiento_id) VALUES (%s, %s)
            """, (compra_id, asiento_id))

            cursor.execute("""
                INSERT INTO asientos_funcion (funcion_id, asiento_id, ocupado)
                VALUES (%s, %s, TRUE)
                ON DUPLICATE KEY UPDATE ocupado = TRUE
            """, (funcion_id, asiento_id))

            cursor.execute("""
                DELETE FROM reservas_temporales 
                WHERE funcion_id=%s AND asiento_id=%s
            """, (funcion_id, asiento_id))

        conexion.commit()
        # Traemos el email del usuario
        cursor.execute("SELECT email FROM usuarios WHERE id=%s", (usuario_id,))
        email_usuario = cursor.fetchone()['email']

        # Enviamos el mail de confirmación
        try:
            msg = Message(
                subject="✅ Confirmación de compra — CINE UNAB",
                recipients=[email_usuario]
            )
            msg.html = f"""
            <div style="font-family:sans-serif; background:#0b132b; color:white; padding:40px; border-radius:12px;">
                <h1 style="color:#4ade80;">¡Compra exitosa! 🎬</h1>
                <p>Hola <strong>{usuario}</strong>, tu compra fue confirmada correctamente.</p>
                <div style="background:#1c2541; padding:20px; border-radius:8px; margin:20px 0;">
                    <p style="color:#94a3b8;">Número de compra</p>
                    <h2 style="color:#facc15;">#{compra_id}</h2>
                    <p style="color:#94a3b8;">Cantidad de entradas: <strong style="color:white;">{len(lista_asientos)}</strong></p>
                    <p style="color:#94a3b8;">Total pagado: <strong style="color:#4ade80;">${total}</strong></p>
                    <p style="color:#94a3b8;">Método de pago: <strong style="color:white;">{metodo_pago}</strong></p>
                </div>
                <p style="color:#94a3b8; font-size:0.9rem;">Presentá el número de compra al retirar tus entradas.</p>
                <p style="color:#94a3b8; font-size:0.8rem; margin-top:30px;">CINE UNAB — Bartolomé Mitre 1399</p>
            </div>
            """
            mail.send(msg)
        except Exception as e:
            print(f"Error al enviar mail: {e}")

        flash(f"¡Compra exitosa! Te enviamos un mail de confirmación.")
        return redirect(url_for('compra_exitosa'))

    finally:
        cursor.close()
        conexion.close()


@app.route('/compra_exitosa')
def compra_exitosa():
    usuario = session.get("usuario", None)
    numero_compra = session.pop('ultimo_compra_id', None)
    return render_template("compra_exitosa.html", usuario=usuario, numero_compra=numero_compra)


@app.route('/compra_fallida')
def compra_fallida():
    usuario = session.get("usuario", None)
    return render_template("compra_fallida.html", usuario=usuario)


@app.route('/precios')
def precios():
    usuario = session.get("usuario", None)
    return render_template("precios.html", usuario=usuario)


@app.route('/terminos')
def terminos():
    usuario = session.get("usuario", None)
    return render_template("terminos.html", usuario=usuario)


@app.route('/arrepentimiento', methods=['GET', 'POST'])
def arrepentimiento():
    usuario = session.get("usuario", None)
    if request.method == 'POST':
        flash("Tu solicitud fue recibida. Nos comunicaremos con vos dentro de las 72 horas hábiles.")
        return redirect(url_for('arrepentimiento'))
    return render_template("arrepentimiento.html", usuario=usuario)


if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
