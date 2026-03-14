import random
import datetime
from decimal import Decimal, ROUND_HALF_UP
import os

random.seed(42)

BASE_DATE = datetime.date(2025, 1, 15)

CUSTOMER_NAMES = [
    "Westside Pharmacy", "Central Drug Mart", "HealthFirst Rx", "Community Care Pharmacy",
    "Sunrise Medical Supply", "Metro Health Pharmacy", "Valley Drug Store", "Capitol Pharmacy",
    "Lakeside Rx Center", "Northgate Pharmacy", "Eastside Drug", "Downtown Health Mart",
    "Suburban Pharmacy Plus", "University Pharmacy", "Regional Medical Supply", "Harbor Drug",
    "Greenfield Pharmacy", "Ridgeview Rx", "Parkside Drug Store", "Hilltop Pharmacy",
    "Oakwood Medical Supply", "Riverside Pharmacy", "Meadowbrook Drug", "Cornerstone Rx",
    "Heritage Pharmacy", "Pinecrest Drug Store", "Summit Health Pharmacy", "Bayview Rx",
    "Creekside Pharmacy", "Hillcrest Drug Mart", "Fairview Medical Supply", "Brookside Pharmacy",
    "Midwest Health Pharmacy A", "Midwest Health Pharmacy B", "Midwest Health Pharmacy C",
    "Midwest Health Pharmacy D", "Midwest Health Pharmacy E", "Premier Specialty Rx",
    "Advanced Specialty Pharmacy", "Elite Specialty Care", "Precision Rx Specialty",
    "Specialty Infusion Center", "Oncology Pharmacy Partners", "Rare Disease Rx",
    "BioSpecialty Pharmacy", "Immunology Rx Center"
]

PRODUCT_NAMES = [
    ("Amoxicillin 500mg", "generic", 12.50),
    ("Lisinopril 10mg", "generic", 8.75),
    ("Metformin 850mg", "generic", 9.20),
    ("Atorvastatin 20mg", "generic", 15.30),
    ("Omeprazole 20mg", "generic", 11.40),
    ("Amlodipine 5mg", "generic", 7.80),
    ("Metoprolol 50mg", "generic", 10.25),
    ("Sertraline 100mg", "generic", 14.60),
    ("Gabapentin 300mg", "generic", 13.90),
    ("Hydrochlorothiazide 25mg", "generic", 6.50),
    ("Losartan 50mg", "generic", 11.75),
    ("Levothyroxine 100mcg", "generic", 8.90),
    ("Prednisone 10mg", "generic", 5.40),
    ("Fluticasone Nasal Spray", "brand", 45.80),
    ("Advair Diskus 250/50", "brand", 285.00),
    ("Eliquis 5mg", "brand", 425.50),
    ("Xarelto 20mg", "brand", 398.75),
    ("Januvia 100mg", "brand", 365.20),
    ("Humira Pen 40mg", "specialty", 5850.00),
    ("Enbrel 50mg", "specialty", 4925.00),
    ("Keytruda 100mg", "specialty", 8750.00),
    ("Revlimid 25mg", "specialty", 12500.00),
    ("Ocrevus 300mg", "specialty", 15200.00),
    ("Stelara 90mg", "specialty", 11800.00),
    ("Tamiflu 75mg", "brand", 125.40),
    ("Flucelvax Quad", "brand", 68.50),
    ("Fluzone HD", "brand", 72.30),
]

def generate_sql():
    lines = []
    
    lines.append("""
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    customer_class VARCHAR(20) NOT NULL,
    contract_tier INTEGER DEFAULT 1,
    specialty_certified BOOLEAN DEFAULT FALSE,
    certification_date DATE,
    region VARCHAR(20) NOT NULL,
    onboarded_date DATE NOT NULL
);

CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(20) NOT NULL,
    base_price DECIMAL(10,2) NOT NULL,
    rebate_eligible BOOLEAN DEFAULT TRUE
);

CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    order_date DATE NOT NULL,
    total_units INTEGER NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    quarter VARCHAR(6) NOT NULL
);

CREATE TABLE order_lines (
    line_id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(order_id),
    product_id INTEGER REFERENCES products(product_id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2) NOT NULL,
    line_total DECIMAL(12,2) NOT NULL
);

CREATE TABLE rebate_tiers (
    tier_id SERIAL PRIMARY KEY,
    tier_name VARCHAR(50) NOT NULL,
    min_volume INTEGER NOT NULL,
    max_volume INTEGER,
    base_rate DECIMAL(5,4) NOT NULL,
    effective_date DATE NOT NULL
);

CREATE TABLE rebate_payments (
    payment_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    quarter VARCHAR(6) NOT NULL,
    quarterly_units INTEGER NOT NULL,
    quarterly_target INTEGER NOT NULL,
    specialty_ratio DECIMAL(5,4),
    certification_days INTEGER,
    calculated_rebate DECIMAL(12,2) NOT NULL,
    payment_date DATE,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE contracts (
    contract_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    contract_type VARCHAR(30) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    quarterly_target INTEGER NOT NULL,
    notes TEXT
);

CREATE TABLE price_lists (
    price_list_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    effective_date DATE NOT NULL,
    expiry_date DATE,
    adjustment_factor DECIMAL(5,4) DEFAULT 1.0000
);

CREATE TABLE price_list_items (
    item_id SERIAL PRIMARY KEY,
    price_list_id INTEGER REFERENCES price_lists(price_list_id),
    product_id INTEGER REFERENCES products(product_id),
    list_price DECIMAL(10,2) NOT NULL
);

CREATE TABLE seasonal_factors (
    factor_id SERIAL PRIMARY KEY,
    product_category VARCHAR(20) NOT NULL,
    month INTEGER NOT NULL,
    demand_multiplier DECIMAL(5,3) NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE specialty_certifications (
    cert_id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(customer_id),
    certification_type VARCHAR(50) NOT NULL,
    granted_date DATE NOT NULL,
    expiry_date DATE,
    status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE hospital_contracts (
    hc_id SERIAL PRIMARY KEY,
    hospital_system VARCHAR(100) NOT NULL,
    pharmacy_customer_id INTEGER REFERENCES customers(customer_id),
    effective_date DATE NOT NULL,
    volume_commitment INTEGER,
    notes TEXT
);

CREATE TABLE calc_audit_log (
    audit_id SERIAL PRIMARY KEY,
    payment_id INTEGER REFERENCES rebate_payments(payment_id),
    customer_id INTEGER REFERENCES customers(customer_id),
    calculation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    volume_index DECIMAL(12,4),
    product_mix_factor DECIMAL(8,5),
    customer_class_rate DECIMAL(6,4),
    final_rebate DECIMAL(12,2),
    input_data JSONB
);

""")
    
    lines.append("INSERT INTO products (name, category, base_price) VALUES")
    product_values = []
    for name, cat, price in PRODUCT_NAMES:
        product_values.append(f"('{name}', '{cat}', {price})")
    lines.append(",\n".join(product_values) + ";\n")
    
    lines.append("INSERT INTO customers (name, customer_class, contract_tier, specialty_certified, certification_date, region, onboarded_date) VALUES")
    customer_values = []
    regions = ["Northeast", "Southeast", "Midwest", "Southwest", "West"]
    
    for i, name in enumerate(CUSTOMER_NAMES):
        if "Specialty" in name or "Oncology" in name or "Infusion" in name or "Rare Disease" in name or "Bio" in name or "Immunology" in name:
            cust_class = "specialty"
            specialty = True
            cert_days_offset = random.randint(150, 400)
            cert_date = BASE_DATE - datetime.timedelta(days=cert_days_offset)
            tier = random.choice([2, 3])
        elif "Midwest Health" in name:
            cust_class = "hospital"
            specialty = False
            cert_date = None
            tier = 3
        else:
            cust_class = random.choice(["retail", "retail", "retail", "independent"])
            specialty = random.random() < 0.15
            if specialty:
                cert_days_offset = random.randint(90, 365)
                cert_date = BASE_DATE - datetime.timedelta(days=cert_days_offset)
            else:
                cert_date = None
            tier = random.choice([1, 1, 1, 2, 2, 3])
        
        region = random.choice(regions) if "Midwest" not in name else "Midwest"
        onboard_days = random.randint(365, 1500)
        onboard_date = BASE_DATE - datetime.timedelta(days=onboard_days)
        
        cert_str = f"'{cert_date}'" if cert_date else "NULL"
        customer_values.append(f"('{name}', '{cust_class}', {tier}, {str(specialty).upper()}, {cert_str}, '{region}', '{onboard_date}')")
    
    lines.append(",\n".join(customer_values) + ";\n")
    
    lines.append("INSERT INTO rebate_tiers (tier_name, min_volume, max_volume, base_rate, effective_date) VALUES")
    tier_values = [
        "('Bronze', 0, 9999, 0.0200, '2024-01-01')",
        "('Silver', 10000, 29999, 0.0350, '2024-01-01')",
        "('Gold', 30000, 49999, 0.0500, '2024-01-01')",
        "('Platinum', 50000, NULL, 0.0750, '2024-01-01')"
    ]
    lines.append(",\n".join(tier_values) + ";\n")
    
    lines.append("INSERT INTO price_lists (name, effective_date, expiry_date, adjustment_factor) VALUES")
    price_list_values = [
        "('Q3 2024 Standard', '2024-07-01', '2024-09-30', 1.0000)",
        "('Q4 2024 Standard', '2024-10-01', '2024-12-31', 1.0250)",
        "('Q1 2025 Standard', '2025-01-01', NULL, 1.0380)"
    ]
    lines.append(",\n".join(price_list_values) + ";\n")
    
    lines.append("INSERT INTO seasonal_factors (product_category, month, demand_multiplier, year) VALUES")
    seasonal_values = []
    for month in range(1, 13):
        for cat in ["generic", "brand", "specialty"]:
            if cat == "brand" and month in [10, 11, 12, 1, 2]:
                mult = round(1.0 + random.uniform(0.15, 0.35), 3)
            elif cat == "generic" and month in [11, 12, 1]:
                mult = round(1.0 + random.uniform(0.08, 0.18), 3)
            else:
                mult = round(1.0 + random.uniform(-0.05, 0.08), 3)
            seasonal_values.append(f"('{cat}', {month}, {mult}, 2024)")
            seasonal_values.append(f"('{cat}', {month}, {mult}, 2025)")
    lines.append(",\n".join(seasonal_values) + ";\n")
    
    lines.append("INSERT INTO contracts (customer_id, contract_type, start_date, end_date, quarterly_target, notes) VALUES")
    contract_values = []
    for cid in range(1, len(CUSTOMER_NAMES) + 1):
        if cid <= 32:
            target = random.randint(8000, 25000)
            ctype = "standard"
        elif cid <= 37:
            target = random.randint(40000, 65000)
            ctype = "hospital_system"
        else:
            target = random.randint(15000, 45000)
            ctype = "specialty"
        
        start = BASE_DATE - datetime.timedelta(days=random.randint(180, 730))
        contract_values.append(f"({cid}, '{ctype}', '{start}', NULL, {target}, NULL)")
    lines.append(",\n".join(contract_values) + ";\n")
    
    lines.append("INSERT INTO hospital_contracts (hospital_system, pharmacy_customer_id, effective_date, volume_commitment, notes) VALUES")
    hc_values = []
    for cid in range(33, 38):
        hc_values.append(f"('Midwest Health Systems', {cid}, '2024-10-15', 55000, 'New regional contract - Q4 2024 expansion')")
    lines.append(",\n".join(hc_values) + ";\n")
    
    lines.append("INSERT INTO specialty_certifications (customer_id, certification_type, granted_date, expiry_date, status) VALUES")
    cert_values = []
    for cid in range(1, len(CUSTOMER_NAMES) + 1):
        name = CUSTOMER_NAMES[cid - 1]
        if "Specialty" in name or "Oncology" in name or "Infusion" in name or "Rare Disease" in name or "Bio" in name or "Immunology" in name:
            days_ago = random.randint(150, 400)
            granted = BASE_DATE - datetime.timedelta(days=days_ago)
            cert_values.append(f"({cid}, 'URAC Specialty Pharmacy', '{granted}', NULL, 'active')")
        elif random.random() < 0.15:
            days_ago = random.choice([180, 181, 182, 185, 190, 200, 220, 250, 300])
            granted = BASE_DATE - datetime.timedelta(days=days_ago)
            cert_values.append(f"({cid}, 'Limited Distribution', '{granted}', NULL, 'active')")
    lines.append(",\n".join(cert_values) + ";\n")
    
    order_id = 1
    line_id = 1
    order_values = []
    line_values = []
    
    quarters = [
        ("2024Q3", datetime.date(2024, 7, 1), datetime.date(2024, 9, 30)),
        ("2024Q4", datetime.date(2024, 10, 1), datetime.date(2024, 12, 31)),
        ("2025Q1", datetime.date(2025, 1, 1), datetime.date(2025, 1, 15)),
    ]
    
    for cid in range(1, len(CUSTOMER_NAMES) + 1):
        name = CUSTOMER_NAMES[cid - 1]
        
        if "Midwest Health" in name:
            base_orders_per_q = random.randint(12, 18)
            units_per_order = random.randint(2500, 4500)
        elif "Specialty" in name or "Oncology" in name:
            base_orders_per_q = random.randint(8, 14)
            units_per_order = random.randint(1200, 3000)
        else:
            base_orders_per_q = random.randint(6, 12)
            units_per_order = random.randint(400, 1800)
        
        for qtr, q_start, q_end in quarters:
            if "Midwest Health" in name and qtr == "2024Q4":
                num_orders = int(base_orders_per_q * 1.25)
                units_mult = 1.15
            elif qtr in ["2024Q4", "2025Q1"]:
                num_orders = int(base_orders_per_q * random.uniform(1.05, 1.15))
                units_mult = random.uniform(1.02, 1.08)
            else:
                num_orders = base_orders_per_q
                units_mult = 1.0
            
            for _ in range(num_orders):
                days_in_q = (q_end - q_start).days
                order_date = q_start + datetime.timedelta(days=random.randint(0, days_in_q))
                
                total_units = 0
                total_amount = Decimal("0.00")
                
                num_lines = random.randint(3, 12)
                order_line_data = []
                
                for _ in range(num_lines):
                    prod_id = random.randint(1, len(PRODUCT_NAMES))
                    prod_name, prod_cat, prod_price = PRODUCT_NAMES[prod_id - 1]
                    
                    if "Specialty" in name and prod_cat == "specialty":
                        qty = random.randint(5, 25)
                    elif prod_cat == "specialty":
                        qty = random.randint(1, 8) if random.random() < 0.3 else 0
                    elif prod_cat == "brand":
                        qty = random.randint(20, 150)
                    else:
                        qty = random.randint(50, 400)
                    
                    if qty > 0:
                        qty = int(qty * units_mult)
                        unit_price = Decimal(str(prod_price)) * Decimal(str(random.uniform(0.92, 1.08)))
                        unit_price = unit_price.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        line_total = unit_price * qty
                        
                        total_units += qty
                        total_amount += line_total
                        order_line_data.append((prod_id, qty, unit_price, line_total))
                
                if total_units > 0:
                    order_values.append(f"({order_id}, {cid}, '{order_date}', {total_units}, {total_amount}, '{qtr}')")
                    
                    for prod_id, qty, unit_price, line_total in order_line_data:
                        line_values.append(f"({line_id}, {order_id}, {prod_id}, {qty}, {unit_price}, {line_total})")
                        line_id += 1
                    
                    order_id += 1
    
    lines.append("INSERT INTO orders (order_id, customer_id, order_date, total_units, total_amount, quarter) VALUES")
    for i in range(0, len(order_values), 500):
        chunk = order_values[i:i+500]
        lines.append(",\n".join(chunk) + ";\n")
    
    lines.append("INSERT INTO order_lines (line_id, order_id, product_id, quantity, unit_price, line_total) VALUES")
    for i in range(0, len(line_values), 500):
        chunk = line_values[i:i+500]
        lines.append(",\n".join(chunk) + ";\n")
    
    lines.append("""
INSERT INTO rebate_payments (customer_id, quarter, quarterly_units, quarterly_target, specialty_ratio, certification_days, calculated_rebate, payment_date, status)
SELECT 
    o.customer_id,
    o.quarter,
    SUM(o.total_units) as quarterly_units,
    c.quarterly_target,
    COALESCE(
        (SELECT SUM(ol.quantity)::DECIMAL / NULLIF(SUM(o2.total_units), 0)
         FROM orders o2
         JOIN order_lines ol ON o2.order_id = ol.order_id
         JOIN products p ON ol.product_id = p.product_id
         WHERE o2.customer_id = o.customer_id AND o2.quarter = o.quarter AND p.category = 'specialty'),
        0
    ) as specialty_ratio,
    CASE WHEN cu.certification_date IS NOT NULL 
         THEN (DATE '2025-01-15' - cu.certification_date)
         ELSE NULL END as certification_days,
    0.00 as calculated_rebate,
    NULL as payment_date,
    'pending' as status
FROM orders o
JOIN contracts c ON o.customer_id = c.customer_id
JOIN customers cu ON o.customer_id = cu.customer_id
GROUP BY o.customer_id, o.quarter, c.quarterly_target, cu.certification_date;
""")
    
    return "\n".join(lines)

if __name__ == "__main__":
    sql = generate_sql()
    output_path = os.path.join(os.path.dirname(__file__), "_seed_data", "init.sql")
    with open(output_path, "w") as f:
        f.write(sql)
    print(f"Generated {output_path}")
