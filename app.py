import os
import sqlite3
from flask import Flask, jsonify

app = Flask(__name__)

# O StatefulSet montará o volume em /data
# Usamos /data/app.db como nosso banco de dados
DB_PATH = '/data/app.db'

def get_db():
    """Inicializa o banco de dados se não existir."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute('''
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    return conn

@app.route('/')
def index():
    """
    Registra uma nova visita e lista todas as visitas.
    Isso demonstra a persistência (StatefulSet + PVC).
    """
    conn = get_db()
    
    # Insere a nova visita
    conn.execute('INSERT INTO visits (timestamp) VALUES (CURRENT_TIMESTAMP)')
    conn.commit()
    
    # Busca todas as visitas
    cursor = conn.execute('SELECT id, timestamp FROM visits ORDER BY id DESC')
    visits = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Retorna a lista de visitas e o nome do pod
    pod_name = os.environ.get('HOSTNAME', 'unknown-pod')
    
    return jsonify({
        "message": f"Olá! Esta visita foi registrada pelo pod: {pod_name}",
        "total_visits": len(visits),
        "visits": visits
    })

@app.route('/heavy')
def heavy_load():
    """
    Endpoint para simular alta carga de CPU.
    Isso acionará o HorizontalPodAutoscaler (HPA).
    """
    # Executa um cálculo pesado e inútil para queimar CPU
    for i in range(20000000):
        _ = i * i
        
    pod_name = os.environ.get('HOSTNAME', 'unknown-pod')
    return jsonify(message=f"Carga de CPU gerada no pod: {pod_name}")

if __name__ == '__main__':
    # Inicializa o banco de dados na inicialização
    with app.app_context():
        get_db().close()
    
    app.run(host='0.0.0.0', port=5000)
