from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Esta es la base de datos de los partidos de la Fecha 1
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
    # Renderizamos el HTML pasándole la lista de partidos
    return render_template('index.html', partidos=partidos)

@app.route('/guardar_jugada', methods=['POST'])
def guardar_jugada():
    # Esta ruta recibirá los datos cuando Lucas haga clic en "Enviar"
    try:
        datos = request.json
        print(f"Recibida jugada de: {datos.get('usuario')}")
        return jsonify({"status": "success", "mensaje": "Jugada recibida correctamente"}), 200
    except Exception as e:
        return jsonify({"status": "error", "mensaje": str(e)}), 400

if __name__ == '__main__':
    # Configuración estándar para desarrollo local
    app.run(debug=True)