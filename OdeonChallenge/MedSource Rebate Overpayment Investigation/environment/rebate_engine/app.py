from flask import Flask, request, jsonify
import subprocess
import psycopg2
import os

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

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "service": "rebate-engine"})

@app.route("/calculate", methods=["POST"])
def calculate_rebate():
    """Calculate rebate for a single customer.
    
    Required fields: customer_id, total_units, base_revenue, certification_days, specialty_certified, customer_class
    Ada binary expects: Customer_ID Total_Units Base_Revenue Certification_Days Is_Specialty_Cert Customer_Class
    Ada returns: Customer_ID Vol_Index Mix_Factor Class_Rate Total_Rebate
    """
    data = request.json
    customer_id = data.get("customer_id")
    total_units = data.get("total_units")
    base_revenue = data.get("base_revenue")
    certification_days = data.get("certification_days", 0)
    specialty_certified = data.get("specialty_certified", False)
    customer_class = data.get("customer_class", 1)
    
    # Ada expects 6 fields: Customer_ID Total_Units Base_Revenue Certification_Days Is_Specialty_Cert Customer_Class
    input_line = f"{customer_id} {total_units} {base_revenue} {certification_days} {1 if specialty_certified else 0} {customer_class}"
    
    try:
        result = subprocess.run(
            ["/app/rebate_calc"],
            input=input_line,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return jsonify({"error": "Calculation failed", "stderr": result.stderr}), 500
        
        # Ada returns: Customer_ID Vol_Index Mix_Factor Class_Rate Total_Rebate
        output = result.stdout.strip().split()
        if len(output) >= 5:
            return jsonify({
                "customer_id": int(output[0]),
                "volume_index": float(output[1]),
                "product_mix_factor": float(output[2]),
                "customer_class_rate": float(output[3]),
                "calculated_rebate": float(output[4])
            })
        else:
            return jsonify({"error": "Unexpected output format"}), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Calculation timeout"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/batch-calculate", methods=["POST"])
def batch_calculate():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT 
            rp.payment_id,
            rp.customer_id,
            rp.quarterly_units,
            COALESCE((SELECT SUM(o.total_amount) FROM orders o 
                      WHERE o.customer_id = rp.customer_id AND o.quarter = rp.quarter), 0)::float as base_revenue,
            COALESCE(rp.certification_days, 0),
            CASE WHEN c.specialty_certified THEN 1 ELSE 0 END as is_specialty_cert,
            c.contract_tier
        FROM rebate_payments rp
        JOIN customers c ON rp.customer_id = c.customer_id
        WHERE rp.status = 'pending'
    """)
    
    payments = cur.fetchall()
    results = []
    
    for row in payments:
        payment_id, customer_id, q_units, base_revenue, cert_days, is_spec_cert, tier = row
        
        input_line = f"{customer_id} {q_units} {base_revenue} {cert_days} {is_spec_cert} {tier}"
        
        try:
            result = subprocess.run(
                ["/app/rebate_calc"],
                input=input_line,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                output = result.stdout.strip().split()
                if len(output) >= 5:
                    calculated_rebate = float(output[4])
                    
                    cur.execute("""
                        UPDATE rebate_payments 
                        SET calculated_rebate = %s
                        WHERE payment_id = %s
                    """, (calculated_rebate, payment_id))
                    
                    cur.execute("""
                        INSERT INTO calc_audit_log 
                        (payment_id, customer_id, volume_index, product_mix_factor, customer_class_rate, final_rebate, input_data)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        payment_id, customer_id,
                        float(output[1]), float(output[2]), float(output[3]), calculated_rebate,
                        f'{{"units": {q_units}, "base_revenue": {base_revenue}, "cert_days": {cert_days}}}'
                    ))
                    
                    results.append({
                        "payment_id": payment_id,
                        "calculated_rebate": calculated_rebate,
                        "status": "success"
                    })
        except Exception as e:
            results.append({
                "payment_id": payment_id,
                "error": str(e),
                "status": "failed"
            })
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        "processed": len(results),
        "results": results[:10]
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
