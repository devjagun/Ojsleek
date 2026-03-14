import random
import os
from datetime import datetime, timedelta

random.seed(42)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SEED_DIR = os.path.join(SCRIPT_DIR, '_seed_data')
os.makedirs(SEED_DIR, exist_ok=True)

REGIONS = ['North', 'South', 'East', 'West']
TIERS = ['Gold', 'Silver', 'Bronze', 'Standard']
TIER_WEIGHTS = [15, 25, 30, 30]
VEHICLE_TYPES = ['Sprinter', 'Transit', 'ProMaster', 'Box Truck']
WEATHER_CONDITIONS = ['Clear', 'Rain', 'Snow', 'Fog', 'Overcast']

ZONES = [
    (1, 'Downtown Core', 4.2, 'North'),
    (2, 'Industrial Park', 3.8, 'North'),
    (3, 'Suburban Heights', 2.5, 'South'),
    (4, 'Riverside District', 3.1, 'South'),
    (5, 'Airport Zone', 4.5, 'East'),
    (6, 'University Quarter', 2.8, 'East'),
    (7, 'Harbor Front', 3.9, 'West'),
    (8, 'Tech Campus', 2.2, 'West'),
    (9, 'Medical Center', 4.0, 'North'),
    (10, 'Shopping District', 3.3, 'South'),
    (11, 'Warehouse District', 3.6, 'West'),
    (12, 'Financial Center', 4.3, 'North'),
]

def generate_drivers(n=75):
    drivers = []
    first_names = ['James', 'Maria', 'Robert', 'Linda', 'Michael', 'Sarah', 'David', 'Jennifer', 
                   'William', 'Patricia', 'Richard', 'Elizabeth', 'Joseph', 'Barbara', 'Thomas',
                   'Susan', 'Charles', 'Jessica', 'Christopher', 'Karen', 'Daniel', 'Nancy',
                   'Matthew', 'Lisa', 'Anthony', 'Betty', 'Mark', 'Margaret', 'Donald', 'Sandra',
                   'Steven', 'Ashley', 'Paul', 'Dorothy', 'Andrew', 'Kimberly', 'Joshua', 'Emily']
    last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                  'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                  'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Perez', 'Thompson',
                  'White', 'Harris', 'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker',
                  'Young', 'Allen', 'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill']
    
    for i in range(1, n + 1):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        years_ago = random.randint(1, 8)
        hire_date = datetime(2026, 3, 12) - timedelta(days=years_ago * 365 + random.randint(0, 364))
        tier = random.choices(TIERS, weights=TIER_WEIGHTS)[0]
        region = random.choice(REGIONS)
        license_class = random.choice(['A', 'B', 'C'])
        training_batch = f"TB-{random.randint(2019, 2025)}-{random.randint(1, 12):02d}"
        drivers.append((i, name, hire_date.strftime('%Y-%m-%d'), tier, 'active', region, license_class, training_batch))
    
    return drivers

def generate_vehicle_assignments(drivers):
    assignments = []
    assignment_id = 1
    for driver in drivers:
        driver_id = driver[0]
        vehicle_type = random.choice(VEHICLE_TYPES)
        vehicle_id = f"VH-{random.randint(1000, 9999)}"
        mileage = random.randint(15000, 120000)
        last_service = datetime(2026, 3, 12) - timedelta(days=random.randint(5, 60))
        fuel_efficiency = round(random.uniform(12.0, 22.0), 1)
        assignments.append((assignment_id, driver_id, vehicle_type, vehicle_id, mileage, 
                          last_service.strftime('%Y-%m-%d'), fuel_efficiency))
        assignment_id += 1
    return assignments

def generate_zone_managers(zones, start_date, end_date):
    managers = []
    manager_names = ['Chen Wei', 'Rodriguez Pablo', 'Kim Soo-Min', 'Okonkwo Adaeze', 
                     'Mueller Hans', 'Patel Priya', 'Santos Miguel', 'Johansson Erik']
    
    for zone in zones:
        zone_id = zone[0]
        current_manager = random.choice(manager_names)
        changed_date = start_date + timedelta(days=random.randint(20, 35))
        
        if random.random() < 0.4:
            previous_manager = random.choice([m for m in manager_names if m != current_manager])
            managers.append((zone_id, previous_manager, start_date.strftime('%Y-%m-%d'), 
                           (changed_date - timedelta(days=1)).strftime('%Y-%m-%d')))
            managers.append((zone_id, current_manager, changed_date.strftime('%Y-%m-%d'), None))
        else:
            managers.append((zone_id, current_manager, start_date.strftime('%Y-%m-%d'), None))
    
    return managers

def generate_weather_events(start_date, end_date):
    events = []
    event_id = 1
    current = start_date
    
    while current <= end_date:
        for region in REGIONS:
            if random.random() < 0.3:
                condition = random.choice(['Rain', 'Snow', 'Fog'])
                severity = random.choice(['Light', 'Moderate', 'Heavy'])
                duration_hours = random.randint(2, 12)
                events.append((event_id, current.strftime('%Y-%m-%d'), region, condition, 
                             severity, duration_hours))
                event_id += 1
        current += timedelta(days=1)
    
    return events

def generate_training_completions(drivers):
    completions = []
    comp_id = 1
    training_types = ['Safety Refresher', 'Customer Service', 'Route Optimization', 
                      'Vehicle Maintenance', 'Hazmat Certification', 'Defensive Driving']
    
    for driver in drivers:
        driver_id = driver[0]
        hire_date = datetime.strptime(driver[2], '%Y-%m-%d')
        
        num_trainings = random.randint(2, 5)
        for _ in range(num_trainings):
            training = random.choice(training_types)
            completion_date = hire_date + timedelta(days=random.randint(30, 500))
            if completion_date < datetime(2026, 3, 12):
                score = random.randint(70, 100) if random.random() > 0.1 else None
                completions.append((comp_id, driver_id, training, 
                                  completion_date.strftime('%Y-%m-%d'), score))
                comp_id += 1
    
    return completions

def generate_zone_history(drivers, zones):
    history = []
    for driver in drivers:
        driver_id = driver[0]
        num_zones = random.randint(2, 6)
        assigned_zones = random.sample([z[0] for z in zones], min(num_zones, len(zones)))
        
        for zone_id in assigned_zones:
            days_worked = random.choices(
                [random.randint(5, 25), 30, random.randint(31, 60), random.randint(61, 150)],
                weights=[35, 25, 25, 15]
            )[0]
            first_date = datetime(2026, 3, 12) - timedelta(days=days_worked + random.randint(0, 45))
            last_worked = first_date + timedelta(days=days_worked - 1) if random.random() > 0.2 else None
            history.append((driver_id, zone_id, first_date.strftime('%Y-%m-%d'), days_worked,
                          last_worked.strftime('%Y-%m-%d') if last_worked else None))
    
    return history

def generate_feedback(drivers, zone_history):
    feedback = []
    feedback_id = 1
    
    zone_map = {}
    for zh in zone_history:
        key = (zh[0], zh[1])
        zone_map[key] = zh[3]
    
    for driver in drivers:
        driver_id = driver[0]
        tier = driver[3]
        
        base_rating = {'Gold': 4.4, 'Silver': 4.0, 'Bronze': 3.6, 'Standard': 3.3}[tier]
        
        zones_for_driver = [zh[1] for zh in zone_history if zh[0] == driver_id]
        
        for zone_id in zones_for_driver:
            num_feedback = random.randint(3, 25)
            for _ in range(num_feedback):
                rating = min(5.0, max(1.0, base_rating + random.gauss(0, 0.6)))
                rating = round(rating, 1)
                days_ago = random.randint(1, 120)
                feedback_date = datetime(2026, 3, 12) - timedelta(days=days_ago)
                comment = random.choice([None, None, None, 'Good service', 'Very professional', 
                                        'Package damaged', 'Late delivery', 'Excellent'])
                feedback.append((feedback_id, driver_id, zone_id, rating, 
                               feedback_date.strftime('%Y-%m-%d'), comment))
                feedback_id += 1
    
    return feedback

def generate_shifts(drivers, zones, zone_history, start_date, end_date):
    shifts = []
    shift_id = 1
    
    zone_map = {}
    for zh in zone_history:
        key = (zh[0], zh[1])
        zone_map[key] = True
    
    current = start_date
    while current <= end_date:
        if current.weekday() < 6:
            for driver in drivers:
                driver_id = driver[0]
                tier = driver[3]
                
                if random.random() < 0.08:
                    continue
                
                available_zones = [z[0] for z in zones if (driver_id, z[0]) in zone_map]
                if not available_zones:
                    available_zones = [random.choice([z[0] for z in zones])]
                
                zone_id = random.choice(available_zones)
                zone_diff = next(z[2] for z in zones if z[0] == zone_id)
                
                base_target = int(25 + (5 - zone_diff) * 3)
                target = base_target + random.randint(-3, 3)
                
                perf_modifier = {'Gold': 1.15, 'Silver': 1.05, 'Bronze': 0.95, 'Standard': 0.90}[tier]
                deliveries = int(target * perf_modifier * random.uniform(0.82, 1.22))
                
                start_hour = random.randint(5, 10)
                start_time = f"{start_hour:02d}:{random.choice(['00', '15', '30', '45'])}:00"
                end_hour = start_hour + random.randint(8, 11)
                end_time = f"{min(end_hour, 23):02d}:{random.choice(['00', '15', '30', '45'])}:00"
                break_mins = random.choice([30, 45, 60])
                
                overtime_flag = 'Y' if end_hour > 18 else 'N'
                route_miles = round(random.uniform(45, 180), 1)
                
                shifts.append((shift_id, driver_id, current.strftime('%Y-%m-%d'), zone_id,
                             start_time, end_time, deliveries, target, break_mins, 
                             overtime_flag, route_miles))
                shift_id += 1
        
        current += timedelta(days=1)
    
    return shifts

def generate_fuel_costs(start_date, end_date):
    costs = []
    current = start_date
    
    base_price = 3.20
    
    while current <= end_date:
        week_num = (current - start_date).days // 7
        if week_num >= 4:
            base_price = 3.78
        
        for region in REGIONS:
            daily_var = random.uniform(-0.08, 0.08)
            region_adj = {'North': 0.05, 'South': -0.03, 'East': 0.02, 'West': -0.01}[region]
            price = round(base_price + daily_var + region_adj, 2)
            
            week_start = current - timedelta(days=current.weekday())
            weekly_avg = round(base_price + region_adj, 2)
            
            costs.append((current.strftime('%Y-%m-%d'), region, price, weekly_avg))
        
        current += timedelta(days=1)
    
    return costs

def generate_route_incidents(shifts):
    incidents = []
    incident_id = 1
    incident_types = ['Traffic Delay', 'Customer Not Home', 'Access Issue', 
                      'Vehicle Issue', 'Weather Delay', 'Missing Package']
    
    for shift in shifts:
        if random.random() < 0.12:
            shift_id = shift[0]
            inc_type = random.choice(incident_types)
            delay_mins = random.randint(5, 45) if 'Delay' in inc_type else 0
            resolved = random.choice([True, True, True, False])
            incidents.append((incident_id, shift_id, inc_type, delay_mins, resolved))
            incident_id += 1
    
    return incidents

def apply_calc_rules(deliveries, target, base_difficulty, avg_rating, zone_days, tier, tenure_years):
    diff = deliveries - target
    if diff > 0:
        adjustment = diff * 1.15
    else:
        adjustment = diff * 0.85
    bpi = target + adjustment
    bpi = round(bpi, 2)
    
    if avg_rating > 4.2:
        rating_factor = 0.92
    else:
        rating_factor = 1.0
    
    if zone_days >= 30:
        familiarity_factor = 0.88
    else:
        familiarity_factor = 1.0
    
    azdf = base_difficulty * rating_factor * familiarity_factor
    azdf = round(azdf, 3)
    
    score = bpi * azdf
    
    if score > 150:
        rate = 1.10
    elif tier == 'Gold':
        rate = 1.15
    elif tier == 'Gold' and score > 150:
        rate = 1.25
    elif tenure_years > 2:
        rate = 1.05
    else:
        rate = 1.00
    
    return bpi, azdf, score, rate, score * rate

def generate_bonus_payments(shifts, drivers, zones, zone_history, feedback):
    payments = []
    payment_id = 1
    
    driver_map = {d[0]: d for d in drivers}
    zone_map = {z[0]: z for z in zones}
    
    zone_days_map = {}
    for zh in zone_history:
        zone_days_map[(zh[0], zh[1])] = zh[3]
    
    feedback_map = {}
    for f in feedback:
        key = (f[1], f[2])
        if key not in feedback_map:
            feedback_map[key] = []
        feedback_map[key].append(f[3])
    
    for shift in shifts:
        shift_id, driver_id, shift_date, zone_id = shift[0], shift[1], shift[2], shift[3]
        deliveries, target = shift[6], shift[7]
        
        driver = driver_map[driver_id]
        tier = driver[3]
        hire_date = datetime.strptime(driver[2], '%Y-%m-%d')
        tenure_years = (datetime(2026, 3, 12) - hire_date).days // 365
        
        zone = zone_map[zone_id]
        base_difficulty = zone[2]
        
        zone_days = zone_days_map.get((driver_id, zone_id), 0)
        
        ratings = feedback_map.get((driver_id, zone_id), [3.5])
        avg_rating = sum(ratings) / len(ratings)
        
        bpi, azdf, score, rate, bonus = apply_calc_rules(
            deliveries, target, base_difficulty, avg_rating, zone_days, tier, tenure_years
        )
        
        calculated_at = shift_date
        paid_at = None
        batch_id = f"BATCH-{shift_date[:7]}-{random.randint(100, 999)}"
        status = random.choice(['Pending', 'Pending', 'Pending', 'Paid', 'Review'])
        
        payments.append((payment_id, driver_id, shift_id, shift_date, bpi, azdf, rate, score, 
                        bonus, calculated_at, paid_at, batch_id, status))
        payment_id += 1
    
    return payments

def generate_audit_log(payments):
    logs = []
    log_id = 1
    
    for payment in payments:
        payment_id = payment[0]
        shift_date = payment[3]
        
        logs.append((log_id, payment_id, shift_date, 'CALC_START', 'bonus_engine', None))
        log_id += 1
        logs.append((log_id, payment_id, shift_date, 'CALC_COMPLETE', 'bonus_engine', 
                    f"bonus={payment[8]}"))
        log_id += 1
        
        if random.random() < 0.05:
            logs.append((log_id, payment_id, shift_date, 'MANUAL_REVIEW', 'payroll_admin', 
                        'Flagged for verification'))
            log_id += 1
    
    return logs

def write_sql():
    drivers = generate_drivers(75)
    vehicle_assignments = generate_vehicle_assignments(drivers)
    zone_history = generate_zone_history(drivers, ZONES)
    feedback = generate_feedback(drivers, zone_history)
    
    start_date = datetime(2026, 1, 6)
    end_date = datetime(2026, 3, 10)
    
    zone_managers = generate_zone_managers(ZONES, start_date, end_date)
    weather_events = generate_weather_events(start_date, end_date)
    training_completions = generate_training_completions(drivers)
    shifts = generate_shifts(drivers, ZONES, zone_history, start_date, end_date)
    fuel_costs = generate_fuel_costs(start_date, end_date)
    route_incidents = generate_route_incidents(shifts)
    payments = generate_bonus_payments(shifts, drivers, ZONES, zone_history, feedback)
    audit_logs = generate_audit_log(payments)
    
    with open(os.path.join(SEED_DIR, 'init.sql'), 'w') as f:
        f.write("CREATE TABLE IF NOT EXISTS drivers (\n")
        f.write("    driver_id INTEGER PRIMARY KEY,\n")
        f.write("    name VARCHAR(100),\n")
        f.write("    hire_date DATE,\n")
        f.write("    tier VARCHAR(20),\n")
        f.write("    status VARCHAR(20),\n")
        f.write("    region VARCHAR(20),\n")
        f.write("    license_class CHAR(1),\n")
        f.write("    training_batch VARCHAR(20)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS vehicle_assignments (\n")
        f.write("    assignment_id INTEGER PRIMARY KEY,\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    vehicle_type VARCHAR(50),\n")
        f.write("    vehicle_id VARCHAR(20),\n")
        f.write("    current_mileage INTEGER,\n")
        f.write("    last_service_date DATE,\n")
        f.write("    avg_fuel_efficiency DECIMAL(4,1)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS zones (\n")
        f.write("    zone_id INTEGER PRIMARY KEY,\n")
        f.write("    zone_name VARCHAR(100),\n")
        f.write("    base_difficulty DECIMAL(3,1),\n")
        f.write("    region VARCHAR(20),\n")
        f.write("    active BOOLEAN DEFAULT TRUE,\n")
        f.write("    max_daily_routes INTEGER DEFAULT 50\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS zone_managers (\n")
        f.write("    zone_id INTEGER REFERENCES zones(zone_id),\n")
        f.write("    manager_name VARCHAR(100),\n")
        f.write("    start_date DATE,\n")
        f.write("    end_date DATE\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS weather_events (\n")
        f.write("    event_id INTEGER PRIMARY KEY,\n")
        f.write("    event_date DATE,\n")
        f.write("    region VARCHAR(20),\n")
        f.write("    condition VARCHAR(30),\n")
        f.write("    severity VARCHAR(20),\n")
        f.write("    duration_hours INTEGER\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS training_completions (\n")
        f.write("    completion_id INTEGER PRIMARY KEY,\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    training_type VARCHAR(50),\n")
        f.write("    completion_date DATE,\n")
        f.write("    score INTEGER\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS shifts (\n")
        f.write("    shift_id INTEGER PRIMARY KEY,\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    shift_date DATE,\n")
        f.write("    zone_id INTEGER REFERENCES zones(zone_id),\n")
        f.write("    start_time TIME,\n")
        f.write("    end_time TIME,\n")
        f.write("    deliveries_completed INTEGER,\n")
        f.write("    route_target INTEGER,\n")
        f.write("    break_minutes INTEGER,\n")
        f.write("    overtime_flag CHAR(1),\n")
        f.write("    route_miles DECIMAL(6,1)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS driver_zone_history (\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    zone_id INTEGER REFERENCES zones(zone_id),\n")
        f.write("    first_worked_date DATE,\n")
        f.write("    total_days_in_zone INTEGER,\n")
        f.write("    last_worked_date DATE,\n")
        f.write("    PRIMARY KEY (driver_id, zone_id)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS feedback (\n")
        f.write("    feedback_id INTEGER PRIMARY KEY,\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    zone_id INTEGER REFERENCES zones(zone_id),\n")
        f.write("    rating DECIMAL(2,1),\n")
        f.write("    feedback_date DATE,\n")
        f.write("    comment TEXT\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS fuel_costs (\n")
        f.write("    date DATE,\n")
        f.write("    region VARCHAR(20),\n")
        f.write("    price_per_gallon DECIMAL(4,2),\n")
        f.write("    weekly_average DECIMAL(4,2),\n")
        f.write("    PRIMARY KEY (date, region)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS route_incidents (\n")
        f.write("    incident_id INTEGER PRIMARY KEY,\n")
        f.write("    shift_id INTEGER REFERENCES shifts(shift_id),\n")
        f.write("    incident_type VARCHAR(50),\n")
        f.write("    delay_minutes INTEGER,\n")
        f.write("    resolved BOOLEAN\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS bonus_payments (\n")
        f.write("    payment_id INTEGER PRIMARY KEY,\n")
        f.write("    driver_id INTEGER REFERENCES drivers(driver_id),\n")
        f.write("    shift_id INTEGER REFERENCES shifts(shift_id),\n")
        f.write("    shift_date DATE,\n")
        f.write("    base_performance_index DECIMAL(10,2),\n")
        f.write("    zone_difficulty_factor DECIMAL(6,3),\n")
        f.write("    tier_multiplier DECIMAL(4,2),\n")
        f.write("    final_score DECIMAL(10,2),\n")
        f.write("    bonus_amount DECIMAL(10,2),\n")
        f.write("    calculated_at TIMESTAMP,\n")
        f.write("    paid_at TIMESTAMP,\n")
        f.write("    batch_id VARCHAR(30),\n")
        f.write("    status VARCHAR(20),\n")
        f.write("    UNIQUE (driver_id, shift_date)\n")
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS calc_audit_log (\n")
        f.write("    log_id INTEGER PRIMARY KEY,\n")
        f.write("    payment_id INTEGER REFERENCES bonus_payments(payment_id),\n")
        f.write("    log_date DATE,\n")
        f.write("    event_type VARCHAR(30),\n")
        f.write("    source_system VARCHAR(30),\n")
        f.write("    details TEXT\n")
        f.write(");\n\n")
        
        for d in drivers:
            f.write(f"INSERT INTO drivers VALUES ({d[0]}, '{d[1]}', '{d[2]}', '{d[3]}', '{d[4]}', '{d[5]}', '{d[6]}', '{d[7]}');\n")
        f.write("\n")
        
        for va in vehicle_assignments:
            f.write(f"INSERT INTO vehicle_assignments VALUES ({va[0]}, {va[1]}, '{va[2]}', '{va[3]}', {va[4]}, '{va[5]}', {va[6]});\n")
        f.write("\n")
        
        for z in ZONES:
            max_routes = random.randint(35, 65)
            f.write(f"INSERT INTO zones VALUES ({z[0]}, '{z[1]}', {z[2]}, '{z[3]}', TRUE, {max_routes});\n")
        f.write("\n")
        
        for zm in zone_managers:
            end_val = f"'{zm[3]}'" if zm[3] else 'NULL'
            f.write(f"INSERT INTO zone_managers VALUES ({zm[0]}, '{zm[1]}', '{zm[2]}', {end_val});\n")
        f.write("\n")
        
        for we in weather_events:
            f.write(f"INSERT INTO weather_events VALUES ({we[0]}, '{we[1]}', '{we[2]}', '{we[3]}', '{we[4]}', {we[5]});\n")
        f.write("\n")
        
        for tc in training_completions:
            score_val = tc[4] if tc[4] is not None else 'NULL'
            f.write(f"INSERT INTO training_completions VALUES ({tc[0]}, {tc[1]}, '{tc[2]}', '{tc[3]}', {score_val});\n")
        f.write("\n")
        
        for zh in zone_history:
            last_worked = f"'{zh[4]}'" if zh[4] else 'NULL'
            f.write(f"INSERT INTO driver_zone_history VALUES ({zh[0]}, {zh[1]}, '{zh[2]}', {zh[3]}, {last_worked});\n")
        f.write("\n")
        
        for fb in feedback:
            comment_val = f"'{fb[5]}'" if fb[5] else 'NULL'
            f.write(f"INSERT INTO feedback VALUES ({fb[0]}, {fb[1]}, {fb[2]}, {fb[3]}, '{fb[4]}', {comment_val});\n")
        f.write("\n")
        
        for s in shifts:
            f.write(f"INSERT INTO shifts VALUES ({s[0]}, {s[1]}, '{s[2]}', {s[3]}, '{s[4]}', '{s[5]}', {s[6]}, {s[7]}, {s[8]}, '{s[9]}', {s[10]});\n")
        f.write("\n")
        
        for fc in fuel_costs:
            f.write(f"INSERT INTO fuel_costs VALUES ('{fc[0]}', '{fc[1]}', {fc[2]}, {fc[3]});\n")
        f.write("\n")
        
        for ri in route_incidents:
            f.write(f"INSERT INTO route_incidents VALUES ({ri[0]}, {ri[1]}, '{ri[2]}', {ri[3]}, {str(ri[4]).upper()});\n")
        f.write("\n")
        
        for p in payments:
            f.write(f"INSERT INTO bonus_payments VALUES ({p[0]}, {p[1]}, {p[2]}, '{p[3]}', {p[4]}, {p[5]}, {p[6]}, {p[7]}, {p[8]}, '{p[9]}', NULL, '{p[11]}', '{p[12]}');\n")
        f.write("\n")
        
        for al in audit_logs:
            details = f"'{al[5]}'" if al[5] else 'NULL'
            f.write(f"INSERT INTO calc_audit_log VALUES ({al[0]}, {al[1]}, '{al[2]}', '{al[3]}', '{al[4]}', {details});\n")

if __name__ == '__main__':
    write_sql()
    print("Generated seed data in _seed_data/init.sql")
            
