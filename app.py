import os
import base64
import datetime
# AGREGAMOS: session, redirect y url_for
from flask import Flask, render_template, request, jsonify, session, redirect, url_for

app = Flask(__name__)
# IMPORTANTE: Necesitas una clave secreta para que las sesiones funcionen
app.secret_key = 'tu_clave_secreta_super_segura' 

# BASE DE DATOS - 15 PARTIDOS
db = {
    'usuarios': {
        'laura': {'password': '123', 'saldo': 500, 'jugadas': [], 'imagenes_cartones': []},
        'juan': {'password': '456', 'saldo': 1200, 'jugadas': [], 'imagenes_cartones': []}
    },
    'partidos': [
        {'local': 'RIVER PLATE', 'visitante': 'BOCA JUNIORS'},
        {'local': 'RACING', 'visitante': 'INDEPENDIENTE'},
        {'local': 'SAN LORENZO', 'visitante': 'HURACAN'},
        {'local': 'ESTUDIANTES LP', 'visitante': 'GIMNASIA LP'},
        {'local': 'ROSARIO CENTRAL', 'visitante': 'NEWELLS'},
        {'local': 'TALLERES', 'visitante': 'BELGRANO'},
        {'local': 'LANUS', 'visitante': 'BANFIELD'},
        {'local': 'VELEZ', 'visitante': 'PLATENSE'},
        {'local': 'COLON', 'visitante': 'UNION'},
        {'local': 'ATL. TUCUMAN', 'visitante': 'CENTRAL CORDOBA'},
        {'local': 'GODOY CRUZ', 'visitante': 'INDEP. RIVADAVIA'},
        {'local': 'ARGENTINOS JRS', 'visitante': 'DEF. Y JUSTICIA'},
        {'local': 'TIGRE', 'visitante': 'BARRACAS CENTRAL'},
        {'local': 'INSTITUTO', 'visitante': 'SARMIENTO'},
        {'local': 'RIESTRA', 'visitante': 'DEPORTIVO MAIPU'}
    ]
}

UPLOAD_FOLDER = os.path.join('static', 'comprobantes')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- RUTA DE LOGIN (La que tenías antes probablemente fuera de Flask) ---
@app.route('/')
def login_page():
    # Si ya está logueado, mandarlo al prode
    if 'usuario' in session:
        return redirect(url_for('home'))
    return render_template('login.html') # Asegúrate que tu archivo de login se llame así

@app.route('/verificar_login', methods=['POST'])
def verificar_login():
    user = request.form.get('usuario')
    pas = request.form.get('password')
    
    if user in db['usuarios'] and db['usuarios'][user]['password'] == pas:
        session['usuario'] = user
        session['saldo'] = db['usuarios'][user]['saldo']
        return redirect(url_for('home'))
    else:
        return "Usuario o contraseña incorrectos", 401

# --- RUTA PRINCIPAL PROTEGIDA ---
@app.route('/index')
def home():
    # SI NO HAY SESIÓN, MANDA AL LOGIN
    if 'usuario' not in session:
        return redirect(url_for('login_page'))
    
    usuario_actual = session['usuario']
    user_data = db['usuarios'].get(usuario_actual)
    return render_template('index.html', usuario=usuario_actual, saldo=user_data['saldo'], partidos=db['partidos'])

@app.route('/logout')
def logout():
    session.clear() # Limpia la memoria del usuario
    return redirect(url_for('login_page'))

@app.route('/guardar_jugada', methods=['POST'])
def guardar_jugada():
    data = request.json
    usuario = session.get('usuario') # Usamos el usuario de la sesión por seguridad
    
    if not usuario or db['usuarios'][usuario]['saldo'] < 100:
        return jsonify({'mensaje': 'Saldo insuficiente o sesión expirada'}), 400
    
    id_ticket = os.urandom(3).hex().upper()
    fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    db['usuarios'][usuario]['saldo'] -= 100
    session['saldo'] = db['usuarios'][usuario]['saldo'] # Actualizamos sesión
    
    predicciones = data.get('predicciones')
    registro_admin = f"[{fecha_hora}] ID:{id_ticket} | USER:{usuario} | JUGADA:{predicciones}"
    
    with open("registro_admin_jugadas.txt", "a", encoding="utf-8") as f:
        f.write(registro_admin + "\n")
    
    return jsonify({
        'mensaje': 'OK',
        'id_ticket': id_ticket,
        'fecha': fecha_hora,
        'saldo_nuevo': db['usuarios'][usuario]['saldo']
    }), 200

@app.route('/guardar_imagen_carton', methods=['POST'])
def guardar_imagen_carton():
    data = request.json
    usuario = session.get('usuario')
    img_data = data.get('imageData')

    try:
        header, encoded = img_data.split(",", 1)
        decoded = base64.b64decode(encoded)
        filename = f"{usuario}_{os.urandom(3).hex()}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        with open(filepath, 'wb') as f:
            f.write(decoded)

        url_final = f"/static/comprobantes/{filename}"
        db['usuarios'][usuario]['imagenes_cartones'].append(url_final)
        return jsonify({'mensaje': 'Imagen guardada', 'imageUrl': url_final}), 200
    except Exception as e:
        return jsonify({'mensaje': str(e)}), 500

@app.route('/mis_comprobantes/<usuario>')
def mis_comprobantes(usuario):
    # Seguridad: Un usuario no puede ver comprobantes de otro
    if session.get('usuario') != usuario:
        return jsonify({'fotos': []}), 403
    fotos = db['usuarios'].get(usuario, {}).get('imagenes_cartones', [])
    return jsonify({'fotos': fotos})

if __name__ == '__main__':
    app.run(debug=True)
