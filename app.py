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

# --- NUEVA RUTA PARA YOUTUBE ---
@app.route('/youtube_premium')
def youtube_premium():
    if 'usuario' not in session: 
        return redirect(url_for('login_page'))
    # Renderiza el archivo youtube.html que está en la carpeta templates
    return render_template('youtube.html')

@app.route('/')
def login_page():
    if 'usuario' in session:
        user_doc = usuarios_col.find_one({'usuario': session['usuario']})
        if user_doc and user_doc.get('nivel') == 2: return redirect(url_for('admin_panel'))
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/verificar_login', methods=['POST'])
def verificar_login():
    user_input = (request.form.get('usuario') or "").upper().strip()
    pass_input = request.form.get('password')
    user_doc = usuarios_col.find_one({'usuario': user_input})
    
    if user_doc and str(user_doc['password']) == str(pass_input):
        session['usuario'] = user_input
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

# ... (El resto de tus rutas de admin_panel, gestion_usuario, logout, guardar_jugada se mantienen IGUAL)

@app.route('/guardar_imagen_carton', methods=['POST'])
def guardar_imagen_carton():
    # ... (tu código de guardar imagen se mantiene igual)
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
