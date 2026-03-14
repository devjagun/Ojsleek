from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime, timedelta

app = Flask(__name__)

DATABASE_URL = os.environ.get('DATABASE_URL', 'postgres://surehaul:surehaul123@postgres:5432/surehaul')

def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/reports/bonus-summary')
def bonus_summary():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            COUNT(*) as total_payments,
            SUM(bonus_amount) as total_paid,
            AVG(bonus_amount) as avg_bonus,
            MIN(bonus_amount) as min_bonus,
            MAX(bonus_amount) as max_bonus,
            AVG(base_performance_index) as avg_bpi,
            AVG(zone_difficulty_factor) as avg_zdf,
            AVG(tier_multiplier) as avg_multiplier
        FROM bonus_payments
        WHERE shift_date BETWEEN %s AND %s
    """, (start_date, end_date))
    
    row = cur.fetchone()
    
    result = {
        'period_start': start_date,
        'period_end': end_date,
        'total_payments': row[0],
        'total_paid': float(row[1]) if row[1] else 0,
        'avg_bonus': float(row[2]) if row[2] else 0,
        'min_bonus': float(row[3]) if row[3] else 0,
        'max_bonus': float(row[4]) if row[4] else 0,
        'avg_base_performance_index': float(row[5]) if row[5] else 0,
        'avg_zone_difficulty_factor': float(row[6]) if row[6] else 0,
        'avg_tier_multiplier': float(row[7]) if row[7] else 0
    }
    
    cur.close()
    conn.close()
    
    return jsonify(result)

@app.route('/reports/efficiency')
def efficiency_report():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    group_by = request.args.get('group_by', 'week')
    
    conn = get_db()
    cur = conn.cursor()
    
    if group_by == 'driver':
        cur.execute("""
            SELECT 
                d.driver_id,
                d.name,
                COUNT(s.shift_id) as shifts,
                SUM(s.deliveries_completed) as deliveries,
                SUM(s.route_target) as targets,
                CASE WHEN SUM(s.route_target) > 0 
                    THEN SUM(s.deliveries_completed)::float / SUM(s.route_target) 
                    ELSE 0 END as efficiency
            FROM shifts s
            JOIN drivers d ON s.driver_id = d.driver_id
            WHERE s.shift_date BETWEEN %s AND %s
            GROUP BY d.driver_id, d.name
            ORDER BY efficiency DESC
        """, (start_date, end_date))
    elif group_by == 'zone':
        cur.execute("""
            SELECT 
                z.zone_id,
                z.zone_name,
                COUNT(s.shift_id) as shifts,
                SUM(s.deliveries_completed) as deliveries,
                SUM(s.route_target) as targets,
                CASE WHEN SUM(s.route_target) > 0 
                    THEN SUM(s.deliveries_completed)::float / SUM(s.route_target) 
                    ELSE 0 END as efficiency
            FROM shifts s
            JOIN zones z ON s.zone_id = z.zone_id
            WHERE s.shift_date BETWEEN %s AND %s
            GROUP BY z.zone_id, z.zone_name
            ORDER BY efficiency DESC
        """, (start_date, end_date))
    else:
        cur.execute("""
            SELECT 
                DATE_TRUNC('week', s.shift_date) as week_start,
                COUNT(s.shift_id) as shifts,
                SUM(s.deliveries_completed) as deliveries,
                SUM(s.route_target) as targets,
                CASE WHEN SUM(s.route_target) > 0 
                    THEN SUM(s.deliveries_completed)::float / SUM(s.route_target) 
                    ELSE 0 END as efficiency
            FROM shifts s
            WHERE s.shift_date BETWEEN %s AND %s
            GROUP BY DATE_TRUNC('week', s.shift_date)
            ORDER BY week_start
        """, (start_date, end_date))
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if group_by == 'driver':
        results = [{'driver_id': r[0], 'name': r[1], 'shifts': r[2], 
                   'deliveries': r[3], 'targets': r[4], 'efficiency': float(r[5])} for r in rows]
    elif group_by == 'zone':
        results = [{'zone_id': r[0], 'zone_name': r[1], 'shifts': r[2],
                   'deliveries': r[3], 'targets': r[4], 'efficiency': float(r[5])} for r in rows]
    else:
        results = [{'week_start': str(r[0].date()), 'shifts': r[1],
                   'deliveries': r[2], 'targets': r[3], 'efficiency': float(r[4])} for r in rows]
    
    return jsonify({'group_by': group_by, 'data': results})

@app.route('/reports/fuel-impact')
def fuel_impact():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    conn = get_db()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            DATE_TRUNC('week', f.date) as week_start,
            AVG(f.price_per_gallon) as avg_fuel_price,
            AVG(f.weekly_average) as weekly_avg
        FROM fuel_costs f
        WHERE f.date BETWEEN %s AND %s
        GROUP BY DATE_TRUNC('week', f.date)
        ORDER BY week_start
    """, (start_date, end_date))
    
    fuel_rows = cur.fetchall()
    
    cur.execute("""
        SELECT 
            DATE_TRUNC('week', bp.shift_date) as week_start,
            SUM(bp.bonus_amount) as total_bonus,
            AVG(bp.bonus_amount) as avg_bonus,
            COUNT(*) as payment_count
        FROM bonus_payments bp
        WHERE bp.shift_date BETWEEN %s AND %s
        GROUP BY DATE_TRUNC('week', bp.shift_date)
        ORDER BY week_start
    """, (start_date, end_date))
    
    bonus_rows = cur.fetchall()
    
    cur.close()
    conn.close()
    
    fuel_data = {str(r[0].date()): {'avg_price': float(r[1]), 'weekly_avg': float(r[2])} for r in fuel_rows}
    
    results = []
    for r in bonus_rows:
        week = str(r[0].date())
        results.append({
            'week_start': week,
            'total_bonus': float(r[1]),
            'avg_bonus': float(r[2]),
            'payment_count': r[3],
            'fuel_price': fuel_data.get(week, {}).get('avg_price', 0),
            'fuel_weekly_avg': fuel_data.get(week, {}).get('weekly_avg', 0)
        })
    
    return jsonify({'data': results})

@app.route('/metrics/comparison')
def metrics_comparison():
    p1_start = request.args.get('period1_start')
    p1_end = request.args.get('period1_end')
    p2_start = request.args.get('period2_start')
    p2_end = request.args.get('period2_end')
    
    conn = get_db()
    cur = conn.cursor()
    
    def get_period_metrics(start, end):
        cur.execute("""
            SELECT 
                COUNT(*) as payments,
                SUM(bonus_amount) as total,
                AVG(bonus_amount) as avg_bonus,
                AVG(base_performance_index) as avg_bpi,
                AVG(zone_difficulty_factor) as avg_zdf,
                AVG(tier_multiplier) as avg_mult
            FROM bonus_payments
            WHERE shift_date BETWEEN %s AND %s
        """, (start, end))
        row = cur.fetchone()
        return {
            'payments': row[0],
            'total_bonus': float(row[1]) if row[1] else 0,
            'avg_bonus': float(row[2]) if row[2] else 0,
            'avg_bpi': float(row[3]) if row[3] else 0,
            'avg_zdf': float(row[4]) if row[4] else 0,
            'avg_multiplier': float(row[5]) if row[5] else 0
        }
    
    period1 = get_period_metrics(p1_start, p1_end)
    period2 = get_period_metrics(p2_start, p2_end)
    
    cur.close()
    conn.close()
    
    def pct_change(old, new):
        if old == 0:
            return 0
        return ((new - old) / old) * 100
    
    return jsonify({
        'period1': {'start': p1_start, 'end': p1_end, 'metrics': period1},
        'period2': {'start': p2_start, 'end': p2_end, 'metrics': period2},
        'changes': {
            'total_bonus_pct': pct_change(period1['total_bonus'], period2['total_bonus']),
            'avg_bonus_pct': pct_change(period1['avg_bonus'], period2['avg_bonus']),
            'avg_bpi_pct': pct_change(period1['avg_bpi'], period2['avg_bpi']),
            'avg_zdf_pct': pct_change(period1['avg_zdf'], period2['avg_zdf']),
            'avg_multiplier_pct': pct_change(period1['avg_multiplier'], period2['avg_multiplier'])
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
