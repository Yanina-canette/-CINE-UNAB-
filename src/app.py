import requests
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from mysql.connector import pooling
from flask import session
import os




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

def get_conexion():
    return pool.get_connection()

@app.route('/')
def inicio():
    usuario = session.get('usuario', None)
    return render_template('inicio.html', usuario=usuario)
        
    
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
        es_estudiante = request.form ['es_estudiante']
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

#   NUEVA RUTA PARA LA API DE PELÍCULAS
@app.route("/peliculas")
def peliculas():
    usuario = session.get("usuario", None)
    
   
    url = "https://api.themoviedb.org/3/movie/now_playing?api_key=9ca3c028ce5b15354d7a635e4a9db833&language=es-ES&region=AR"
    
    try:
        respuesta = requests.get(url, verify=False)
        datos = respuesta.json()
        peliculas_api = datos.get("results", [])
        
       
        lista_peliculas = []
        for peli in peliculas_api[:6]:
            imagen_hd = f"https://image.tmdb.org/t/p/original{peli.get('poster_path')}" if peli.get('poster_path') else None
            imagen_normal = f"https://image.tmdb.org/t/p/w500{peli.get('poster_path')}" if peli.get('poster_path') else None
            
            # 2. Guardamos ambas en el diccionario
            lista_peliculas.append({
                "titulo": peli.get("title"),
                "descripcion": peli.get("overview"),
                "imagen_carru": imagen_hd,       # <--- Alta calidad para el carrusel
                "imagen_tarjeta": imagen_normal  # <--- Calidad normal para las tarjetas
            })
            
    except Exception as e:
        print(f"Error al conectar con la API de películas: {e}")
        lista_peliculas = []  

    # 3. Le pasamos las películas procesadas al HTML
    return render_template("peliculas.html", usuario=usuario, peliculas=lista_peliculas)



if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)

