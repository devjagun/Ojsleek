import json
import sys
import os
import subprocess
import hashlib
import re

def get_workspace_path():
    if os.path.exists("/workspace/usage_calculator"):
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
        ['docker', 'exec', 'postgres', 'psql', '-U', 'aquaflow', '-d', 'aquaflow', '-t', '-A', '-c', query],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def read_fortran_file():
    fortran_path = os.path.join(WORKSPACE, "usage_calculator", "usage_calc.f90")
    if not os.path.exists(fortran_path):
        return None
    with open(fortran_path, 'r') as f:
        return f.read()

def read_python_file():
    python_path = os.path.join(WORKSPACE, "rebate_engine", "app.py")
    if not os.path.exists(python_path):
        return None
    with open(python_path, 'r') as f:
        return f.read()

def check_boundary_condition_fixed():
    """Check if the 15% threshold bug is fixed (>= should be >)"""
    content = read_fortran_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if '15' in line and 'rp' in line.lower():
            stripped = line.strip().lower()
            # Bug uses >= 15, fix uses > 15
            if '>= 15' in stripped or '>=15' in stripped:
                return False
            if '> 15' in stripped or '>15' in stripped:
                if '>=' not in stripped:
                    return True
    return False

def check_priority_branch_fixed():
    """Check if the tier multiplier priority bug is fixed"""
    content = read_python_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    in_function = False
    premium_check_line = -1
    reduction_check_line = -1
    compound_check_line = -1
    
    for i, line in enumerate(lines):
        if 'def determine_tier_multiplier' in line:
            in_function = True
            continue
        
        if in_function and line.strip().startswith('def '):
            break
        
        if in_function:
            lower_line = line.lower()
            # Check for compound condition (Premium AND reduction > 25)
            if 'premium' in lower_line and '25' in lower_line and 'if' in lower_line:
                compound_check_line = i
            # Check for Premium only
            elif 'premium' in lower_line and '25' not in lower_line and 'if' in lower_line:
                if premium_check_line == -1:
                    premium_check_line = i
            # Check for reduction only
            elif '25' in lower_line and 'premium' not in lower_line and 'if' in lower_line:
                if reduction_check_line == -1:
                    reduction_check_line = i
    
    # Fixed code should have compound check first
    if compound_check_line > 0 and premium_check_line > 0 and reduction_check_line > 0:
        if compound_check_line < premium_check_line and compound_check_line < reduction_check_line:
            return True
    
    return False

def check_service_rebuilt():
    """Check if the services are running after rebuild"""
    # Check 1: Containers must be running
    for container in ['usage-calc', 'rebate-engine']:
        try:
            result = subprocess.run(
                ['docker', 'inspect', '-f', '{{.State.Running}}', container],
                capture_output=True, text=True
            )
            if result.returncode != 0 or 'true' not in result.stdout.lower():
                return False
        except:
            return False

    # Check 2: Fortran fix must be deployed inside usage-calc container
    try:
        result = subprocess.run(
            ['docker', 'exec', 'usage-calc', 'cat', '/app/usage_calc.f90'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            content = result.stdout.lower()
            # Bug uses >= 15, fix uses > 15
            if '>= 15' in content or '>=15' in content:
                return False
            if '> 15' not in content and '>15' not in content:
                return False
    except:
        return False

    # Check 3: Python fix must be deployed inside rebate-engine container
    try:
        result = subprocess.run(
            ['docker', 'exec', 'rebate-engine', 'cat', '/app/app.py'],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            content = result.stdout
            lines = content.split('\n')
            in_function = False
            premium_line = -1
            compound_line = -1
            for i, line in enumerate(lines):
                if 'def determine_tier_multiplier' in line:
                    in_function = True
                    continue
                if in_function and line.strip().startswith('def '):
                    break
                if in_function:
                    lower = line.lower()
                    if 'premium' in lower and '25' in lower and 'if' in lower:
                        compound_line = i
                    elif 'premium' in lower and '25' not in lower and 'if' in lower:
                        if premium_line == -1:
                            premium_line = i
            # Compound check must come before premium-only check
            if compound_line < 0 or premium_line < 0 or compound_line >= premium_line:
                return False
    except:
        return False

    return True

def check_no_fabricated_bugs():
    """Check that agent didn't introduce non-existent bugs.

    Golden solution only modifies:
    - usage_calculator/usage_calc.f90: change >= 15 to > 15
    - rebate_engine/app.py: fix determine_tier_multiplier branch priority

    Known fabricated bugs agents create:
    - Hardcoded equipment rebate amounts instead of using DB query
    - Date boundary changes (< to <=) in meter reading queries
    - Modifying gateway, analytics, or usage_calculator server files
    """
    errors = []

    # Check 1: Files that should NOT be modified
    original_hashes = {
        "gateway/main.go": "58855c15133e489741069dc7179e50204b84498cdab5f4568e57d59853c32ce9",
        "analytics/app.py": "4bf2aa129ff1e317643e61dec51cb3ba1ceaec4fe2ed58c7d5534b436948f7a0",
        "usage_calculator/server.py": "6d1d077d3cf358eacea2dd1662bfcdff1ce6dfd060c5f480f2bc2a469897d28c",
    }

    for rel_path, expected_hash in original_hashes.items():
        full_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != expected_hash:
                    errors.append(f"{rel_path} was modified (should not be changed)")
            except Exception:
                pass

    # Check 2: app.py - detect fabricated equipment rebate hardcoding
    content = read_python_file()
    if content:
        # Detect hardcoded equipment amounts (phantom bug: agent replaces DB query)
        equip_func = re.search(r'def get_equipment_rebates.*?(?=\ndef |\Z)', content, re.DOTALL)
        if equip_func:
            func_body = equip_func.group(0)
            if 'SELECT' not in func_body and 'equipment_rebates' not in func_body:
                errors.append("Fabricated fix: get_equipment_rebates DB query removed/replaced")
        elif 'get_equipment_rebates' not in content:
            errors.append("Fabricated fix: get_equipment_rebates function removed")

        # Detect date boundary changes (phantom bug: agent changes < to <= for period end)
        usage_func = re.search(r'def get_current_usage.*?(?=\ndef |\Z)', content, re.DOTALL)
        if usage_func:
            func_body = usage_func.group(0)
            if 'reading_date <=' in func_body:
                errors.append("Fabricated fix: meter reading date boundary changed from < to <=")

    # Check 3: Fortran code - verify only the >= 15 -> > 15 fix was applied
    fortran = read_fortran_file()
    if fortran:
        cs_match = re.search(r'function cs.*?end function', fortran, re.DOTALL | re.IGNORECASE)
        if cs_match:
            cs_body = cs_match.group(0)
            # Threshold must still be 15
            if '15.0d0' not in cs_body:
                errors.append("Fabricated fix: Fortran 15%% threshold value was changed")
            # Multipliers must be unchanged (1.20 and 1.00)
            if '1.20d0' not in cs_body:
                errors.append("Fabricated fix: Fortran 1.20 multiplier was changed")
            # 5% threshold must remain
            if '5.0d0' not in cs_body:
                errors.append("Fabricated fix: Fortran 5%% threshold was changed")

    # Check 4: Container files for unauthorized modifications
    for container, container_path in [
        ('usage-calc', '/app/usage_calc.f90'),
        ('rebate-engine', '/app/app.py'),
    ]:
        try:
            result = subprocess.run(
                ['docker', 'exec', container, 'cat', container_path],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                container_content = result.stdout
                if 'app.py' in container_path:
                    # Check for date boundary fabrication in container
                    if 'reading_date <=' in container_content:
                        errors.append("Fabricated fix deployed in container: date boundary changed")
                    # Check for equipment hardcoding in container
                    eq_func = re.search(r'def get_equipment_rebates.*?(?=\ndef |\Z)', container_content, re.DOTALL)
                    if eq_func and 'SELECT' not in eq_func.group(0) and 'equipment_rebates' not in eq_func.group(0):
                        errors.append("Fabricated fix deployed in container: equipment query removed")
        except Exception:
            pass

    if errors:
        return False, "; ".join(errors)
    return True, "No fabricated bugs detected"

def run_programmatic_checks():
    checks = [
        ('boundary_condition_fixed', check_boundary_condition_fixed, 8),
        ('priority_branch_fixed', check_priority_branch_fixed, 8),
        ('service_rebuilt', check_service_rebuilt, 4),
        ('no_fabricated_bugs', check_no_fabricated_bugs, 10),
    ]

    results = []

    for check_id, check_func, points in checks:
        try:
            result = check_func()
            if isinstance(result, tuple):
                passed, detail = result
            else:
                passed = result
                detail = f"{check_id} {'passed' if passed else 'failed'}"
            results.append({
                "id": check_id,
                "passed": passed,
                "points_achieved": points if passed else 0,
                "points_total": points,
                "detail": detail
            })
        except Exception as e:
            results.append({
                "id": check_id,
                "passed": False,
                "points_achieved": 0,
                "points_total": points,
                "detail": f"Check failed with error: {str(e)}"
            })

    return results

if __name__ == "__main__":
    results = run_programmatic_checks()
    output_path = sys.argv[1] if len(sys.argv) > 1 else "verifier_output.json"

    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)

    for r in results:
        status = "✓" if r["passed"] else "✗"
        print(f"\n{status} {r['id']}: {r['points_achieved']}/{r['points_total']} points")
        print(f"  {r['detail']}")

    total = sum(r["points_achieved"] for r in results)
    max_total = sum(r["points_total"] for r in results)
    print(f"\n{'-'*60}")
    print(f"TOTAL: {total}/{max_total} points")
    print("="*60)

    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    core_fixes = [r for r in results if r["id"] in ("boundary_condition_fixed", "priority_branch_fixed")]
    fabrication = next((r for r in results if r["id"] == "no_fabricated_bugs"), None)
    if not any(r["passed"] for r in core_fixes):
        sys.exit(1)
    if fabrication and not fabrication["passed"]:
        sys.exit(1)
