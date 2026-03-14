from flask import Flask, request, jsonify
import psycopg2
import psycopg2.extras
import os
from datetime import datetime, date
from decimal import Decimal

app = Flask(__name__)

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "postgres"),
    "port": os.environ.get("DB_PORT", "5432"),
    "database": os.environ.get("DB_NAME", "medsource"),
    "user": os.environ.get("DB_USER", "medsource"),
    "password": os.environ.get("DB_PASS", "medsource123")
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def serialize(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    return obj

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "analytics"})

@app.route("/reports/rebate-summary", methods=["GET"])
def rebate_summary():
    quarter = request.args.get("quarter", "2024Q4")
    
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            c.customer_class,
            COUNT(DISTINCT rp.customer_id) as customer_count,
            SUM(rp.quarterly_units) as total_units,
            SUM(rp.calculated_rebate) as total_rebate,
            AVG(rp.calculated_rebate) as avg_rebate,
            SUM(rp.quarterly_target) as total_target
        FROM rebate_payments rp
        JOIN customers c ON rp.customer_id = c.customer_id
        WHERE rp.quarter = %s
        GROUP BY c.customer_class
        ORDER BY total_rebate DESC
    """, (quarter,))
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"quarter": quarter, "summary": results})

@app.route("/reports/variance-analysis", methods=["GET"])
def variance_analysis():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        WITH quarterly_totals AS (
            SELECT 
                quarter,
                SUM(calculated_rebate) as total_rebate,
                SUM(quarterly_units) as total_units,
                COUNT(DISTINCT customer_id) as customer_count
            FROM rebate_payments
            GROUP BY quarter
        )
        SELECT 
            qt.quarter,
            qt.total_rebate,
            qt.total_units,
            qt.customer_count,
            qt.total_rebate / NULLIF(qt.total_units, 0) as rebate_per_unit,
            LAG(qt.total_rebate) OVER (ORDER BY qt.quarter) as prev_rebate,
            (qt.total_rebate - LAG(qt.total_rebate) OVER (ORDER BY qt.quarter)) / 
                NULLIF(LAG(qt.total_rebate) OVER (ORDER BY qt.quarter), 0) * 100 as pct_change
        FROM quarterly_totals qt
        ORDER BY qt.quarter
    """)
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"variance_analysis": results})

@app.route("/reports/customer-detail/<int:customer_id>", methods=["GET"])
def customer_detail(customer_id):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT c.*, con.quarterly_target, con.contract_type
        FROM customers c
        LEFT JOIN contracts con ON c.customer_id = con.customer_id
        WHERE c.customer_id = %s
    """, (customer_id,))
    customer = cur.fetchone()
    
    cur.execute("""
        SELECT * FROM rebate_payments 
        WHERE customer_id = %s 
        ORDER BY quarter
    """, (customer_id,))
    payments = cur.fetchall()
    
    cur.execute("""
        SELECT * FROM calc_audit_log 
        WHERE customer_id = %s 
        ORDER BY calculation_date DESC 
        LIMIT 10
    """, (customer_id,))
    audit = cur.fetchall()
    
    cur.close()
    conn.close()
    
    return jsonify({
        "customer": {k: serialize(v) for k, v in customer.items()} if customer else None,
        "payments": [{k: serialize(v) for k, v in row.items()} for row in payments],
        "audit_log": [{k: serialize(v) for k, v in row.items()} for row in audit]
    })

@app.route("/reports/hospital-impact", methods=["GET"])
def hospital_impact():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            hc.hospital_system,
            hc.effective_date,
            c.name as pharmacy_name,
            rp.quarter,
            rp.quarterly_units,
            rp.quarterly_target,
            rp.calculated_rebate
        FROM hospital_contracts hc
        JOIN customers c ON hc.pharmacy_customer_id = c.customer_id
        LEFT JOIN rebate_payments rp ON c.customer_id = rp.customer_id
        ORDER BY hc.hospital_system, rp.quarter
    """)
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"hospital_contracts": results})

@app.route("/reports/seasonal-trends", methods=["GET"])
def seasonal_trends():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            sf.product_category,
            sf.month,
            sf.year,
            sf.demand_multiplier,
            COUNT(DISTINCT ol.order_id) as order_count,
            SUM(ol.quantity) as total_quantity
        FROM seasonal_factors sf
        LEFT JOIN products p ON p.category = sf.product_category
        LEFT JOIN order_lines ol ON ol.product_id = p.product_id
        LEFT JOIN orders o ON ol.order_id = o.order_id 
            AND EXTRACT(MONTH FROM o.order_date) = sf.month
            AND EXTRACT(YEAR FROM o.order_date) = sf.year
        GROUP BY sf.product_category, sf.month, sf.year, sf.demand_multiplier
        ORDER BY sf.year, sf.month, sf.product_category
    """)
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"seasonal_trends": results})

@app.route("/reports/specialty-analysis", methods=["GET"])
def specialty_analysis():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            c.name,
            c.specialty_certified,
            sc.certification_type,
            sc.granted_date,
            DATE '2025-01-15' - sc.granted_date as certification_days,
            rp.quarter,
            rp.quarterly_units,
            rp.specialty_ratio,
            rp.calculated_rebate
        FROM customers c
        LEFT JOIN specialty_certifications sc ON c.customer_id = sc.customer_id
        LEFT JOIN rebate_payments rp ON c.customer_id = rp.customer_id
        WHERE c.specialty_certified = TRUE OR sc.cert_id IS NOT NULL
        ORDER BY c.name, rp.quarter
    """)
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"specialty_analysis": results})

@app.route("/reports/price-list-impact", methods=["GET"])
def price_list_impact():
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cur.execute("""
        SELECT 
            pl.name as price_list,
            pl.effective_date,
            pl.adjustment_factor,
            COUNT(DISTINCT o.order_id) as orders_affected,
            SUM(o.total_amount) as total_revenue
        FROM price_lists pl
        LEFT JOIN orders o ON o.order_date >= pl.effective_date 
            AND (pl.expiry_date IS NULL OR o.order_date <= pl.expiry_date)
        GROUP BY pl.price_list_id, pl.name, pl.effective_date, pl.adjustment_factor
        ORDER BY pl.effective_date
    """)
    
    results = [{k: serialize(v) for k, v in row.items()} for row in cur.fetchall()]
    
    cur.close()
    conn.close()
    
    return jsonify({"price_list_impact": results})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
