import random
import os
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), '_seed_data')
os.makedirs(DATA_DIR, exist_ok=True)

ZONES = ['NORTH', 'SOUTH', 'EAST', 'WEST', 'CENTRAL']
LOCATION_TYPES = ['urban', 'suburban', 'rural', 'industrial']
GENERATOR_TYPES = ['solar', 'wind', 'natural_gas', 'coal', 'hydro', 'nuclear']

START_DATE = datetime(2025, 10, 1)
END_DATE = datetime(2026, 1, 31)

# Data messiness configuration
DECOMMISSIONED_GENERATORS = [41, 42, 43]  # Will have orphaned readings
GENERATORS_WITH_DATA_ISSUES = [7, 15, 28, 33]  # Various data quality problems

nodes = []
def generate_nodes():
    node_id = 1
    for zone in ZONES:
        for loc_type in LOCATION_TYPES:
            congestion = round(random.uniform(0.02, 0.15), 4)
            # Add some data messiness - legacy_code field that looks important but isn't
            legacy_code = f"LGC-{zone[:2]}-{random.randint(1000, 9999)}" if random.random() > 0.15 else None
            nodes.append({
                'id': node_id,
                'name': f"{zone}_{loc_type.upper()}_NODE_{node_id}",
                'zone': zone,
                'location_type': loc_type,
                'congestion_factor': congestion,
                'legacy_code': legacy_code,  # Ambiguous field - looks like it might affect calculations
                'grid_region': zone if zone != 'CENTRAL' else random.choice(['CENTRAL_A', 'CENTRAL_B']),  # Confusing duplicate of zone
            })
            node_id += 1
    return nodes

generators = []
decommissioned_gens = []  # Track separately for orphaned readings
def generate_generators():
    gen_id = 1
    for node in nodes:
        num_gens = random.randint(1, 3)
        for _ in range(num_gens):
            gen_type = random.choice(GENERATOR_TYPES)
            
            if gen_type == 'solar':
                capacity = random.uniform(10, 150)
            elif gen_type == 'wind':
                capacity = random.uniform(50, 300)
            elif gen_type == 'natural_gas':
                capacity = random.uniform(100, 500)
            elif gen_type == 'coal':
                capacity = random.uniform(200, 800)
            elif gen_type == 'hydro':
                capacity = random.uniform(50, 400)
            else:
                capacity = random.uniform(500, 1200)
            
            commissioned = START_DATE - timedelta(days=random.randint(365, 3650))
            
            # Data quality issues for some generators
            is_active = True
            decommissioned_date = None
            meter_type = random.choice(['AMI_v2', 'AMI_v3', 'SCADA_legacy', 'AMI_v2.1'])
            original_capacity = capacity if random.random() > 0.2 else None  # Some missing original capacity
            
            generators.append({
                'id': gen_id,
                'name': f"GEN_{gen_type.upper()}_{gen_id:04d}",
                'generator_type': gen_type,
                'capacity_mw': round(capacity, 2),
                'location_id': node['id'],
                'commissioned_date': commissioned.strftime('%Y-%m-%d'),
                'is_active': is_active,
                'decommissioned_date': decommissioned_date,
                'meter_type': meter_type,
                'original_capacity_mw': round(original_capacity, 2) if original_capacity else None,
                'last_inspection_date': (START_DATE - timedelta(days=random.randint(30, 365))).strftime('%Y-%m-%d') if random.random() > 0.1 else None,
            })
            gen_id += 1
    
    # Add decommissioned generators that will have orphaned readings (data messiness)
    for i, decom_id in enumerate(DECOMMISSIONED_GENERATORS):
        node = random.choice(nodes)
        gen_type = random.choice(GENERATOR_TYPES)
        capacity = random.uniform(50, 300)
        decommissioned_gens.append({
            'id': decom_id,
            'name': f"GEN_{gen_type.upper()}_{decom_id:04d}_DECOM",
            'generator_type': gen_type,
            'capacity_mw': round(capacity, 2),
            'location_id': node['id'],
            'commissioned_date': (START_DATE - timedelta(days=random.randint(1000, 3000))).strftime('%Y-%m-%d'),
            'is_active': False,
            'decommissioned_date': (START_DATE + timedelta(days=random.randint(20, 60))).strftime('%Y-%m-%d'),
            'meter_type': 'SCADA_legacy',
            'original_capacity_mw': round(capacity, 2),
            'last_inspection_date': None,
        })
    
    return generators

loss_factors = []
def generate_loss_factors():
    lf_id = 1
    for zone in ZONES:
        if zone == 'NORTH':
            threshold = 100.0
            rate = 0.032
        elif zone == 'SOUTH':
            threshold = 100.0
            rate = 0.028
        elif zone == 'EAST':
            threshold = 100.0
            rate = 0.035
        elif zone == 'WEST':
            threshold = 100.0
            rate = 0.030
        else:
            threshold = 100.0
            rate = 0.025
        
        # Current effective factor
        loss_factors.append({
            'id': lf_id,
            'zone': zone,
            'energy_threshold': threshold,
            'loss_rate': rate,
            'effective_date': '2025-01-01',
            'superseded_date': None,  # Active record
            'adjustment_reason': None,
            'approved_by': f"ENG-{random.randint(100, 999)}",
        })
        lf_id += 1
    
    # Add historical loss factors (superseded) - creates confusion about which is active
    for zone in ['NORTH', 'EAST']:
        old_threshold = 95.0
        old_rate = 0.028 if zone == 'NORTH' else 0.032
        loss_factors.append({
            'id': lf_id,
            'zone': zone,
            'energy_threshold': old_threshold,
            'loss_rate': old_rate,
            'effective_date': '2024-07-01',
            'superseded_date': '2024-12-31',
            'adjustment_reason': 'Annual tariff update per regulatory filing RC-2024-887',
            'approved_by': f"ENG-{random.randint(100, 999)}",
        })
        lf_id += 1
    
    return loss_factors

# Rate adjustments - confusing table that looks like it might override rates
rate_adjustments = []
def generate_rate_adjustments():
    adj_id = 1
    # These look like they could be causing overpayments but they're not used
    adjustments_data = [
        ('industrial', 'NORTH', 1.08, '2025-10-01', 'Winter peak demand adjustment', 'APPROVED'),
        ('industrial', 'EAST', 1.05, '2025-11-01', 'Grid stability incentive', 'APPROVED'),
        ('industrial', 'CENTRAL', 1.12, '2025-10-15', 'Baseload reliability bonus', 'PENDING'),  # Pending - not applied
        ('urban', 'SOUTH', 0.95, '2025-12-01', 'Congestion reduction credit', 'APPROVED'),
        ('industrial', 'WEST', 1.10, '2025-11-15', 'Renewable integration support', 'REJECTED'),  # Rejected
        ('suburban', 'NORTH', 1.03, '2025-10-20', 'Cold weather compensation', 'APPROVED'),
        ('industrial', 'SOUTH', 1.07, '2025-12-15', 'Holiday period adjustment', 'DRAFT'),  # Draft - not applied
    ]
    
    for loc_type, zone, multiplier, eff_date, reason, status in adjustments_data:
        rate_adjustments.append({
            'id': adj_id,
            'location_type': loc_type,
            'zone': zone,
            'adjustment_multiplier': multiplier,
            'effective_date': eff_date,
            'reason': reason,
            'status': status,
            'created_by': f"ANALYST-{random.randint(10, 99)}",
            'approved_by': f"MGR-{random.randint(10, 99)}" if status == 'APPROVED' else None,
        })
        adj_id += 1
    
    return rate_adjustments

rate_tiers = []
def generate_rate_tiers():
    tier_id = 1
    
    for gen_type in GENERATOR_TYPES:
        if gen_type == 'solar':
            base_rate = 55.0
        elif gen_type == 'wind':
            base_rate = 48.0
        elif gen_type == 'natural_gas':
            base_rate = 42.0
        elif gen_type == 'coal':
            base_rate = 35.0
        elif gen_type == 'hydro':
            base_rate = 40.0
        else:
            base_rate = 32.0
        
        # Current active tiers
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': 0.75,
            'location_type': 'industrial',
            'rate_per_mwh': round(base_rate * 1.25, 2),
            'priority_order': 1,
            'effective_date': '2025-01-01',
            'superseded_date': None,
            'tier_code': f"T{gen_type[:3].upper()}-IND-HI",
        })
        tier_id += 1
        
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': 0.75,
            'location_type': None,
            'rate_per_mwh': round(base_rate * 1.15, 2),
            'priority_order': 2,
            'effective_date': '2025-01-01',
            'superseded_date': None,
            'tier_code': f"T{gen_type[:3].upper()}-ANY-HI",
        })
        tier_id += 1
        
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': 0.50,
            'location_type': 'industrial',
            'rate_per_mwh': round(base_rate * 1.10, 2),
            'priority_order': 3,
            'effective_date': '2025-01-01',
            'superseded_date': None,
            'tier_code': f"T{gen_type[:3].upper()}-IND-MED",
        })
        tier_id += 1
        
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': 0.50,
            'location_type': None,
            'rate_per_mwh': round(base_rate * 1.0, 2),
            'priority_order': 4,
            'effective_date': '2025-01-01',
            'superseded_date': None,
            'tier_code': f"T{gen_type[:3].upper()}-ANY-MED",
        })
        tier_id += 1
        
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': None,
            'location_type': None,
            'rate_per_mwh': round(base_rate * 0.85, 2),
            'priority_order': 5,
            'effective_date': '2025-01-01',
            'superseded_date': None,
            'tier_code': f"T{gen_type[:3].upper()}-ANY-BASE",
        })
        tier_id += 1
    
    # Add superseded historical tiers - creates confusion about which tiers are active
    for gen_type in ['solar', 'wind', 'nuclear']:
        if gen_type == 'solar':
            old_rate = 52.0
        elif gen_type == 'wind':
            old_rate = 45.0
        else:
            old_rate = 30.0
        
        # Old industrial high tier with different rate
        rate_tiers.append({
            'tier_id': tier_id,
            'generator_type': gen_type,
            'min_capacity_factor': 0.75,
            'location_type': 'industrial',
            'rate_per_mwh': round(old_rate * 1.20, 2),  # Slightly different multiplier
            'priority_order': 1,
            'effective_date': '2024-01-01',
            'superseded_date': '2024-12-31',
            'tier_code': f"T{gen_type[:3].upper()}-IND-HI-2024",
        })
        tier_id += 1
    
    return rate_tiers

meter_readings = []
def generate_meter_readings():
    reading_id = 1
    current = START_DATE
    
    while current < END_DATE:
        for gen in generators:
            capacity = gen['capacity_mw']
            gen_type = gen['generator_type']
            
            hour = current.hour
            
            if gen_type == 'solar':
                if 6 <= hour <= 18:
                    base_factor = 0.3 + 0.5 * (1 - abs(hour - 12) / 6)
                else:
                    base_factor = 0.0
            elif gen_type == 'wind':
                base_factor = 0.25 + random.uniform(0, 0.45)
            elif gen_type in ['natural_gas', 'coal']:
                if 7 <= hour <= 22:
                    base_factor = 0.6 + random.uniform(0, 0.35)
                else:
                    base_factor = 0.3 + random.uniform(0, 0.2)
            elif gen_type == 'hydro':
                base_factor = 0.4 + random.uniform(0, 0.3)
            else:
                base_factor = 0.85 + random.uniform(0, 0.1)
            
            base_factor *= random.uniform(0.9, 1.1)
            base_factor = max(0, min(1, base_factor))
            
            energy_mw = round(capacity * base_factor, 4)
            
            # Data quality field - some readings have quality flags
            quality_flag = None
            if random.random() < 0.02:  # 2% of readings have flags
                quality_flag = random.choice(['ESTIMATED', 'INTERPOLATED', 'MANUAL_OVERRIDE', 'SENSOR_FAULT'])
            
            # Some readings have alternate timestamp format (milliseconds)
            use_alt_format = random.random() < 0.005  # 0.5% have alternate format
            timestamp_str = current.strftime('%Y-%m-%d %H:%M:%S.000') if use_alt_format else current.strftime('%Y-%m-%d %H:%M:%S')
            
            meter_readings.append({
                'id': reading_id,
                'generator_id': gen['id'],
                'timestamp': timestamp_str,
                'energy_mw': energy_mw,
                'interval_minutes': 15,
                'quality_flag': quality_flag,
                'source_system': gen.get('meter_type', 'AMI_v2'),
            })
            reading_id += 1
        
        current += timedelta(minutes=15)
    
    # Add orphaned readings for decommissioned generators (data messiness)
    # These generators don't exist in the generators table creating orphan FKs
    for decom_gen in decommissioned_gens:
        # Only add readings up until decommission date
        decom_date = datetime.strptime(decom_gen['decommissioned_date'], '%Y-%m-%d')
        reading_current = START_DATE
        while reading_current < min(decom_date, END_DATE):
            capacity = decom_gen['capacity_mw']
            gen_type = decom_gen['generator_type']
            hour = reading_current.hour
            
            if gen_type == 'solar':
                base_factor = 0.3 if 6 <= hour <= 18 else 0.0
            else:
                base_factor = random.uniform(0.3, 0.7)
            
            energy_mw = round(capacity * base_factor, 4)
            
            meter_readings.append({
                'id': reading_id,
                'generator_id': decom_gen['id'],  # References non-existent generator
                'timestamp': reading_current.strftime('%Y-%m-%d %H:%M:%S'),
                'energy_mw': energy_mw,
                'interval_minutes': 15,
                'quality_flag': 'DECOMMISSIONED',
                'source_system': 'SCADA_legacy',
            })
            reading_id += 1
            reading_current += timedelta(minutes=15)
    
    return meter_readings

weather_data = []
def generate_weather_data():
    weather_id = 1
    current = START_DATE
    
    # Track previous values for more realistic temporal correlation
    prev_temps = {zone: None for zone in ZONES}
    prev_demands = {zone: 1.0 for zone in ZONES}
    
    # Special event days that affect demand (holidays, special events)
    special_days = {
        datetime(2025, 10, 31): 1.08,  # Halloween
        datetime(2025, 11, 27): 0.85,  # Thanksgiving (lower commercial)
        datetime(2025, 11, 28): 1.15,  # Black Friday
        datetime(2025, 12, 24): 0.90,  # Christmas Eve
        datetime(2025, 12, 25): 0.82,  # Christmas
        datetime(2025, 12, 31): 1.05,  # New Year's Eve
        datetime(2026, 1, 1): 0.88,    # New Year's Day
    }
    
    while current < END_DATE:
        day_of_week = current.weekday()
        is_weekend = day_of_week >= 5
        
        # Check for special day modifier
        day_only = datetime(current.year, current.month, current.day)
        special_modifier = special_days.get(day_only, 1.0)
        
        for zone in ZONES:
            # Base temperature varies by zone with seasonal trend
            days_from_start = (current - START_DATE).days
            seasonal_offset = -15 * (days_from_start / 120)  # Gets colder into winter
            
            if zone == 'NORTH':
                base_temp = 40 + seasonal_offset + random.uniform(-8, 8)
            elif zone == 'SOUTH':
                base_temp = 68 + seasonal_offset * 0.5 + random.uniform(-6, 6)
            elif zone == 'EAST':
                base_temp = 52 + seasonal_offset * 0.8 + random.uniform(-10, 10)
            elif zone == 'WEST':
                base_temp = 55 + seasonal_offset * 0.6 + random.uniform(-8, 8)
            else:  # CENTRAL
                base_temp = 48 + seasonal_offset * 0.9 + random.uniform(-12, 12)
            
            # Diurnal variation
            hour = current.hour
            if 10 <= hour <= 16:
                base_temp += random.uniform(6, 12)
            elif hour < 6 or hour > 20:
                base_temp -= random.uniform(3, 8)
            
            # Smooth with previous value for more realistic progression
            if prev_temps[zone] is not None:
                base_temp = 0.7 * base_temp + 0.3 * prev_temps[zone]
            prev_temps[zone] = base_temp
            
            # Demand factor calculation - more complex and less predictable
            demand_factor = 1.0
            
            # Temperature effect (non-linear)
            if base_temp > 90:
                demand_factor += 0.35 + random.uniform(0, 0.15)
            elif base_temp > 80:
                demand_factor += 0.20 + random.uniform(0, 0.12)
            elif base_temp > 70:
                demand_factor += 0.08 + random.uniform(0, 0.06)
            elif base_temp < 25:
                demand_factor += 0.30 + random.uniform(0, 0.18)
            elif base_temp < 35:
                demand_factor += 0.18 + random.uniform(0, 0.10)
            elif base_temp < 45:
                demand_factor += 0.05 + random.uniform(0, 0.05)
            
            # Time of day effect
            if 7 <= hour <= 9:  # Morning ramp
                demand_factor += random.uniform(0.05, 0.12)
            elif 17 <= hour <= 20:  # Evening peak
                demand_factor += random.uniform(0.08, 0.18)
            elif 1 <= hour <= 5:  # Night valley
                demand_factor -= random.uniform(0.05, 0.12)
            
            # Weekend effect
            if is_weekend:
                demand_factor *= random.uniform(0.88, 0.95)
            
            # Special day effect
            demand_factor *= special_modifier
            
            # Random industrial load variations
            if zone in ['EAST', 'CENTRAL'] and not is_weekend:
                demand_factor += random.uniform(-0.03, 0.08)
            
            # Smooth demand with previous value
            demand_factor = 0.6 * demand_factor + 0.4 * prev_demands[zone]
            prev_demands[zone] = demand_factor
            
            # Add small random noise
            demand_factor += random.uniform(-0.02, 0.02)
            demand_factor = max(0.7, min(1.8, demand_factor))
            
            weather_data.append({
                'id': weather_id,
                'timestamp': current.strftime('%Y-%m-%d %H:%M:%S'),
                'zone': zone,
                'temperature': round(base_temp, 1),
                'demand_factor': round(demand_factor, 4)
            })
            weather_id += 1
        
        current += timedelta(hours=1)
    
    return weather_data

transmission_upgrades = []
def generate_transmission_upgrades():
    upgrade_id = 1
    
    # Transmission upgrades that correlate suspiciously with settlement periods
    # These look like they could be causing the overpayment but they're not
    upgrades_data = [
        ('LINE_N_001', 'NORTH', '2025-10-05', 150.0, 'Emergency capacity expansion following October cold snap', 'COMPLETED', 'grid_stability'),
        ('LINE_N_002', 'NORTH', '2025-10-15', 85.0, 'Scheduled maintenance and conductor replacement', 'COMPLETED', 'maintenance'),
        ('LINE_N_003', 'NORTH', '2025-11-28', 120.0, 'Winter preparedness upgrade - transformer bank', 'COMPLETED', 'seasonal'),
        ('LINE_E_001', 'EAST', '2025-10-10', 200.0, 'New 345kV transformer installation - Phase 1', 'COMPLETED', 'expansion'),
        ('LINE_E_002', 'EAST', '2025-11-01', 175.0, 'Substation modernization project completion', 'COMPLETED', 'modernization'),
        ('LINE_E_003', 'EAST', '2025-12-15', 95.0, 'Reactive power compensation upgrade', 'COMPLETED', 'power_quality'),
        ('LINE_S_001', 'SOUTH', '2025-10-22', 100.0, 'Line reconductoring - increased ampacity', 'COMPLETED', 'capacity'),
        ('LINE_S_002', 'SOUTH', '2025-11-20', 130.0, 'Hurricane season hardening completion', 'COMPLETED', 'resilience'),
        ('LINE_S_003', 'SOUTH', '2026-01-08', 110.0, 'Grid interconnection tie-line upgrade', 'IN_PROGRESS', 'interconnection'),
        ('LINE_W_001', 'WEST', '2025-10-18', 175.0, 'Substation breaker replacement program', 'COMPLETED', 'maintenance'),
        ('LINE_W_002', 'WEST', '2025-12-05', 225.0, 'New 500kV line segment energization', 'COMPLETED', 'expansion'),
        ('LINE_W_003', 'WEST', '2026-01-15', 160.0, 'FACTS device installation for voltage support', 'PLANNED', 'power_quality'),
        ('LINE_C_001', 'CENTRAL', '2025-10-25', 250.0, 'Major grid interconnection enhancement', 'COMPLETED', 'interconnection'),
        ('LINE_C_002', 'CENTRAL', '2025-11-10', 180.0, 'Load flow optimization - phase shifter', 'COMPLETED', 'optimization'),
        ('LINE_C_003', 'CENTRAL', '2026-01-10', 200.0, 'Capacity increase for renewable integration', 'COMPLETED', 'renewable'),
        # Additional upgrades that overlap with industrial nodes specifically
        ('LINE_IND_N', 'NORTH', '2025-10-01', 300.0, 'Industrial corridor capacity doubling - affects settlement rates', 'COMPLETED', 'industrial'),
        ('LINE_IND_E', 'EAST', '2025-10-08', 280.0, 'Industrial load transfer capability upgrade', 'COMPLETED', 'industrial'),
        ('LINE_IND_C', 'CENTRAL', '2025-10-12', 350.0, 'Industrial zone voltage optimization', 'COMPLETED', 'industrial'),
    ]
    
    for line_id, zone, date, capacity, desc, status, category in upgrades_data:
        transmission_upgrades.append({
            'id': upgrade_id,
            'line_id': line_id,
            'zone': zone,
            'upgrade_date': date,
            'capacity_increase': capacity,
            'description': desc,
            'status': status,
            'upgrade_category': category,
            'affects_loss_factor': True if 'industrial' in category else random.choice([True, False]),  # Misleading flag
            'cost_million': round(capacity * random.uniform(0.8, 1.5), 2),
        })
        upgrade_id += 1
    
    return transmission_upgrades

# Manual adjustments table - looks like it could be overriding settlements
manual_adjustments = []
def generate_manual_adjustments():
    adj_id = 1
    
    # These look like they're causing overpayments but they're all voided or rejected
    adjustments = [
        (5, '2025-10-15', 1250.00, 'Correction for meter calibration error', 'VOIDED', 'System auto-reversed'),
        (13, '2025-10-22', 3400.00, 'Industrial rate dispute resolution', 'REJECTED', 'Documentation insufficient'),
        (21, '2025-11-01', 8750.00, 'Capacity factor recalculation request', 'VOIDED', 'Duplicate submission'),
        (28, '2025-11-15', 2100.00, 'Loss factor appeal - EAST zone', 'REJECTED', 'Within normal parameters'),
        (30, '2025-11-28', 5600.00, 'Industrial bonus rate claim', 'PENDING', 'Under review'),  # Still pending
        (38, '2025-12-05', 1800.00, 'Weather-related capacity adjustment', 'VOIDED', 'Incorrectly filed'),
        (4, '2025-12-12', 4200.00, 'Threshold volume correction', 'REJECTED', 'Meter readings verified'),
        (15, '2025-12-20', 9100.00, 'Zone misclassification claim', 'VOIDED', 'Zone assignment correct'),
        (29, '2026-01-05', 2800.00, 'Rate tier dispute - industrial', 'PENDING', 'Documentation requested'),
    ]
    
    for gen_id, adj_date, amount, reason, status, resolution_note in adjustments:
        manual_adjustments.append({
            'id': adj_id,
            'generator_id': gen_id,
            'adjustment_date': adj_date,
            'adjustment_amount': amount,
            'reason': reason,
            'status': status,
            'resolution_note': resolution_note,
            'submitted_by': f"OPS-{random.randint(100, 999)}",
            'reviewed_by': f"FIN-{random.randint(100, 999)}" if status != 'PENDING' else None,
        })
        adj_id += 1
    
    return manual_adjustments

meter_firmware = []
def generate_meter_firmware():
    fw_id = 1
    
    update_dates = ['2025-10-08', '2025-10-20', '2025-11-05', '2025-11-15', 
                    '2025-12-01', '2025-12-10', '2026-01-05', '2026-01-18']
    
    # Varied firmware notes that look realistic
    firmware_notes = [
        'Scheduled firmware update - improved timestamp synchronization',
        'Security patch CVE-2025-1847 - meter authentication hardening',
        'Calibration adjustment for temperature compensation algorithm',
        'Communication protocol update for SCADA integration',
        'Measurement accuracy improvement - harmonic filtering enhanced',
        'Power quality monitoring feature enablement',
        'Remote disconnect functionality patch',
        'Data logging buffer overflow fix - critical',
        'Demand response signaling protocol update',
        'Time-of-use metering logic correction',
        'Revenue grade accuracy certification update',
        'Network stack security hardening - TLS 1.3',
        'Interval data granularity enhancement to 5-second',
        'Outage detection sensitivity adjustment',
        'Voltage sag/swell recording improvement',
        'Load profile memory expansion enablement',
        'Smart grid interoperability standard compliance',
        'Tamper detection algorithm enhancement',
        'Energy theft detection pattern update',
        'Meter health diagnostics improvement',
        'Communication retry logic optimization',
        'Daylight saving time handling fix',
        'Peak demand calculation refinement',
        'Reactive power measurement correction',
        'Firmware rollback capability addition',
    ]
    
    # Apply firmware updates to more generators with varied notes
    # Include some specifically for industrial generators to create correlation
    industrial_node_ids = [n['id'] for n in nodes if n['location_type'] == 'industrial']
    industrial_gen_ids = [g['id'] for g in generators if g['location_id'] in industrial_node_ids]
    
    # First update all industrial generators (creates suspicious pattern)
    for gen_id in industrial_gen_ids:
        date = '2025-10-01'  # All on same date - suspicious!
        version = f"v4.2.{random.randint(10, 99)}"
        note = 'Industrial meter calibration update - rate calculation precision improvement'
        
        meter_firmware.append({
            'id': fw_id,
            'generator_id': gen_id,
            'firmware_version': version,
            'update_date': date,
            'notes': note,
            'update_source': 'BULK_UPDATE',
            'rollback_available': True,
        })
        fw_id += 1
    
    # Then random updates for other generators
    for gen in generators[:35]:
        if gen['id'] not in industrial_gen_ids:
            date = random.choice(update_dates)
            major = random.randint(2, 5)
            minor = random.randint(0, 9)
            patch = random.randint(0, 99)
            version = f"v{major}.{minor}.{patch}"
            note = random.choice(firmware_notes)
            
            meter_firmware.append({
                'id': fw_id,
                'generator_id': gen['id'],
                'firmware_version': version,
                'update_date': date,
                'notes': note,
                'update_source': random.choice(['SCHEDULED', 'MANUAL', 'EMERGENCY']),
                'rollback_available': random.choice([True, False]),
            })
            fw_id += 1
    
    return meter_firmware

# Settlement exceptions - another red herring table
settlement_exceptions = []
def generate_settlement_exceptions():
    exc_id = 1
    
    # These look like they explain overpayments but they're either resolved or don't match the pattern
    exceptions = [
        ('2025-10-07', '2025-10-13', 'NORTH', 'Meter data gap - interpolation required', 'RESOLVED', 0.02),
        ('2025-10-15', '2025-10-21', 'EAST', 'SCADA communication failure', 'RESOLVED', 0.0),
        ('2025-11-01', '2025-11-07', 'SOUTH', 'Hurricane preparation - reduced output', 'RESOLVED', -0.05),
        ('2025-11-10', '2025-11-14', 'CENTRAL', 'Grid frequency deviation event', 'RESOLVED', 0.01),
        ('2025-11-28', '2025-12-04', 'ALL', 'Thanksgiving weekend - demand anomaly', 'RESOLVED', 0.0),
        ('2025-12-20', '2025-12-26', 'ALL', 'Holiday period settlement delay', 'OPEN', 0.0),
        ('2025-12-31', '2026-01-02', 'NORTH', 'Year-end reconciliation adjustment', 'OPEN', 0.03),
    ]
    
    for start, end, zone, desc, status, impact in exceptions:
        settlement_exceptions.append({
            'id': exc_id,
            'exception_start': start,
            'exception_end': end,
            'affected_zone': zone,
            'description': desc,
            'status': status,
            'payment_impact_pct': impact,
            'created_by': f"SYS-{random.randint(1000, 9999)}",
        })
        exc_id += 1
    
    return settlement_exceptions

def write_sql_file():
    with open(os.path.join(DATA_DIR, 'init.sql'), 'w') as f:
        # Nodes table with additional confusing columns
        f.write("CREATE TABLE IF NOT EXISTS nodes (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    name VARCHAR(100) NOT NULL,\n")
        f.write("    zone VARCHAR(20) NOT NULL,\n")
        f.write("    location_type VARCHAR(20) NOT NULL,\n")
        f.write("    congestion_factor DECIMAL(10,4) NOT NULL,\n")
        f.write("    legacy_code VARCHAR(20),\n")  # Ambiguous - looks important but isn't used
        f.write("    grid_region VARCHAR(20)\n")   # Confusing duplicate of zone
        f.write(");\n\n")
        
        # Generators table with additional columns
        f.write("CREATE TABLE IF NOT EXISTS generators (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    name VARCHAR(100) NOT NULL,\n")
        f.write("    generator_type VARCHAR(20) NOT NULL,\n")
        f.write("    capacity_mw DECIMAL(10,2) NOT NULL,\n")
        f.write("    location_id INTEGER REFERENCES nodes(id),\n")
        f.write("    commissioned_date DATE,\n")  # Now nullable for data messiness
        f.write("    is_active BOOLEAN DEFAULT true,\n")
        f.write("    decommissioned_date DATE,\n")
        f.write("    meter_type VARCHAR(20),\n")
        f.write("    original_capacity_mw DECIMAL(10,2),\n")  # Some nulls
        f.write("    last_inspection_date DATE\n")  # Some nulls
        f.write(");\n\n")
        
        # Loss factors with historical tracking
        f.write("CREATE TABLE IF NOT EXISTS loss_factors (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    zone VARCHAR(20) NOT NULL,\n")
        f.write("    energy_threshold DECIMAL(10,2) NOT NULL,\n")
        f.write("    loss_rate DECIMAL(10,6) NOT NULL,\n")
        f.write("    effective_date DATE NOT NULL,\n")
        f.write("    superseded_date DATE,\n")  # For historical records
        f.write("    adjustment_reason TEXT,\n")
        f.write("    approved_by VARCHAR(20)\n")
        f.write(");\n\n")
        
        # Rate tiers with historical tracking
        f.write("CREATE TABLE IF NOT EXISTS rate_tiers (\n")
        f.write("    tier_id SERIAL PRIMARY KEY,\n")
        f.write("    generator_type VARCHAR(20) NOT NULL,\n")
        f.write("    min_capacity_factor DECIMAL(10,4),\n")
        f.write("    location_type VARCHAR(20),\n")
        f.write("    rate_per_mwh DECIMAL(10,2) NOT NULL,\n")
        f.write("    priority_order INTEGER NOT NULL,\n")
        f.write("    effective_date DATE,\n")
        f.write("    superseded_date DATE,\n")  # For historical tiers
        f.write("    tier_code VARCHAR(30)\n")  # Ambiguous identifier
        f.write(");\n\n")
        
        # Rate adjustments table - red herring
        f.write("CREATE TABLE IF NOT EXISTS rate_adjustments (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    location_type VARCHAR(20),\n")
        f.write("    zone VARCHAR(20),\n")
        f.write("    adjustment_multiplier DECIMAL(6,4),\n")
        f.write("    effective_date DATE,\n")
        f.write("    reason TEXT,\n")
        f.write("    status VARCHAR(20),\n")  # APPROVED, PENDING, REJECTED, DRAFT
        f.write("    created_by VARCHAR(20),\n")
        f.write("    approved_by VARCHAR(20)\n")
        f.write(");\n\n")
        
        # Meter readings with quality flags
        f.write("CREATE TABLE IF NOT EXISTS meter_readings (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    generator_id INTEGER,\n")  # No FK constraint - allows orphaned readings
        f.write("    timestamp TIMESTAMP NOT NULL,\n")
        f.write("    energy_mw DECIMAL(12,4) NOT NULL,\n")
        f.write("    interval_minutes INTEGER NOT NULL,\n")
        f.write("    quality_flag VARCHAR(20),\n")  # Data quality indicator
        f.write("    source_system VARCHAR(20)\n")  # Meter type that recorded this
        f.write(");\n\n")
        
        f.write("CREATE TABLE IF NOT EXISTS settlements (\n")
        f.write("    settlement_id SERIAL PRIMARY KEY,\n")
        f.write("    generator_id INTEGER REFERENCES generators(id),\n")
        f.write("    period_start TIMESTAMP NOT NULL,\n")
        f.write("    period_end TIMESTAMP NOT NULL,\n")
        f.write("    energy_mwh DECIMAL(12,4) NOT NULL,\n")
        f.write("    gross_payment DECIMAL(12,2) NOT NULL,\n")
        f.write("    loss_deduction DECIMAL(12,2) NOT NULL,\n")
        f.write("    congestion_credit DECIMAL(12,2) NOT NULL,\n")
        f.write("    net_payment DECIMAL(12,2) NOT NULL,\n")
        f.write("    rate_applied DECIMAL(10,2),\n")
        f.write("    loss_factor_applied DECIMAL(10,6),\n")
        f.write("    capacity_factor DECIMAL(10,4)\n")
        f.write(");\n\n")
        
        # Weather data with additional analysis field
        f.write("CREATE TABLE IF NOT EXISTS weather_data (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    timestamp TIMESTAMP NOT NULL,\n")
        f.write("    zone VARCHAR(20) NOT NULL,\n")
        f.write("    temperature DECIMAL(5,1) NOT NULL,\n")
        f.write("    demand_factor DECIMAL(6,4) NOT NULL,\n")
        f.write("    forecast_accuracy DECIMAL(5,4)\n")  # Additional confusing metric
        f.write(");\n\n")
        
        # Transmission upgrades with more fields
        f.write("CREATE TABLE IF NOT EXISTS transmission_upgrades (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    line_id VARCHAR(20) NOT NULL,\n")
        f.write("    zone VARCHAR(20) NOT NULL,\n")
        f.write("    upgrade_date DATE NOT NULL,\n")
        f.write("    capacity_increase DECIMAL(10,2) NOT NULL,\n")
        f.write("    description TEXT,\n")
        f.write("    status VARCHAR(20),\n")
        f.write("    upgrade_category VARCHAR(30),\n")
        f.write("    affects_loss_factor BOOLEAN,\n")  # Red herring flag
        f.write("    cost_million DECIMAL(10,2)\n")
        f.write(");\n\n")
        
        # Meter firmware with more fields
        f.write("CREATE TABLE IF NOT EXISTS meter_firmware_updates (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    generator_id INTEGER REFERENCES generators(id),\n")
        f.write("    firmware_version VARCHAR(20) NOT NULL,\n")
        f.write("    update_date DATE NOT NULL,\n")
        f.write("    notes TEXT,\n")
        f.write("    update_source VARCHAR(20),\n")
        f.write("    rollback_available BOOLEAN\n")
        f.write(");\n\n")
        
        # Manual adjustments table - red herring
        f.write("CREATE TABLE IF NOT EXISTS manual_adjustments (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    generator_id INTEGER REFERENCES generators(id),\n")
        f.write("    adjustment_date DATE NOT NULL,\n")
        f.write("    adjustment_amount DECIMAL(12,2),\n")
        f.write("    reason TEXT,\n")
        f.write("    status VARCHAR(20),\n")  # VOIDED, REJECTED, PENDING, APPLIED
        f.write("    resolution_note TEXT,\n")
        f.write("    submitted_by VARCHAR(20),\n")
        f.write("    reviewed_by VARCHAR(20)\n")
        f.write(");\n\n")
        
        # Settlement exceptions table - red herring
        f.write("CREATE TABLE IF NOT EXISTS settlement_exceptions (\n")
        f.write("    id SERIAL PRIMARY KEY,\n")
        f.write("    exception_start DATE NOT NULL,\n")
        f.write("    exception_end DATE NOT NULL,\n")
        f.write("    affected_zone VARCHAR(20),\n")
        f.write("    description TEXT,\n")
        f.write("    status VARCHAR(20),\n")
        f.write("    payment_impact_pct DECIMAL(6,4),\n")
        f.write("    created_by VARCHAR(20)\n")
        f.write(");\n\n")
        
        # Indexes
        f.write("CREATE INDEX idx_meter_readings_generator ON meter_readings(generator_id);\n")
        f.write("CREATE INDEX idx_meter_readings_timestamp ON meter_readings(timestamp);\n")
        f.write("CREATE INDEX idx_settlements_generator ON settlements(generator_id);\n")
        f.write("CREATE INDEX idx_settlements_period ON settlements(period_start, period_end);\n")
        f.write("CREATE INDEX idx_weather_zone_time ON weather_data(zone, timestamp);\n")
        f.write("CREATE INDEX idx_loss_factors_zone ON loss_factors(zone, effective_date);\n")
        f.write("CREATE INDEX idx_rate_tiers_type ON rate_tiers(generator_type, priority_order);\n")
        f.write("CREATE INDEX idx_manual_adj_gen ON manual_adjustments(generator_id);\n\n")
        
        # Insert nodes with new columns
        for node in nodes:
            legacy_code = f"'{node['legacy_code']}'" if node['legacy_code'] else 'NULL'
            f.write(f"INSERT INTO nodes (id, name, zone, location_type, congestion_factor, legacy_code, grid_region) VALUES ")
            f.write(f"({node['id']}, '{node['name']}', '{node['zone']}', '{node['location_type']}', {node['congestion_factor']}, {legacy_code}, '{node['grid_region']}');\n")
        f.write("\n")
        
        # Insert generators with new columns
        for gen in generators:
            orig_cap = 'NULL' if gen['original_capacity_mw'] is None else gen['original_capacity_mw']
            last_insp = 'NULL' if gen['last_inspection_date'] is None else f"'{gen['last_inspection_date']}'"
            decom_date = 'NULL' if gen['decommissioned_date'] is None else f"'{gen['decommissioned_date']}'"
            f.write(f"INSERT INTO generators (id, name, generator_type, capacity_mw, location_id, commissioned_date, is_active, decommissioned_date, meter_type, original_capacity_mw, last_inspection_date) VALUES ")
            f.write(f"({gen['id']}, '{gen['name']}', '{gen['generator_type']}', {gen['capacity_mw']}, {gen['location_id']}, '{gen['commissioned_date']}', {str(gen['is_active']).lower()}, {decom_date}, '{gen['meter_type']}', {orig_cap}, {last_insp});\n")
        f.write("\n")
        
        # Insert loss factors with new columns
        for lf in loss_factors:
            superseded = 'NULL' if lf['superseded_date'] is None else f"'{lf['superseded_date']}'"
            reason = 'NULL' if lf['adjustment_reason'] is None else f"'{lf['adjustment_reason']}'"
            f.write(f"INSERT INTO loss_factors (id, zone, energy_threshold, loss_rate, effective_date, superseded_date, adjustment_reason, approved_by) VALUES ")
            f.write(f"({lf['id']}, '{lf['zone']}', {lf['energy_threshold']}, {lf['loss_rate']}, '{lf['effective_date']}', {superseded}, {reason}, '{lf['approved_by']}');\n")
        f.write("\n")
        
        # Insert rate tiers with new columns
        for rt in rate_tiers:
            min_cf = 'NULL' if rt['min_capacity_factor'] is None else rt['min_capacity_factor']
            loc_type = 'NULL' if rt['location_type'] is None else f"'{rt['location_type']}'"
            eff_date = f"'{rt['effective_date']}'" if rt['effective_date'] else 'NULL'
            superseded = 'NULL' if rt['superseded_date'] is None else f"'{rt['superseded_date']}'"
            f.write(f"INSERT INTO rate_tiers (tier_id, generator_type, min_capacity_factor, location_type, rate_per_mwh, priority_order, effective_date, superseded_date, tier_code) VALUES ")
            f.write(f"({rt['tier_id']}, '{rt['generator_type']}', {min_cf}, {loc_type}, {rt['rate_per_mwh']}, {rt['priority_order']}, {eff_date}, {superseded}, '{rt['tier_code']}');\n")
        f.write("\n")
        
        # Insert rate adjustments
        for ra in rate_adjustments:
            approved = 'NULL' if ra['approved_by'] is None else f"'{ra['approved_by']}'"
            f.write(f"INSERT INTO rate_adjustments (id, location_type, zone, adjustment_multiplier, effective_date, reason, status, created_by, approved_by) VALUES ")
            f.write(f"({ra['id']}, '{ra['location_type']}', '{ra['zone']}', {ra['adjustment_multiplier']}, '{ra['effective_date']}', '{ra['reason']}', '{ra['status']}', '{ra['created_by']}', {approved});\n")
        f.write("\n")
        
        # Use COPY for meter readings (CSV)
        f.write("\\copy meter_readings (id, generator_id, timestamp, energy_mw, interval_minutes, quality_flag, source_system) FROM '/docker-entrypoint-initdb.d/meter_readings.csv' WITH CSV HEADER NULL AS 'NULL';\n\n")
        
        # Insert weather data (first 5000 to keep file manageable)
        for wd in weather_data[:5000]:
            forecast_acc = round(random.uniform(0.85, 0.99), 4)  # Add forecast accuracy
            f.write(f"INSERT INTO weather_data (id, timestamp, zone, temperature, demand_factor, forecast_accuracy) VALUES ")
            f.write(f"({wd['id']}, '{wd['timestamp']}', '{wd['zone']}', {wd['temperature']}, {wd['demand_factor']}, {forecast_acc});\n")
        f.write("\n")
        
        # Insert transmission upgrades with new columns
        for tu in transmission_upgrades:
            affects_lf = 'true' if tu['affects_loss_factor'] else 'false'
            f.write(f"INSERT INTO transmission_upgrades (id, line_id, zone, upgrade_date, capacity_increase, description, status, upgrade_category, affects_loss_factor, cost_million) VALUES ")
            desc_escaped = tu['description'].replace("'", "''")
            f.write(f"({tu['id']}, '{tu['line_id']}', '{tu['zone']}', '{tu['upgrade_date']}', {tu['capacity_increase']}, '{desc_escaped}', '{tu['status']}', '{tu['upgrade_category']}', {affects_lf}, {tu['cost_million']});\n")
        f.write("\n")
        
        # Insert meter firmware with new columns
        for mf in meter_firmware:
            rollback = 'true' if mf['rollback_available'] else 'false'
            notes_escaped = mf['notes'].replace("'", "''")
            f.write(f"INSERT INTO meter_firmware_updates (id, generator_id, firmware_version, update_date, notes, update_source, rollback_available) VALUES ")
            f.write(f"({mf['id']}, {mf['generator_id']}, '{mf['firmware_version']}', '{mf['update_date']}', '{notes_escaped}', '{mf['update_source']}', {rollback});\n")
        f.write("\n")
        
        # Insert manual adjustments
        for ma in manual_adjustments:
            reviewed = 'NULL' if ma['reviewed_by'] is None else f"'{ma['reviewed_by']}'"
            reason_escaped = ma['reason'].replace("'", "''")
            resolution_escaped = ma['resolution_note'].replace("'", "''")
            f.write(f"INSERT INTO manual_adjustments (id, generator_id, adjustment_date, adjustment_amount, reason, status, resolution_note, submitted_by, reviewed_by) VALUES ")
            f.write(f"({ma['id']}, {ma['generator_id']}, '{ma['adjustment_date']}', {ma['adjustment_amount']}, '{reason_escaped}', '{ma['status']}', '{resolution_escaped}', '{ma['submitted_by']}', {reviewed});\n")
        f.write("\n")
        
        # Insert settlement exceptions
        for se in settlement_exceptions:
            desc_escaped = se['description'].replace("'", "''")
            f.write(f"INSERT INTO settlement_exceptions (id, exception_start, exception_end, affected_zone, description, status, payment_impact_pct, created_by) VALUES ")
            f.write(f"({se['id']}, '{se['exception_start']}', '{se['exception_end']}', '{se['affected_zone']}', '{desc_escaped}', '{se['status']}', {se['payment_impact_pct']}, '{se['created_by']}');\n")
        f.write("\n")
        
        # Sequence updates
        f.write("SELECT setval('nodes_id_seq', (SELECT MAX(id) FROM nodes));\n")
        f.write("SELECT setval('generators_id_seq', (SELECT MAX(id) FROM generators));\n")
        f.write("SELECT setval('loss_factors_id_seq', (SELECT MAX(id) FROM loss_factors));\n")
        f.write("SELECT setval('rate_tiers_tier_id_seq', (SELECT MAX(tier_id) FROM rate_tiers));\n")
        f.write("SELECT setval('meter_readings_id_seq', (SELECT MAX(id) FROM meter_readings));\n")
        f.write("SELECT setval('weather_data_id_seq', (SELECT MAX(id) FROM weather_data));\n")
        f.write("SELECT setval('transmission_upgrades_id_seq', (SELECT MAX(id) FROM transmission_upgrades));\n")
        f.write("SELECT setval('meter_firmware_updates_id_seq', (SELECT MAX(id) FROM meter_firmware_updates));\n")
        f.write("SELECT setval('manual_adjustments_id_seq', (SELECT MAX(id) FROM manual_adjustments));\n")
        f.write("SELECT setval('settlement_exceptions_id_seq', (SELECT MAX(id) FROM settlement_exceptions));\n")
        f.write("SELECT setval('rate_adjustments_id_seq', (SELECT MAX(id) FROM rate_adjustments));\n")

def write_meter_readings_csv():
    with open(os.path.join(DATA_DIR, 'meter_readings.csv'), 'w') as f:
        f.write("id,generator_id,timestamp,energy_mw,interval_minutes,quality_flag,source_system\n")
        for mr in meter_readings:
            quality = mr['quality_flag'] if mr['quality_flag'] else 'NULL'
            f.write(f"{mr['id']},{mr['generator_id']},{mr['timestamp']},{mr['energy_mw']},{mr['interval_minutes']},{quality},{mr['source_system']}\n")

def main():
    print("Generating nodes...")
    generate_nodes()
    
    print("Generating generators...")
    generate_generators()
    
    print("Generating loss factors...")
    generate_loss_factors()
    
    print("Generating rate adjustments...")
    generate_rate_adjustments()
    
    print("Generating rate tiers...")
    generate_rate_tiers()
    
    print("Generating meter readings...")
    generate_meter_readings()
    
    print("Generating weather data...")
    generate_weather_data()
    
    print("Generating transmission upgrades...")
    generate_transmission_upgrades()
    
    print("Generating manual adjustments...")
    generate_manual_adjustments()
    
    print("Generating meter firmware updates...")
    generate_meter_firmware()
    
    print("Generating settlement exceptions...")
    generate_settlement_exceptions()
    
    print("Writing SQL file...")
    write_sql_file()
    
    print("Writing meter readings CSV...")
    write_meter_readings_csv()
    
    print(f"Generated {len(nodes)} nodes")
    print(f"Generated {len(generators)} generators (+ {len(decommissioned_gens)} decommissioned)")
    print(f"Generated {len(loss_factors)} loss factors")
    print(f"Generated {len(rate_adjustments)} rate adjustments")
    print(f"Generated {len(rate_tiers)} rate tiers")
    print(f"Generated {len(meter_readings)} meter readings")
    print(f"Generated {len(weather_data)} weather records")
    print(f"Generated {len(transmission_upgrades)} transmission upgrades")
    print(f"Generated {len(manual_adjustments)} manual adjustments")
    print(f"Generated {len(meter_firmware)} firmware updates")
    print(f"Generated {len(settlement_exceptions)} settlement exceptions")
    print("Data generation complete!")

if __name__ == '__main__':
    main()
