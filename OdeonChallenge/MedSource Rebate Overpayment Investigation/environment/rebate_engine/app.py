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
    data = request.json
    payment_id = data.get("payment_id")
    customer_id = data.get("customer_id")
    quarterly_units = data.get("quarterly_units")
    quarterly_target = data.get("quarterly_target")
    specialty_ratio = data.get("specialty_ratio", 0.0)
    certification_days = data.get("certification_days", 0)
    specialty_certified = data.get("specialty_certified", False)
    contract_tier = data.get("contract_tier", 1)
    
    input_line = f"{payment_id} {customer_id} {quarterly_units} {quarterly_target} {specialty_ratio} {certification_days} {1 if specialty_certified else 0} {contract_tier}"
    
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
        
        output = result.stdout.strip().split()
        if len(output) >= 5:
            return jsonify({
                "payment_id": int(output[0]),
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
            rp.quarterly_target,
            COALESCE(rp.specialty_ratio, 0)::float,
            COALESCE(rp.certification_days, 0),
            c.specialty_certified,
            c.contract_tier
        FROM rebate_payments rp
        JOIN customers c ON rp.customer_id = c.customer_id
        WHERE rp.status = 'pending'
    """)
    
    payments = cur.fetchall()
    results = []
    
    for row in payments:
        payment_id, customer_id, q_units, q_target, spec_ratio, cert_days, spec_cert, tier = row
        
        input_line = f"{payment_id} {customer_id} {q_units} {q_target} {spec_ratio} {cert_days} {1 if spec_cert else 0} {tier}"
        
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
                        f'{{"units": {q_units}, "target": {q_target}, "spec_ratio": {spec_ratio}, "cert_days": {cert_days}}}'
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
