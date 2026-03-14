import os
import requests
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import psycopg2
from decimal import Decimal, ROUND_HALF_UP

app = Flask(__name__)

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'user': os.environ.get('DB_USER', 'gridpeak'),
    'password': os.environ.get('DB_PASSWORD', 'settlement2024'),
    'dbname': os.environ.get('DB_NAME', 'energy_market')
}

LOSS_CALC_URL = os.environ.get('LOSS_CALC_URL', 'http://localhost:8081')

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def get_loss_factor(zone, energy_mwh):
    resp = requests.post(
        f"{LOSS_CALC_URL}/calculate",
        json={'zone': zone, 'energy_mwh': energy_mwh},
        timeout=30
    )
    if resp.status_code == 200:
        return resp.json()['loss_factor']
    return 1.0

def determine_rate_tier(generator_type, capacity_factor, location_type):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT tier_id, rate_per_mwh, priority_order
        FROM rate_tiers
        WHERE generator_type = %s
        ORDER BY priority_order ASC
    """, (generator_type,))
    
    tiers = cur.fetchall()
    cur.close()
    conn.close()
    
    for tier_id, rate, priority in tiers:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT min_capacity_factor, location_type
            FROM rate_tiers
            WHERE tier_id = %s
        """, (tier_id,))
        tier_info = cur.fetchone()
        cur.close()
        conn.close()
        
        min_cf, loc_type = tier_info
        
        if loc_type is not None and loc_type == location_type:
            return float(rate)
        elif loc_type is None:
            if min_cf is None or capacity_factor >= float(min_cf):
                return float(rate)
    
    return 45.00

def aggregate_meter_readings(generator_id, period_start, period_end):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT timestamp, energy_mw, interval_minutes
        FROM meter_readings
        WHERE generator_id = %s
        AND timestamp >= %s
        AND timestamp < %s
        ORDER BY timestamp
    """, (generator_id, period_start, period_end))
    
    readings = cur.fetchall()
    cur.close()
    conn.close()
    
    total_mwh = Decimal('0')
    
    for ts, energy_mw, interval_min in readings:
        mwh = Decimal(str(energy_mw)) * Decimal(str(interval_min)) / Decimal('60')
        mwh = mwh.quantize(Decimal('0.0001'), rounding=ROUND_HALF_UP)
        total_mwh += mwh
    
    return float(total_mwh.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))

def calculate_settlement(generator_id, period_start, period_end):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT g.id, g.name, g.generator_type, g.capacity_mw, g.location_id, n.zone, n.location_type
        FROM generators g
        JOIN nodes n ON g.location_id = n.id
        WHERE g.id = %s
    """, (generator_id,))
    
    gen_info = cur.fetchone()
    
    if not gen_info:
        cur.close()
        conn.close()
        return None
    
    gen_id, name, gen_type, capacity, loc_id, zone, loc_type = gen_info
    
    cur.execute("""
        SELECT SUM(energy_mw * interval_minutes / 60.0) as total_mwh,
               COUNT(*) as reading_count,
               MAX(energy_mw) as peak_mw
        FROM meter_readings
        WHERE generator_id = %s
        AND timestamp >= %s
        AND timestamp < %s
    """, (generator_id, period_start, period_end))
    
    agg = cur.fetchone()
    total_mwh, reading_count, peak_mw = agg
    
    if total_mwh is None:
        total_mwh = 0
    
    cur.close()
    conn.close()
    
    total_mwh = float(total_mwh)
    
    hours_in_period = (period_end - period_start).total_seconds() / 3600
    capacity_factor = (total_mwh / (float(capacity) * hours_in_period)) if capacity > 0 else 0
    
    rate = determine_rate_tier(gen_type, capacity_factor, loc_type)
    
    gross_payment = round(total_mwh * rate, 2)
    
    loss_factor = get_loss_factor(zone, total_mwh)
    loss_deduction = round(total_mwh * (loss_factor - 1.0) * rate, 2)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT congestion_factor FROM nodes WHERE id = %s
    """, (loc_id,))
    cong_factor = cur.fetchone()[0]
    
    congestion_credit = round(total_mwh * float(cong_factor) * 0.05 * rate, 2)
    
    net_payment = round(gross_payment - loss_deduction + congestion_credit, 2)
    
    cur.execute("""
        INSERT INTO settlements 
        (generator_id, period_start, period_end, energy_mwh, gross_payment, 
         loss_deduction, congestion_credit, net_payment, rate_applied, 
         loss_factor_applied, capacity_factor)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING settlement_id
    """, (generator_id, period_start, period_end, total_mwh, gross_payment,
          loss_deduction, congestion_credit, net_payment, rate, loss_factor, capacity_factor))
    
    settlement_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()
    
    return {
        'settlement_id': settlement_id,
        'generator_id': generator_id,
        'generator_name': name,
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'energy_mwh': total_mwh,
        'gross_payment': gross_payment,
        'loss_deduction': loss_deduction,
        'congestion_credit': congestion_credit,
        'net_payment': net_payment,
        'rate_applied': rate,
        'loss_factor': loss_factor,
        'capacity_factor': round(capacity_factor, 4)
    }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'settlement_engine'})

@app.route('/calculate', methods=['POST'])
def calculate():
    data = request.json
    generator_id = data.get('generator_id')
    period_start = datetime.fromisoformat(data.get('period_start'))
    period_end = datetime.fromisoformat(data.get('period_end'))
    
    result = calculate_settlement(generator_id, period_start, period_end)
    
    if result:
        return jsonify(result)
    return jsonify({'error': 'Generator not found'}), 404

@app.route('/batch_calculate', methods=['POST'])
def batch_calculate():
    data = request.json
    period_start = datetime.fromisoformat(data.get('period_start'))
    period_end = datetime.fromisoformat(data.get('period_end'))
    generator_ids = data.get('generator_ids', [])
    
    results = []
    for gen_id in generator_ids:
        result = calculate_settlement(gen_id, period_start, period_end)
        if result:
            results.append(result)
    
    return jsonify({'settlements': results})

@app.route('/recalculate_all', methods=['POST'])
def recalculate_all():
    data = request.json
    period_start = datetime.fromisoformat(data.get('period_start'))
    period_end = datetime.fromisoformat(data.get('period_end'))
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM settlements WHERE period_start = %s AND period_end = %s",
                (period_start, period_end))
    conn.commit()
    
    cur.execute("SELECT id FROM generators WHERE is_active = true")
    generators = cur.fetchall()
    cur.close()
    conn.close()
    
    results = []
    for (gen_id,) in generators:
        result = calculate_settlement(gen_id, period_start, period_end)
        if result:
            results.append(result)
    
    return jsonify({'settlements': results, 'count': len(results)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8082)
