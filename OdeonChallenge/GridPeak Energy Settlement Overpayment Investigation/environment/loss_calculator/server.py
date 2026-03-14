import subprocess
import os
from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'user': os.environ.get('DB_USER', 'gridpeak'),
    'password': os.environ.get('DB_PASSWORD', 'settlement2024'),
    'dbname': os.environ.get('DB_NAME', 'energy_market')
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def run_fortran_calculator(zone, energy_mwh, threshold, loss_rate):
    input_data = f"{zone} {energy_mwh} {threshold} {loss_rate}\n"
    
    proc = subprocess.Popen(
        ['./loss_calc'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    stdout, stderr = proc.communicate(input=input_data, timeout=10)
    
    if proc.returncode != 0:
        raise Exception(f"Fortran calculator error: {stderr}")
    
    return float(stdout.strip())

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'loss_calculator'})

@app.route('/calculate', methods=['POST'])
def calculate_loss():
    data = request.json
    
    zone = data.get('zone')
    energy_mwh = float(data.get('energy_mwh', 0))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT energy_threshold, loss_rate 
        FROM loss_factors 
        WHERE zone = %s 
        AND effective_date <= CURRENT_DATE
        ORDER BY effective_date DESC
        LIMIT 1
    """, (zone,))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({'error': 'No loss factor found for zone'}), 404
    
    threshold, loss_rate = row
    
    loss_factor = run_fortran_calculator(zone, energy_mwh, float(threshold), float(loss_rate))
    
    return jsonify({
        'zone': zone,
        'energy_mwh': energy_mwh,
        'threshold': float(threshold),
        'loss_rate': float(loss_rate),
        'loss_factor': loss_factor
    })

@app.route('/batch_calculate', methods=['POST'])
def batch_calculate():
    data = request.json
    results = []
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    for item in data.get('items', []):
        zone = item.get('zone')
        energy_mwh = float(item.get('energy_mwh', 0))
        
        cur.execute("""
            SELECT energy_threshold, loss_rate 
            FROM loss_factors 
            WHERE zone = %s 
            AND effective_date <= CURRENT_DATE
            ORDER BY effective_date DESC
            LIMIT 1
        """, (zone,))
        
        row = cur.fetchone()
        
        if row:
            threshold, loss_rate = row
            loss_factor = run_fortran_calculator(zone, energy_mwh, float(threshold), float(loss_rate))
            results.append({
                'zone': zone,
                'energy_mwh': energy_mwh,
                'loss_factor': loss_factor
            })
    
    cur.close()
    conn.close()
    
    return jsonify({'results': results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081)
