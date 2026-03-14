import json
import sys
import os
import subprocess
import hashlib

def get_workspace_path():
    if os.path.exists("/workspace/bonus_engine"):
        return "/workspace"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), "environment")

WORKSPACE = get_workspace_path()

def load_rubric():
    rubric_path = os.path.join(os.path.dirname(__file__), "rubric.json")
    with open(rubric_path) as f:
        return json.load(f)

def run_psql_query(query):
    result = subprocess.run(
        ['docker', 'exec', 'postgres', 'psql', '-U', 'surehaul', '-d', 'surehaul', '-t', '-A', '-c', query],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def read_fortran_file():
    fortran_path = os.path.join(WORKSPACE, "bonus_engine", "bonus_calc.f90")
    if not os.path.exists(fortran_path):
        return None
    with open(fortran_path, 'r') as f:
        return f.read()

def check_boundary_condition_fixed():
    content = read_fortran_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'zd' in line.lower() and '30' in line:
            stripped = line.strip().lower()
            if '>= 30' in stripped or '>=30' in stripped:
                return False
            if '> 30' in stripped or '>30' in stripped:
                if '>=' not in stripped:
                    return True
    return False

def check_priority_branch_fixed():
    content = read_fortran_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    in_gr_function = False
    gold_score_check_line = -1
    score_only_check_line = -1
    gold_only_check_line = -1
    
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        if 'function gr' in lower_line:
            in_gr_function = True
            continue
        
        if in_gr_function and 'end function' in lower_line:
            break
        
        if in_gr_function:
            if 'gold' in lower_line and '150' in lower_line and 'if' in lower_line:
                gold_score_check_line = i
            elif '150' in lower_line and 'gold' not in lower_line and 'if' in lower_line:
                score_only_check_line = i
            elif 'gold' in lower_line and '150' not in lower_line and 'if' in lower_line:
                gold_only_check_line = i
    
    if gold_score_check_line > 0 and score_only_check_line > 0 and gold_only_check_line > 0:
        if gold_score_check_line < gold_only_check_line < score_only_check_line:
            return True
        if gold_score_check_line < score_only_check_line and gold_score_check_line < gold_only_check_line:
            return True
    
    return False

def check_service_rebuilt():
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', 'bonus-calc'],
            capture_output=True,
            text=True,
            cwd=WORKSPACE
        )
        return 'running' in result.stdout.lower() or 'up' in result.stdout.lower()
    except:
        return False

def check_no_fabricated_bugs():
    """Check that agent didn't introduce non-existent bugs."""
    content = read_fortran_file()
    if content is None:
        return True, "Could not read Fortran file"
    
    errors = []
    lines = content.split('\n')
    
    # Check rating condition: ar > 4.2 → 0.92 is CORRECT, should not be inverted
    for i, line in enumerate(lines):
        lower_line = line.lower().strip()
        # Check for inverted rating condition (ar < 4.2 or ar <= 4.2)
        if ('ar' in lower_line or 'rating' in lower_line) and '4.2' in lower_line:
            if '< 4.2' in lower_line or '<4.2' in lower_line or '<= 4.2' in lower_line or '<=4.2' in lower_line:
                if i+1 < len(lines) and '0.92' in lines[i+1]:
                    errors.append("Rating condition inverted (< 4.2 gets 0.92 is wrong)")
    
    # Check BPI deficit multiplier: 0.85 must be present in the cb function (not changed to 1.15)
    # The cb function calculates BPI and should have 0.85d0 for deficit (x < 0) case
    in_cb_function = False
    found_deficit_multiplier = False
    for line in lines:
        lower_line = line.lower().strip()
        if 'function cb' in lower_line:
            in_cb_function = True
        elif in_cb_function and 'end function' in lower_line:
            in_cb_function = False
        elif in_cb_function:
            # Check if the deficit multiplier 0.85 is present
            if '0.85d0' in line:
                found_deficit_multiplier = True
    
    if not found_deficit_multiplier and '0.85d0' not in content:
        errors.append("BPI deficit multiplier changed from 0.85 (should not be modified)")
    
    # Check familiarity condition: should be > 30, not < 30 (inversion)
    for line in lines:
        lower_line = line.lower().strip()
        if ('zd' in lower_line or 'zone_days' in lower_line) and '30' in lower_line:
            if ('< 30' in lower_line or '<30' in lower_line) and '>=' not in lower_line:
                errors.append("Familiarity condition inverted to < 30 (should be > 30)")
    
    # Check for app.py modifications - golden solution ONLY modifies bonus_calc.f90
    # Any changes to app.py indicate fabricated bug fixes
    app_py_modified = check_app_py_modified()
    if app_py_modified:
        errors.append(f"app.py was modified - golden solution only modifies Fortran code ({app_py_modified})")
    
    if errors:
        return False, "; ".join(errors)
    return True, "No fabricated bugs detected"


def check_app_py_modified():
    """Check if any app.py files were modified from their original state.
    
    Golden solution only modifies bonus_calc.f90. Any changes to app.py
    indicate fabricated bug fixes (e.g., SQL query changes, tenure calculation
    changes, zone filter removal, GROUP BY additions for non-existent duplicates).
    """
    # Original checksums of app.py files (computed from clean state)
    original_hashes = {
        "bonus_engine/app.py": "729d0be8f85561b71c541cd4d3135b2d7cd0ee428a45a073776dbd0db34567ae",
        "analytics/app.py": "e61baa098352cb9daf5550323a8dce4b0a04eebc05664dc3b25de61645ed7ef2"
    }
    
    modified_files = []
    
    for rel_path, expected_hash in original_hashes.items():
        full_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != expected_hash:
                    modified_files.append(rel_path)
            except Exception:
                pass  # If can't read, assume not modified
    
    if modified_files:
        return ", ".join(modified_files)
    return None


def check_container_matches_workspace():
    """Verify container code matches workspace changes."""
    try:
        # Read Fortran from container
        result = subprocess.run(
            ['docker', 'exec', 'bonus-calc', 'cat', '/app/bonus_calc.f90'],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, "Could not read container Fortran code"
        container_code = result.stdout
        
        # Read Fortran from workspace
        workspace_code = read_fortran_file()
        if workspace_code is None:
            return False, "Could not read workspace Fortran code"
        
        # Normalize and compare key sections
        container_has_fixed_boundary = '> 30' in container_code and '>= 30' not in container_code.replace('> 30', '')
        workspace_has_fixed_boundary = '> 30' in workspace_code and '>= 30' not in workspace_code.replace('> 30', '')
        
        if workspace_has_fixed_boundary and not container_has_fixed_boundary:
            return False, "Container not rebuilt: boundary fix not deployed"
        
        return True, "Container matches workspace"
    except Exception as e:
        return False, f"Container check failed: {str(e)}"


def check_calculation_correct():
    """Test actual calculations with known inputs."""
    try:
        # Test 1: Call service directly with Fortran binary
        # Input format: driver_id n t bd ar zd tr ty
        # Test case: driver with exactly 30 zone days - should NOT get familiarity factor (after fix)
        test_input = "1 32 30 1.0 4.5 30 Silver 1"
        
        result = subprocess.run(
            ['docker', 'exec', '-i', 'bonus-calc', '/app/bonus_calc'],
            input=test_input,
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Try via API as fallback
            api_result = subprocess.run(
                ['curl', '-sf', 'http://localhost:9000/health'],
                capture_output=True,
                text=True
            )
            if api_result.returncode != 0:
                return False, "Bonus-calc service not responding"
            return False, "Could not run Fortran binary directly"
        
        output = result.stdout.strip()
        if not output:
            return False, "Empty output from calculation"
        
        parts = output.split()
        if len(parts) < 6:
            return False, f"Unexpected output format: {output}"
        
        # Parse output: driver_id, p(BPI), z(zone_factor), s(score), r(rate), f(final)
        try:
            zone_factor = float(parts[2])
            
            # With fixed boundary (> 30): 30 days should NOT trigger 0.88
            # Expected zone_factor ≈ 1.0 * 0.92 (rating) * 1.0 (no familiarity) = 0.92
            # With buggy code (>= 30): zone_factor ≈ 1.0 * 0.92 * 0.88 = 0.8096
            
            # Check if familiarity factor was NOT applied (value should be > 0.85)
            if zone_factor < 0.85:
                return False, f"Boundary bug still present: zone_factor={zone_factor} (expected ~0.92 for 30 days)"
            
        except (ValueError, IndexError) as e:
            return False, f"Could not parse calculation output: {str(e)}"
        
        # Test 2: Gold tier with score > 150 - should get rate 1.25 (after fix)
        test_input2 = "2 35 30 1.0 4.0 45 Gold 3"  # Gold, score will be >150
        result2 = subprocess.run(
            ['docker', 'exec', '-i', 'bonus-calc', '/app/bonus_calc'],
            input=test_input2,
            capture_output=True,
            text=True
        )
        
        if result2.returncode == 0:
            output2 = result2.stdout.strip()
            parts2 = output2.split()
            if len(parts2) >= 5:
                try:
                    rate = float(parts2[4])
                    score = float(parts2[3])
                    
                    # If Gold tier and score > 150, rate should be 1.25
                    if score > 150 and abs(rate - 1.10) < 0.01:
                        return False, f"Priority bug still present: Gold+score>{score} got rate={rate} (expected 1.25)"
                except (ValueError, IndexError):
                    pass  # Non-critical
        
        return True, "Calculations match expected values"
        
    except Exception as e:
        return False, f"Calculation check failed: {str(e)}"

def run_programmatic_checks():
    rubric = load_rubric()
    checks_def = {c["id"]: c["points"] for c in rubric["programmatic_checks"]}
    results = []
    
    boundary_fixed = check_boundary_condition_fixed()
    results.append({
        "id": "boundary_condition_fixed",
        "passed": boundary_fixed,
        "points_achieved": checks_def.get("boundary_condition_fixed", 8) if boundary_fixed else 0,
        "points_total": checks_def.get("boundary_condition_fixed", 8),
        "detail": "Familiarity condition fixed to > 30" if boundary_fixed else "Familiarity condition still uses >= 30"
    })
    
    priority_fixed = check_priority_branch_fixed()
    results.append({
        "id": "priority_branch_fixed",
        "passed": priority_fixed,
        "points_achieved": checks_def.get("priority_branch_fixed", 8) if priority_fixed else 0,
        "points_total": checks_def.get("priority_branch_fixed", 8),
        "detail": "Tier rate priority order corrected" if priority_fixed else "Tier rate priority order still incorrect"
    })
    
    rebuilt = check_service_rebuilt()
    results.append({
        "id": "service_rebuilt",
        "passed": rebuilt,
        "points_achieved": checks_def.get("service_rebuilt", 4) if rebuilt else 0,
        "points_total": checks_def.get("service_rebuilt", 4),
        "detail": "bonus-calc service is running" if rebuilt else "bonus-calc service not running"
    })
    
    # Check for fabricated bugs (agent introducing non-existent bugs)
    no_fabricated, fabricated_detail = check_no_fabricated_bugs()
    results.append({
        "id": "no_fabricated_bugs",
        "passed": no_fabricated,
        "points_achieved": checks_def.get("no_fabricated_bugs", 0) if no_fabricated else -checks_def.get("no_fabricated_bugs", 10),
        "points_total": checks_def.get("no_fabricated_bugs", 0),
        "detail": fabricated_detail
    })
    
    # Check container matches workspace (code was actually deployed)
    container_matches, container_detail = check_container_matches_workspace()
    results.append({
        "id": "container_matches_workspace",
        "passed": container_matches,
        "points_achieved": checks_def.get("container_matches_workspace", 5) if container_matches else 0,
        "points_total": checks_def.get("container_matches_workspace", 5),
        "detail": container_detail
    })
    
    # Actual calculation verification
    calc_passed, calc_detail = check_calculation_correct()
    results.append({
        "id": "calculation_correct",
        "passed": calc_passed,
        "points_achieved": checks_def.get("calculation_correct", 5) if calc_passed else 0,
        "points_total": checks_def.get("calculation_correct", 5),
        "detail": calc_detail
    })
    
    return results

if __name__ == "__main__":
    results = run_programmatic_checks()
    output_path = sys.argv[1] if len(sys.argv) > 1 else "verifier_output.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    if not all(r["passed"] for r in results):
        sys.exit(1)
