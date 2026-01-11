from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'prode_ganador_2026' 

# --- BASE DE DATOS TEMPORAL (Saldos en 0 para pruebas) ---
usuarios_db = {
    "admin": {"clave": "1234", "nivel": 2, "saldo": 0},
    "ayudante": {"clave": "5678", "nivel": 1, "saldo": 0},
    "lucas": {"clave": "prode01", "nivel": 0, "saldo": 0}
}

# Costo del cartón para la prueba (lo puse en 100 por defecto)
COSTO_CARTON = 100

partidos = [
    {'id': 1, 'local': 'Boca Juniors', 'visitante': 'River Plate'},
    {'id': 2, 'local': 'Independiente', 'visitante': 'Racing Club'},
    {'id': 3, 'local': 'San Lorenzo', 'visitante': 'Huracán'},
    {'id': 4, 'local': 'Estudiantes LP', 'visitante': 'Gimnasia LP'},
    {'id': 5, 'local': 'Rosario Central', 'visitante': 'Newell\'s'},
    {'id': 6, 'local': 'Talleres', 'visitante': 'Belgrano'},
    {'id': 7, 'local': 'Lanús', 'visitante': 'Banfield'},
    {'id': 8, 'local': 'Vélez Sarsfield', 'visitante': 'Argentinos Jrs'},
    {'id': 9, 'local': 'Defensa y Justicia', 'visitante': 'Tigre'},
    {'id': 10, 'local': 'Platense', 'visitante': 'Sarmiento'},
    {'id': 11, 'local': 'Atl. Tucumán', 'visitante': 'Central Córdoba'},
    {'id': 12, 'local': 'Godoy Cruz', 'visitante': 'Ind. Rivadavia'},
    {'id': 13, 'local': 'Instituto', 'visitante': 'Unión'},
    {'id': 14, 'local': 'Barracas Central', 'visitante': 'Riestra'},
    {'id': 15, 'local': 'Banfield', 'visitante': 'Lanús'}
]

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    user_input = request.form.get('usuario', '').strip().lower()
    pass_input = request.form.get('password', '').strip().lower()

    if user_input in usuarios_db and usuarios_db[user_input]['clave'] == pass_input:
        nivel = usuarios_db[user_input]['nivel']
        if nivel >= 1:
            # Importante: pasamos usuarios_db para que el Admin vea la lista
            return render_template('admin.html', usuario=user_input, nivel=nivel, usuarios=usuarios_db)
        else:
            saldo = usuarios_db[user_input]['saldo']
            return render_template('index.html', partidos=partidos, usuario=user_input, saldo=saldo, costo=COSTO_CARTON)
    else:
        flash('USUARIO O CONTRASEÑA INCORRECTOS')
        return redirect(url_for('home'))

# --- RUTA PARA QUE EL ADMIN CREE USUARIOS O CARGUE SALDO ---
@app.route('/admin/gestion_usuario', methods=['POST'])
def gestion_usuario():
    accion = request.form.get('accion')
    user_target = request.form.get('usuario_nombre', '').strip().lower()

    if accion == 'crear':
        clave = request.form.get('usuario_clave', '').strip().lower()
        saldo_ini = int(request.form.get('usuario_saldo', 0))
        if user_target and user_target not in usuarios_db:
            usuarios_db[user_target] = {"clave": clave, "nivel": 0, "saldo": saldo_ini}
            flash(f'ÉXITO: USUARIO {user_target.upper()} CREADO')
        else:
            flash('ERROR: EL USUARIO YA EXISTE O NOMBRE VACÍO')

    elif accion == 'cargar_saldo':
        try:
            monto = int(request.form.get('monto', 0))
            if user_target in usuarios_db:
                usuarios_db[user_target]['saldo'] += monto
                flash(f'SALDO CARGADO: ${monto} A {user_target.upper()}')
            else:
                flash('ERROR: USUARIO NO ENCONTRADO')
        except:
            flash('ERROR: MONTO INVÁLIDO')

    return redirect(url_for('home')) # Al terminar vuelve al login para que vuelvas a entrar y ver cambios

@app.route('/guardar_jugada', methods=['POST'])
def guardar_jugada():
    try:
        datos = request.json
        nombre_usuario = datos.get('usuario', '').lower()
        
        if nombre_usuario in usuarios_db:
            saldo_actual = usuarios_db[nombre_usuario]['saldo']
            if saldo_actual >= COSTO_CARTON:
                usuarios_db[nombre_usuario]['saldo'] -= COSTO_CARTON
                return jsonify({"status": "success", "mensaje": "¡JUGADA GUARDADA!", "nuevo_saldo": usuarios_db[nombre_usuario]['saldo']}), 200
            else:
                return jsonify({"status": "error", "mensaje": "SALDO INSUFICIENTE"}), 400
        return jsonify({"status": "error", "mensaje": "USUARIO NO ENCONTRADO"}), 404
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000)
