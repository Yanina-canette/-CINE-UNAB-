from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder="templates",
            static_folder="static")

# Simulación de una base de datos de socios del cine
usuarios = []


@app.route('/')
def inicio():
    # Esta ruta busca el archivo inicio.html en la carpeta templates
    return render_template('inicio.html')


@app.route('/login')
def registro():
    return render_template('login.html')


@app.route('/formulario')
def formulario():
    return render_template('formulario.html')


if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
