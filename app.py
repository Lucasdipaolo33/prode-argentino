import os
import base64
import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura' 

# --- CONEXIÓN A MONGODB ---
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:K57362930k@cluster0.zbwrn8k.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db_mongo = client['prode_db']
usuarios_col = db_mongo['usuarios']
jugadas_col = db_mongo['jugadas']

PARTIDOS = [
    {'local': 'RIVER PLATE', 'visitante': 'BOCA JUNIORS'}, {'local': 'RACING', 'visitante': 'INDEPENDIENTE'},
    {'local': 'SAN LORENZO', 'visitante': 'HURACAN'}, {'local': 'ESTUDIANTES LP', 'visitante': 'GIMNASIA LP'},
    {'local': 'ROSARIO CENTRAL', 'visitante': 'NEWELLS'}, {'local': 'TALLERES', 'visitante': 'BELGRANO'},
    {'local': 'LANUS', 'visitante': 'BANFIELD'}, {'local': 'VELEZ', 'visitante': 'PLATENSE'},
    {'local': 'COLON', 'visitante': 'UNION'}, {'local': 'ATL. TUCUMAN', 'visitante': 'CENTRAL CORDOBA'},
    {'local': 'GODOY CRUZ', 'visitante': 'INDEP. RIVADAVIA'}, {'local': 'ARGENTINOS JRS', 'visitante': 'DEF. Y JUSTICIA'},
    {'local': 'TIGRE', 'visitante': 'BARRACAS CENTRAL'}, {'local': 'INSTITUTO', 'visitante': 'SARMIENTO'},
    {'local': 'RIESTRA', 'visitante': 'DEPORTIVO MAIPU'}
]

UPLOAD_FOLDER = os.path.join('static', 'comprobantes')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def login_page():
    if 'usuario' in session:
        user_doc = usuarios_col.find_one({'usuario': session['usuario']})
        if user_doc and user_doc.get('nivel') == 2: return redirect(url_for('admin_panel'))
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/verificar_login', methods=['POST'])
def verificar_login():
    user_input = request.form.get('usuario').upper()
    pass_input = request.form.get('password')
    user_doc = usuarios_col.find_one({'usuario': user_input})
    
    if user_doc and user_doc['password'] == pass_input:
        session['usuario'] = user_input
        # Redirección inteligente: ADMIN va a su panel, USER a jugar
        if user_doc.get('nivel') == 2:
            return redirect(url_for('admin_panel'))
        return redirect(url_for('home'))
    return "Usuario o contraseña incorrectos", 401

@app.route('/index')
def home():
    if 'usuario' not in session: return redirect(url_for('login_page'))
    user_doc = usuarios_col.find_one({'usuario': session['usuario']})
    saldo = user_doc.get('saldo', 0) if user_doc else 0
    return render_template('index.html', usuario=session['usuario'], saldo=saldo, partidos=PARTIDOS)

# --- PANEL DE ADMINISTRADOR ---
@app.route('/admin_panel')
def admin_panel():
    if 'usuario' not in session: return redirect(url_for('login_page'))
    user_doc = usuarios_col.find_one({'usuario': session['usuario']})
    
    if not user_doc or user_doc.get('nivel') != 2:
        return "Acceso denegado: No eres administrador", 403
        
    usuarios = list(usuarios_col.find())
    return render_template('admin.html', usuario=session['usuario'], usuarios=usuarios)

# --- GESTIÓN DE USUARIOS (RUTA PARA TU FORMULARIO HTML) ---
@app.route('/admin/gestion_usuario', methods=['POST'])
def gestion_usuario():
    if 'usuario' not in session: return redirect(url_for('login_page'))
    user_admin = usuarios_col.find_one({'usuario': session['usuario']})
    if not user_admin or user_admin.get('nivel') != 2:
        return "No autorizado", 403

    accion = request.form.get('accion')
    nombre = request.form.get('usuario_nombre').upper()

    if accion == 'crear':
        clave = request.form.get('usuario_clave')
        saldo_inicial = int(request.form.get('usuario_saldo', 0))
        if usuarios_col.find_one({'usuario': nombre}):
            flash(f"ERROR: El usuario {nombre} ya existe.")
        else:
            usuarios_col.insert_one({
                'usuario': nombre,
                'password': clave,
                'nivel': 0,
                'saldo': saldo_inicial,
                'imagenes_cartones': []
            })
            flash(f"ÉXITO: Usuario {nombre} creado correctamente.")

    elif accion == 'cargar_saldo':
        monto = int(request.form.get('monto', 0))
        resultado = usuarios_col.update_one({'usuario': nombre}, {'$inc': {'saldo': monto}})
        if resultado.modified_count > 0:
            flash(f"ÉXITO: Se cargaron ${monto} a {nombre}.")
        else:
            flash(f"ERROR: No se encontró al usuario {nombre}.")

    return redirect(url_for('admin_panel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login_page'))

@app.route('/guardar_jugada', methods=['POST'])
def guardar_jugada():
    data = request.json
    usuario = session.get('usuario')
    user_doc = usuarios_col.find_one({'usuario': usuario})
    
    if not user_doc or user_doc.get('saldo', 0) < 100:
        return jsonify({'mensaje': 'Saldo insuficiente'}), 400
    
    id_ticket = os.urandom(3).hex().upper()
    fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    usuarios_col.update_one({'usuario': usuario}, {'$inc': {'saldo': -100}})
    
    predicciones_str = " ".join([f"{k}:{v}" for k, v in data.get('predicciones', {}).items()])
    jugadas_col.insert_one({
        'fecha': fecha_hora,
        'id_ticket': id_ticket,
        'usuario': usuario,
        'jugada': predicciones_str
    })
    return jsonify({'mensaje': 'OK', 'id_ticket': id_ticket, 'fecha': fecha_hora, 'saldo_nuevo': user_doc['saldo'] - 100})

@app.route('/guardar_imagen_carton', methods=['POST'])
def guardar_imagen_carton():
    data = request.json
    usuario = session.get('usuario')
    try:
        header, encoded = data.get('imageData').split(",", 1)
        decoded = base64.b64decode(encoded)
        filename = f"{usuario}_{os.urandom(3).hex()}.png"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        with open(filepath, 'wb') as f: f.write(decoded)
        url_final = f"/static/comprobantes/{filename}"
        usuarios_col.update_one({'usuario': usuario}, {'$push': {'imagenes_cartones': url_final}})
        return jsonify({'mensaje': 'OK', 'imageUrl': url_final})
    except: return jsonify({'mensaje': 'Error al guardar foto'}), 500

if __name__ == '__main__':
    app.run(debug=True)
