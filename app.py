import os
import base64
import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_super_segura' 

# --- CONEXIÓN A MONGODB ATLAS ---
# Intenta leer la clave secreta desde Render, si no, usa el link directo
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://admin:K57362930k@cluster0.zbwrn8k.mongodb.net/?retryWrites=true&w=majority")
client = MongoClient(MONGO_URI)
db_mongo = client['prode_db']
usuarios_col = db_mongo['usuarios']
jugadas_col = db_mongo['jugadas'] # <--- NUEVO: Aquí guardaremos lo que antes iba al .txt

PARTIDOS = [
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

UPLOAD_FOLDER = os.path.join('static', 'comprobantes')
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/')
def login_page():
    if 'usuario' in session:
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route('/verificar_login', methods=['POST'])
def verificar_login():
    user_input = request.form.get('usuario').upper()
    pass_input = request.form.get('password').upper() # Normalizamos todo a MAYÚSCULAS
    
    user_doc = usuarios_col.find_one({'usuario': user_input})
    
    if user_doc and user_doc['password'] == pass_input:
        session['usuario'] = user_input
        return redirect(url_for('home'))
    else:
        return "Usuario o contraseña incorrectos", 401

@app.route('/index')
def home():
    if 'usuario' not in session:
        return redirect(url_for('login_page'))
    
    user_doc = usuarios_col.find_one({'usuario': session['usuario']})
    # Si por algún motivo no hay saldo en la DB, ponemos 0
    saldo_actual = user_doc.get('saldo', 0) if user_doc else 0
    
    return render_template('index.html', 
                           usuario=session['usuario'], 
                           saldo=saldo_actual, 
                           partidos=PARTIDOS)

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
    
    # 1. Descontar saldo
    usuarios_col.update_one({'usuario': usuario}, {'$inc': {'saldo': -100}})
    
    # 2. GUARDAR EN MONGODB (Lo que antes era el .txt)
    nueva_jugada = {
        'id_ticket': id_ticket,
        'usuario': usuario,
        'fecha': fecha_hora,
        'predicciones': data.get('predicciones')
    }
    jugadas_col.insert_one(nueva_jugada)
    
    return jsonify({
        'mensaje': 'OK',
        'id_ticket': id_ticket,
        'fecha': fecha_hora,
        'saldo_nuevo': user_doc['saldo'] - 100
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
        usuarios_col.update_one({'usuario': usuario}, {'$push': {'imagenes_cartones': url_final}})
        
        return jsonify({'mensaje': 'Imagen guardada', 'imageUrl': url_final}), 200
    except Exception as e:
        return jsonify({'mensaje': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
