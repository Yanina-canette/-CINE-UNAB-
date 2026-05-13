from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from flask import session




app = Flask(__name__, template_folder="templates",
            static_folder="static")
app.secret_key = "clave_secreta"

# Simulación de una base de datos de socios del cine
usuario = []

conexion = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="cine_database"
    
)


@app.route('/')
def inicio():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    
    return render_template('inicio.html',
    usuario= session['usuario'])
    
        

    
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

        cursor = conexion.cursor()

        cursor.execute(
            "SELECT * FROM usuarios WHERE email=%s",
            (email,))

        usuario = cursor.fetchone()
        cursor.close()
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
        cursor.close()

        flash("Usuario registrado correctamente")

        return redirect(url_for('login'))

    return render_template('formulario.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email= request.form ['email']
        contraseña= request.form ['contraseña']

        cursor = conexion.cursor()

        cursor.execute(
            "SELECT nombre, password_hash FROM usuarios WHERE email=%s",
            (email,))

        usuario = cursor.fetchone()
        cursor.close()

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

    return render_template('login.html')


if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)

