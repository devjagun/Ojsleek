from flask import Flask, request, jsonify
import subprocess
import os
import psycopg2

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://surehaul:surehaul123@postgres:5432/surehaul')

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def run_bonus_calc(driver_id, deliveries, target, base_difficulty, avg_rating, zone_days, tier, tenure_years):
    input_line = f"{driver_id} {deliveries} {target} {base_difficulty} {avg_rating} {zone_days} {tier} {tenure_years}"
    result = subprocess.run(
        ['/app/bonus_calc'],
        input=input_line,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split()
    return {
        'driver_id': int(parts[0]),
        'base_performance_index': float(parts[1]),
        'zone_difficulty_factor': float(parts[2]),
        'score': float(parts[3]),
        'tier_multiplier': float(parts[4]),
        'final_bonus': float(parts[5])
    }

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/calculate/<int:driver_id>')
def calculate(driver_id):
    period_start = request.args.get('period_start')
    period_end = request.args.get('period_end')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT d.tier, 
               EXTRACT(YEAR FROM AGE(CURRENT_DATE, d.hire_date))::int as tenure_years
        FROM drivers d WHERE d.driver_id = %s
    """, (driver_id,))
    driver_row = cur.fetchone()
    if not driver_row:
        cur.close()
        conn.close()
        return jsonify({'error': 'Driver not found'}), 404
    
    tier, tenure_years = driver_row
    
    cur.execute("""
        SELECT s.shift_id, s.shift_date, s.zone_id, s.deliveries_completed, s.route_target,
               z.base_difficulty, dzh.total_days_in_zone,
               COALESCE((SELECT AVG(f.rating) FROM feedback f 
                         WHERE f.driver_id = s.driver_id AND f.zone_id = s.zone_id), 3.5) as avg_rating
        FROM shifts s
        JOIN zones z ON s.zone_id = z.zone_id
        LEFT JOIN driver_zone_history dzh ON dzh.driver_id = s.driver_id AND dzh.zone_id = s.zone_id
        WHERE s.driver_id = %s AND s.shift_date BETWEEN %s AND %s
        ORDER BY s.shift_date
    """, (driver_id, period_start, period_end))
    
    shifts = cur.fetchall()
    results = []
    
    for shift in shifts:
        shift_id, shift_date, zone_id, deliveries, target, base_diff, zone_days, avg_rating = shift
        zone_days = zone_days or 0
        
        calc_result = run_bonus_calc(
            driver_id, deliveries, target, base_diff, avg_rating, zone_days, tier, tenure_years
        )
        
        if calc_result:
            results.append({
                'shift_id': shift_id,
                'shift_date': str(shift_date),
                'zone_id': zone_id,
                **calc_result
            })
    
    cur.close()
    conn.close()
    
    return jsonify({
        'driver_id': driver_id,
        'period_start': period_start,
        'period_end': period_end,
        'calculations': results,
        'total_bonus': sum(r['final_bonus'] for r in results)
    })

@app.route('/scores/<int:driver_id>/breakdown')
def breakdown(driver_id):
    shift_date = request.args.get('shift_date')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT bp.* FROM bonus_payments bp
        WHERE bp.driver_id = %s AND bp.shift_date = %s
    """, (driver_id, shift_date))
    
    row = cur.fetchone()
    cur.close()
    conn.close()
    
    if not row:
        return jsonify({'error': 'No bonus record found'}), 404
    
    return jsonify({
        'payment_id': row[0],
        'driver_id': row[1],
        'shift_date': str(row[2]),
        'base_performance_index': float(row[3]),
        'zone_difficulty_factor': float(row[4]),
        'tier_multiplier': float(row[5]),
        'final_score': float(row[6]),
        'bonus_amount': float(row[7])
    })

@app.route('/batch-calculate', methods=['POST'])
def batch_calculate():
    data = request.get_json()
    start_date = data.get('start_date')
    end_date = data.get('end_date')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT driver_id FROM drivers WHERE status = 'active'")
    drivers = cur.fetchall()
    
    processed = 0
    for (driver_id,) in drivers:
        cur.execute("""
            SELECT d.tier,
                   EXTRACT(YEAR FROM AGE(CURRENT_DATE, d.hire_date))::int as tenure_years
            FROM drivers d WHERE d.driver_id = %s
        """, (driver_id,))
        driver_row = cur.fetchone()
        tier, tenure_years = driver_row
        
        cur.execute("""
            SELECT s.shift_id, s.shift_date, s.zone_id, s.deliveries_completed, s.route_target,
                   z.base_difficulty, dzh.total_days_in_zone,
                   COALESCE((SELECT AVG(f.rating) FROM feedback f 
                             WHERE f.driver_id = s.driver_id AND f.zone_id = s.zone_id), 3.5) as avg_rating
            FROM shifts s
            JOIN zones z ON s.zone_id = z.zone_id
            LEFT JOIN driver_zone_history dzh ON dzh.driver_id = s.driver_id AND dzh.zone_id = s.zone_id
            WHERE s.driver_id = %s AND s.shift_date BETWEEN %s AND %s
        """, (driver_id, start_date, end_date))
        
        shifts = cur.fetchall()
        
        for shift in shifts:
            shift_id, shift_date, zone_id, deliveries, target, base_diff, zone_days, avg_rating = shift
            zone_days = zone_days or 0
            
            calc_result = run_bonus_calc(
                driver_id, deliveries, target, base_diff, avg_rating, zone_days, tier, tenure_years
            )
            
            if calc_result:
                cur.execute("""
                    INSERT INTO bonus_payments 
                    (driver_id, shift_date, base_performance_index, zone_difficulty_factor, 
                     tier_multiplier, final_score, bonus_amount, calculated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (driver_id, shift_date) DO UPDATE SET
                    base_performance_index = EXCLUDED.base_performance_index,
                    zone_difficulty_factor = EXCLUDED.zone_difficulty_factor,
                    tier_multiplier = EXCLUDED.tier_multiplier,
                    final_score = EXCLUDED.final_score,
                    bonus_amount = EXCLUDED.bonus_amount,
                    calculated_at = NOW()
                """, (
                    driver_id, shift_date, 
                    calc_result['base_performance_index'],
                    calc_result['zone_difficulty_factor'],
                    calc_result['tier_multiplier'],
                    calc_result['score'],
                    calc_result['final_bonus']
                ))
                processed += 1
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({'status': 'completed', 'records_processed': processed})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
