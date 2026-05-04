from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__, template_folder="templates", static_folder="static")

# Simulación de una base de datos de socios del cine
usuarios = []


@app.route('/')
def inicio():
    # Esta ruta busca el archivo inicio.html en la carpeta templates
    return render_template('inicio.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Aquí capturamos lo que el usuario escribe en el cine
        email = request.form.get('email')
        password = request.form.get('password')

        # Por ahora, cualquier login nos lleva al inicio
        return redirect(url_for('inicio'))

    return render_template('login.html')


if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
