import os
import base64
import datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# BASE DE DATOS - 15 PARTIDOS
db = {
    'usuarios': {
        'laura': {'saldo': 500, 'jugadas': [], 'imagenes_cartones': []},
        'juan': {'saldo': 1200, 'jugadas': [], 'imagenes_cartones': []}
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

@app.route('/')
def home():
    usuario_actual = 'laura'
    user_data = db['usuarios'].get(usuario_actual)
    return render_template('index.html', usuario=usuario_actual, saldo=user_data['saldo'], partidos=db['partidos'])

@app.route('/guardar_jugada', methods=['POST'])
def guardar_jugada():
    data = request.json
    usuario = data.get('usuario')
    predicciones = data.get('predicciones') # Recibe el texto resumen de la jugada
    
    if db['usuarios'][usuario]['saldo'] < 100:
        return jsonify({'mensaje': 'Saldo insuficiente'}), 400
    
    # Generar ID único y Fecha
    id_ticket = os.urandom(3).hex().upper()
    fecha_hora = datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    # 1. Descontar saldo
    db['usuarios'][usuario]['saldo'] -= 100
    
    # 2. Registro Prolijo para el ADMIN (en consola y archivo)
    registro_admin = f"[{fecha_hora}] ID:{id_ticket} | USER:{usuario} | JUGADA:{predicciones}"
    
    with open("registro_admin_jugadas.txt", "a", encoding="utf-8") as f:
        f.write(registro_admin + "\n")
    
    print(f"✔️ REGISTRO GUARDADO: {registro_admin}")

    return jsonify({
        'mensaje': 'OK',
        'id_ticket': id_ticket,
        'fecha': fecha_hora,
        'saldo_nuevo': db['usuarios'][usuario]['saldo']
    }), 200

@app.route('/guardar_imagen_carton', methods=['POST'])
def guardar_imagen_carton():
    data = request.json
    usuario = data.get('usuario')
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
    fotos = db['usuarios'].get(usuario, {}).get('imagenes_cartones', [])
    return jsonify({'fotos': fotos})

if __name__ == '__main__':
    app.run(debug=True)
