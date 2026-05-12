from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__, template_folder="templates",
            static_folder="static")

# Simulación de una base de datos de socios del cine
usuarios = []


@app.route('/')
def inicio():
    return render_template('inicio.html')


@app.route('/formulario')
def formulario():
    return render_template('formulario.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email= request.form ['email']
        contraseña= request.form ['contraseña']
        confirmar= request.form ['confirmar']

    if contraseña != confirmar:
       flash("Contraseña incorrecta!")
       return redirect(url_for('formulario'))

    lista_email= []
    if email in lista_email:
       flash("Email ya existente")
       return redirect(url_for('login'))
       

    return render_template('login.html')





if __name__ == '__main__':
    # Esto enciende el servidor web
    app.run(debug=True)
