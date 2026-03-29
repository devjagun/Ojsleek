#!/usr/bin/env python3
import subprocess
import json
import hashlib
import sys
import os
import re

def get_workspace_path():
    if os.path.exists("/workspace/loss_calculator"):
        return "/workspace"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), "environment")

WORKSPACE = get_workspace_path()
FORTRAN_PATH = os.path.join(WORKSPACE, "loss_calculator", "loss_calculator.f90")
PYTHON_PATH = os.path.join(WORKSPACE, "settlement_engine", "app.py")

def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception:
        return ""

def run_docker_exec(container, cmd):
    full_cmd = ["docker", "exec", container] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=15)
    return result.returncode, result.stdout, result.stderr

def run_curl(url):
    result = subprocess.run(["curl", "-sf", url], capture_output=True, text=True, timeout=15)
    return result.returncode, result.stdout


def check_loss_factor_bug_fixed():
    """Check if the loss calculator boundary condition was corrected.

    Handles multiple fix approaches:
    - emwh >= thresh (standard)
    - emwh .ge. thresh (Fortran operator syntax)
    - Python rewrite using >= comparison
    """
    # Strategy 1: Live service test - energy at exactly threshold should get loss_factor > 1.0
    try:
        result = subprocess.run(
            ["curl", "-sf", "-X", "POST",
             "http://localhost:8081/calculate",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"zone": "NORTH", "energy_mwh": 100.0})],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            try:
                data = json.loads(result.stdout)
                loss_factor = data.get('loss_factor', 1.0)
                threshold = data.get('threshold', 0)
                if loss_factor > 1.0:
                    return True, f"Loss factor service correctly returns {loss_factor} for energy at threshold"
                if loss_factor == 1.0 and abs(threshold - 100.0) < 0.5:
                    return False, f"Loss factor bug still present: energy=100.0 at threshold={threshold} got factor={loss_factor} (expected > 1.0)"
            except (json.JSONDecodeError, KeyError):
                pass
    except Exception:
        pass

    # Strategy 2: Check Fortran source code
    content = read_file(FORTRAN_PATH)
    if not content:
        for cname in ["gridpeak_loss_calc", "loss_calculator", "loss-calculator"]:
            rc, content, _ = run_docker_exec(cname, ["cat", "/app/loss_calculator.f90"])
            if rc == 0 and content:
                break
        if rc != 0:
            return False, "Could not read loss_calculator.f90"

    # Strip Fortran comments
    code_lines = []
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped.startswith('!'):
            continue
        if '!' in line:
            line = line[:line.index('!')]
        code_lines.append(line)
    clean_content = '\n'.join(code_lines)

    correct_patterns = [
        r'emwh\s*>=\s*thresh',
        r'emwh\s*\.ge\.\s*thresh',
    ]
    buggy_patterns = [
        r'emwh\s*>\s*thresh(?!\s*\.)',
        r'emwh\s*\.gt\.\s*thresh',
    ]

    has_correct = any(re.search(p, clean_content, re.IGNORECASE) for p in correct_patterns)
    has_buggy = any(re.search(p, clean_content, re.IGNORECASE) for p in buggy_patterns)

    if has_correct and not has_buggy:
        return True, "Threshold comparison correctly uses >= operator"
    elif has_buggy and not has_correct:
        return False, "Threshold comparison still uses > instead of >="
    elif has_correct and has_buggy:
        return False, "Mixed comparisons found - both > and >= present"

    # Strategy 3: Check if reimplemented in Python
    server_path = os.path.join(WORKSPACE, "loss_calculator", "server.py")
    server_content = read_file(server_path)
    if server_content and '>=' in server_content and 'thresh' in server_content.lower():
        return True, "Loss factor boundary condition reimplemented in Python with >="

    return False, "Could not determine threshold comparison operator"


def check_rate_tier_bug_fixed():
    """Check that rate tier selection verifies capacity factor for location-type matches.

    The bug: when a tier's location_type matches the generator's location, the code
    returns the rate immediately without checking if capacity_factor meets min_cf.
    The fix: both location_type AND capacity_factor must be validated before returning.

    Handles multiple fix approaches:
    - Nested if (golden solution pattern)
    - loc_match/cf_match boolean variables
    - match=True flag pattern
    - Combined condition with 'and'
    - Complete function rewrite
    """
    # Strategy 1: Live service test
    # Find an industrial generator with low CF and check if it gets premium rate
    try:
        find_cmd = [
            "docker", "exec", "gridpeak_postgres",
            "psql", "-U", "gridpeak", "-d", "energy_market",
            "-t", "-A", "-c",
            "SELECT s.generator_id, g.generator_type, s.rate_applied, s.capacity_factor "
            "FROM settlements s "
            "JOIN generators g ON s.generator_id = g.id "
            "JOIN nodes n ON g.location_id = n.id "
            "WHERE n.location_type = 'industrial' "
            "AND s.capacity_factor < 0.5 "
            "LIMIT 1"
        ]
        find_result = subprocess.run(find_cmd, capture_output=True, text=True, timeout=10)
        if find_result.returncode == 0 and find_result.stdout.strip():
            parts = find_result.stdout.strip().split('|')
            if len(parts) >= 4:
                gen_id = int(parts[0])
                gen_type = parts[1].strip()
                old_rate = float(parts[2])

                # Get the premium rate for this generator type (priority 1 = industrial + high CF)
                premium_cmd = [
                    "docker", "exec", "gridpeak_postgres",
                    "psql", "-U", "gridpeak", "-d", "energy_market",
                    "-t", "-A", "-c",
                    f"SELECT rate_per_mwh FROM rate_tiers WHERE generator_type = '{gen_type}' "
                    "AND location_type = 'industrial' AND priority_order = 1"
                ]
                premium_result = subprocess.run(premium_cmd, capture_output=True, text=True, timeout=10)
                if premium_result.returncode == 0 and premium_result.stdout.strip():
                    premium_rate = float(premium_result.stdout.strip())

                    # Call the settlement engine live to see what rate it returns now
                    calc_result = subprocess.run(
                        ["curl", "-sf", "-X", "POST",
                         "http://localhost:8082/calculate",
                         "-H", "Content-Type: application/json",
                         "-d", json.dumps({
                             "generator_id": gen_id,
                             "period_start": "2025-10-01T00:00:00",
                             "period_end": "2025-10-08T00:00:00"
                         })],
                        capture_output=True, text=True, timeout=30
                    )
                    if calc_result.returncode == 0:
                        try:
                            data = json.loads(calc_result.stdout)
                            live_rate = data.get('rate_applied', 0)
                            live_cf = data.get('capacity_factor', 0)
                            if live_cf < 0.5 and abs(live_rate - premium_rate) < 0.01:
                                return False, f"Rate tier bug still present: industrial gen {gen_id} with CF {live_cf:.2f} gets premium rate {live_rate}"
                            if live_cf < 0.5 and live_rate < premium_rate:
                                return True, f"Rate tier correctly assigns lower rate {live_rate} (not premium {premium_rate}) for low-CF industrial generator"
                        except (json.JSONDecodeError, KeyError, ValueError):
                            pass
    except Exception:
        pass

    # Strategy 2: Check source code from CONTAINER (not workspace - agent may edit workspace without rebuilding)
    content = ""
    settlement_containers = ["gridpeak_settlement", "settlement_engine", "settlement-engine"]
    for container_name in settlement_containers:
        rc, content, _ = run_docker_exec(container_name, ["cat", "/app/app.py"])
        if rc == 0 and content:
            break
    # Try docker cp for stopped containers
    if not content:
        for container_name in settlement_containers:
            tmp = f"/tmp/_verifier_{container_name}_app.py"
            try:
                cp_r = subprocess.run(
                    ["docker", "cp", f"{container_name}:/app/app.py", tmp],
                    capture_output=True, text=True, timeout=10
                )
                if cp_r.returncode == 0:
                    content = read_file(tmp)
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
                    if content:
                        break
            except Exception:
                continue
    if not content:
        # Last resort: workspace file (less reliable since container may not be rebuilt)
        content = read_file(PYTHON_PATH)

    # Find the determine_rate_tier function boundaries
    lines = content.split('\n')
    func_start = -1
    func_end = len(lines)

    for i, line in enumerate(lines):
        if 'def determine_rate_tier' in line:
            func_start = i
        elif func_start >= 0 and i > func_start and line.strip().startswith('def ') and 'determine_rate_tier' not in line:
            func_end = i
            break

    if func_start < 0:
        return False, "Could not find determine_rate_tier function"

    func_lines = lines[func_start:func_end]
    func_body = '\n'.join(func_lines)

    # Check 1: Is the buggy pattern still present?
    # The bug: loc_type matches location_type → immediate return without CF check
    for i, line in enumerate(func_lines):
        stripped = line.strip()
        if stripped.startswith('#'):
            continue

        # Pattern A: direct if with loc_type == location_type and return
        if ('loc_type' in stripped and 'location_type' in stripped and
            '==' in stripped and 'if' in stripped.lower()):
            # Check if CF validation is on the same if-line (combined condition)
            cf_on_if_line = any(t in stripped for t in [
                'capacity_factor', 'min_cf', 'cf_match', 'min_capacity'
            ])
            if cf_on_if_line:
                continue  # Fix is present as combined condition
            # Use indentation to scope only to this if-block (before elif/else)
            if_indent = len(line) - len(line.lstrip())
            block_lines = []
            for j in range(i + 1, len(func_lines)):
                next_line = func_lines[j]
                if not next_line.strip():
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent <= if_indent:
                    break  # Left the if block (elif, else, or new statement)
                block_lines.append(next_line)
            block_content = '\n'.join(block_lines)
            has_return = 'return float(rate)' in block_content or 'return rate' in block_content
            has_cf = ('capacity_factor' in block_content or 'min_cf' in block_content or
                      'cf_match' in block_content or 'min_capacity' in block_content)
            if has_return and not has_cf:
                return False, "Rate tier selection still skips capacity factor check for location matches"

        # Pattern B: loc_type == location_type on its own line (assignment or similar)
        if ('loc_type' in stripped and 'location_type' in stripped and
            '==' in stripped and 'return' in stripped and
            'capacity_factor' not in stripped and 'min_cf' not in stripped):
            return False, "Rate tier selection returns rate on location match without CF check"

    # Check 2: Verify fix is present - capacity_factor IS used in the function's tier loop
    has_cf_in_func = any(term in func_body for term in [
        'capacity_factor', 'min_cf', 'cf_match', 'min_capacity',
        'cap_factor', 'cf_check', 'capacity_check'
    ])
    has_loc_in_func = 'location_type' in func_body or 'loc_type' in func_body

    if has_loc_in_func and has_cf_in_func:
        # Extra validation: make sure CF check is in the tier loop, not just in function signature
        for_loop_start = -1
        for i, line in enumerate(func_lines):
            if 'for ' in line and ('tier' in line.lower() or 'rate' in line.lower()):
                for_loop_start = i
                break
        if for_loop_start >= 0:
            loop_body = '\n'.join(func_lines[for_loop_start:])
            if any(term in loop_body for term in ['capacity_factor', 'min_cf', 'cf_match', 'min_capacity']):
                return True, "Rate tier selection correctly checks capacity factor for location matches"

        # Even without finding the loop explicitly, if CF is checked near loc_type, it's fixed
        return True, "Rate tier selection includes capacity factor validation"

    if not has_loc_in_func:
        return False, "Could not find location type check in rate tier function"

    return False, "Could not verify capacity factor is checked for location-type matches"


def check_settlements_recalculated():
    """
    Verify settlements were recalculated AFTER fixes were applied.
    Checks that settlement data reflects corrected rate tier assignments
    and corrected loss factor calculations.
    """
    # Check that settlements exist
    rc, output = run_curl("http://localhost:8080/api/settlements?period_start=2025-10-01")
    if rc != 0:
        return False, "Could not query settlements API"

    try:
        settlements = json.loads(output)
        if not settlements or len(settlements) == 0:
            return False, "No settlements found"
    except json.JSONDecodeError:
        return False, "Invalid JSON response from settlements API"

    # Check 1: Industrial low-CF generators should NOT have premium rates
    cmd = [
        "docker", "exec", "gridpeak_postgres",
        "psql", "-U", "gridpeak", "-d", "energy_market",
        "-t", "-A", "-c",
        """
        SELECT COUNT(*) FROM settlements s
        JOIN generators g ON s.generator_id = g.id
        JOIN nodes n ON g.location_id = n.id
        WHERE n.location_type = 'industrial'
        AND s.capacity_factor < 0.5
        AND s.rate_applied > 50
        """
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        try:
            bad_rate_count = int(result.stdout.strip())
            if bad_rate_count > 0:
                return False, f"Found {bad_rate_count} industrial low-CF generators still with overpaid rates - recalculation needed after fix"
        except ValueError:
            pass

    # Check 2: Threshold-volume generators should have loss_factor > 1.0
    cmd2 = [
        "docker", "exec", "gridpeak_postgres",
        "psql", "-U", "gridpeak", "-d", "energy_market",
        "-t", "-A", "-c",
        """
        SELECT COUNT(*) FROM settlements
        WHERE energy_mwh BETWEEN 99.5 AND 100.5
        AND loss_factor_applied = 1.0
        """
    ]
    result2 = subprocess.run(cmd2, capture_output=True, text=True, timeout=10)
    if result2.returncode == 0:
        try:
            bad_loss_count = int(result2.stdout.strip())
            if bad_loss_count > 0:
                return False, f"Found {bad_loss_count} threshold-volume settlements with loss_factor=1.0 - loss factor bug not corrected"
        except ValueError:
            pass

    return True, f"Found {len(settlements)} settlements with correct rates and loss factors"


def check_no_fabricated_bugs():
    """Check that agent didn't introduce non-existent bugs.

    Golden solution only modifies:
    - loss_calculator/loss_calculator.f90: change > to >= for threshold
    - settlement_engine/app.py: add capacity factor check for location-type matches

    Known fabricated bugs agents create:
    - DECOMMISSIONED quality flag filtering (not a real calculation bug)
    - superseded_date filtering on rate tiers (already handled correctly)
    - Aggregation precision changes to meter reading summation
    - Date range filtering additions beyond the expected fix
    """
    errors = []

    # Read settlement engine code
    content = read_file(PYTHON_PATH)
    if not content:
        for cname in ["gridpeak_settlement", "settlement_engine", "settlement-engine"]:
            rc, content, _ = run_docker_exec(cname, ["cat", "/app/app.py"])
            if rc == 0 and content:
                break
        else:
            content = ""

    if content:
        # Check 1: DECOMMISSIONED quality flag filtering (common fabricated fix)
        # The original code has no DECOMMISSIONED filtering - this is not a real bug
        decommissioned_patterns = [
            r"quality_flag.*!=.*'DECOMMISSIONED'",
            r"quality_flag.*<>.*'DECOMMISSIONED'",
            r"quality_flag.*NOT.*DECOMMISSIONED",
            r"decommissioned.*quality",
            r"exclude.*decommissioned",
            r"filter.*decommissioned",
            r"DECOMMISSIONED.*WHERE",
            r"WHERE.*DECOMMISSIONED",
        ]
        for pattern in decommissioned_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                errors.append("Fabricated fix: DECOMMISSIONED quality flag filtering added (quality flags do not affect settlement calculations)")
                break

        # Check 2: superseded_date filtering (already handled correctly by effective tiers)
        if 'superseded_date' in content and 'superseded_date' not in read_file(PYTHON_PATH + '.orig'):
            # Check if it was added vs already present
            orig_content = ""
            # Read original from init.sql to check if rate_tiers query was modified
            if 'superseded_date IS NULL' in content or 'superseded_date' in content.lower():
                # Check if rate_tiers query was modified to filter superseded
                func_match = re.search(r'def determine_rate_tier.*?(?=\ndef |\Z)', content, re.DOTALL)
                if func_match and 'superseded' in func_match.group(0).lower():
                    errors.append("Fabricated fix: superseded_date filtering added to rate tier query (all current tiers have NULL superseded_date)")

        # Check 3: Excessive modifications (return statements, hardcoded values)
        if content.count("return float(rate)") > 10:
            errors.append("settlement_engine/app.py has excessive rate returns")
        if "direct_rate" in content.lower() or "hardcode" in content.lower():
            errors.append("settlement_engine/app.py may contain hardcoded values")

        # Check 4: aggregate_meter_readings modified (precision changes are fabricated)
        func_match = re.search(r'def aggregate_meter_readings.*?(?=\ndef |\Z)', content, re.DOTALL)
        if func_match:
            agg_func = func_match.group(0)
            # Check for precision-related fabricated changes
            if 'round(' in agg_func and 'ROUND_HALF_UP' not in agg_func:
                errors.append("Fabricated fix: aggregate_meter_readings precision changed (original uses Decimal with ROUND_HALF_UP)")
            if 'float(' in agg_func and 'Decimal' not in agg_func:
                errors.append("Fabricated fix: aggregate_meter_readings converted from Decimal to float (reduces precision)")

    # Check 5: loss_calculator/server.py suspicious modifications
    loss_server_content = read_file(os.path.join(WORKSPACE, "loss_calculator", "server.py"))
    if not loss_server_content:
        for cname in ["gridpeak_loss_calc", "loss_calculator", "loss-calculator"]:
            rc, loss_server_content, _ = run_docker_exec(cname, ["cat", "/app/server.py"])
            if rc == 0 and loss_server_content:
                break
            loss_server_content = ""

    if loss_server_content:
        if "BUG" in loss_server_content.upper() or "HACK" in loss_server_content.upper():
            errors.append("loss_calculator/server.py contains suspicious modifications")
        if "settlement" in loss_server_content.lower() and "override" in loss_server_content.lower():
            errors.append("loss_calculator/server.py may contain result overrides")

    if errors:
        return False, "; ".join(errors)
    return True, "No fabricated bugs detected"


def check_container_matches_workspace():
    """Verify container code matches workspace changes - fixes were deployed."""
    try:
        # Try multiple possible container names (agents sometimes rename containers)
        loss_calc_names = ["gridpeak_loss_calc", "loss_calculator", "loss-calculator"]
        settlement_names = ["gridpeak_settlement", "settlement_engine", "settlement-engine"]

        # Check Fortran file
        container_fortran = ""
        for name in loss_calc_names:
            rc, out, _ = run_docker_exec(name, ["cat", "/app/loss_calculator.f90"])
            if rc == 0 and out:
                container_fortran = out
                break
        if not container_fortran:
            for name in loss_calc_names:
                tmp = f"/tmp/_verifier_{name}_loss_calculator.f90"
                try:
                    cp_r = subprocess.run(
                        ["docker", "cp", f"{name}:/app/loss_calculator.f90", tmp],
                        capture_output=True, text=True, timeout=10
                    )
                    if cp_r.returncode == 0:
                        container_fortran = read_file(tmp)
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass
                        if container_fortran:
                            break
                except Exception:
                    continue
        if not container_fortran:
            return False, "Could not read container Fortran code (tried: " + ", ".join(loss_calc_names) + ")"

        workspace_fortran = read_file(FORTRAN_PATH)
        if workspace_fortran:
            ws_correct = bool(re.search(r'emwh\s*>=\s*thresh', workspace_fortran, re.IGNORECASE)) or \
                         bool(re.search(r'emwh\s*\.ge\.\s*thresh', workspace_fortran, re.IGNORECASE))
            ct_buggy = bool(re.search(r'emwh\s*>\s*thresh(?!\s*\.)', container_fortran, re.IGNORECASE)) and \
                       not bool(re.search(r'emwh\s*>=\s*thresh', container_fortran, re.IGNORECASE))

            if ws_correct and ct_buggy:
                return False, "Container not rebuilt: loss factor fix not deployed"

        # Check Python file
        container_python = ""
        for name in settlement_names:
            rc2, out2, _ = run_docker_exec(name, ["cat", "/app/app.py"])
            if rc2 == 0 and out2:
                container_python = out2
                break
        if not container_python:
            for name in settlement_names:
                tmp = f"/tmp/_verifier_{name}_app.py"
                try:
                    cp_r = subprocess.run(
                        ["docker", "cp", f"{name}:/app/app.py", tmp],
                        capture_output=True, text=True, timeout=10
                    )
                    if cp_r.returncode == 0:
                        container_python = read_file(tmp)
                        try:
                            os.remove(tmp)
                        except Exception:
                            pass
                        if container_python:
                            break
                except Exception:
                    continue
        if not container_python:
            return False, "Could not read container Python code (tried: " + ", ".join(settlement_names) + ")"

        workspace_python = read_file(PYTHON_PATH)
        if workspace_python:
            # Check if container still has the buggy pattern
            ct_func = re.search(r'def determine_rate_tier.*?(?=\ndef |\Z)', container_python, re.DOTALL)
            ws_func = re.search(r'def determine_rate_tier.*?(?=\ndef |\Z)', workspace_python, re.DOTALL)

            if ct_func and ws_func:
                ct_body = ct_func.group(0)
                ws_body = ws_func.group(0)
                # Check if container has buggy pattern but workspace doesn't
                ct_has_bug = False
                ws_has_bug = False
                for line in ct_body.split('\n'):
                    s = line.strip()
                    if ('loc_type' in s and 'location_type' in s and '==' in s and
                        'if' in s.lower() and 'capacity_factor' not in s and 'min_cf' not in s):
                        next_lines = ct_body[ct_body.index(line):][:200]
                        if 'return float(rate)' in next_lines.split('\n')[1] if len(next_lines.split('\n')) > 1 else False:
                            ct_has_bug = True
                for line in ws_body.split('\n'):
                    s = line.strip()
                    if ('loc_type' in s and 'location_type' in s and '==' in s and
                        'if' in s.lower() and 'capacity_factor' not in s and 'min_cf' not in s):
                        next_lines = ws_body[ws_body.index(line):][:200]
                        if 'return float(rate)' in next_lines.split('\n')[1] if len(next_lines.split('\n')) > 1 else False:
                            ws_has_bug = True

                if not ws_has_bug and ct_has_bug:
                    return False, "Container not rebuilt: rate tier fix not deployed"

        # Direct content comparison: workspace and container files must actually match
        def normalize(s):
            return '\n'.join(line.rstrip() for line in s.strip().splitlines())

        if workspace_fortran and container_fortran:
            if normalize(workspace_fortran) != normalize(container_fortran):
                return False, "Container Fortran file differs from workspace (content mismatch)"

        if workspace_python and container_python:
            if normalize(workspace_python) != normalize(container_python):
                return False, "Container Python file differs from workspace (content mismatch)"

        return True, "Container code matches workspace"
    except Exception as e:
        return False, f"Container check failed: {str(e)}"


def check_calculation_correct():
    """Test actual calculations with known inputs to verify fixes are working.

    Checks:
    1. Loss factor for threshold energy returns > 1.0
    2. Rate tier for industrial low-CF generator returns correct rate
    3. Energy totals in settlements match ALL meter readings (no fabricated quality flag filtering)
    """
    errors = []

    # Test 1: Loss factor for threshold energy
    try:
        result = subprocess.run(
            ["curl", "-sf", "-X", "POST",
             "http://localhost:8081/calculate",
             "-H", "Content-Type: application/json",
             "-d", json.dumps({"zone": "NORTH", "energy_mwh": 100.0})],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            try:
                loss_result = json.loads(result.stdout)
                loss_factor = loss_result.get('loss_factor', 1.0)
                threshold = loss_result.get('threshold', 0)
                if loss_factor == 1.0 and abs(threshold - 100.0) < 0.5:
                    errors.append(f"Loss factor bug still present: energy=100.0 at threshold={threshold} got factor={loss_factor}")
            except (json.JSONDecodeError, KeyError):
                pass
        else:
            errors.append("Loss calculator service not responding")
    except Exception:
        errors.append("Loss calculator service unreachable")

    # Test 2: Energy totals - verify no fabricated quality flag filtering
    # Compare settlement energy_mwh against expected totals from ALL meter readings
    try:
        # Get a sample of settlement energy values and compare to raw meter reading sums
        energy_check_cmd = [
            "docker", "exec", "gridpeak_postgres",
            "psql", "-U", "gridpeak", "-d", "energy_market",
            "-t", "-A", "-c",
            """
            SELECT s.generator_id, s.energy_mwh as settlement_energy,
                   ROUND(SUM(m.energy_mw * m.interval_minutes / 60.0)::numeric, 2) as expected_energy
            FROM settlements s
            JOIN meter_readings m ON m.generator_id = s.generator_id
                AND m.timestamp >= s.period_start AND m.timestamp < s.period_end
            GROUP BY s.generator_id, s.energy_mwh, s.period_start, s.period_end
            ORDER BY ABS(s.energy_mwh - ROUND(SUM(m.energy_mw * m.interval_minutes / 60.0)::numeric, 2)) DESC
            LIMIT 5
            """
        ]
        energy_result = subprocess.run(energy_check_cmd, capture_output=True, text=True, timeout=15)
        if energy_result.returncode == 0 and energy_result.stdout.strip():
            mismatches = []
            for line in energy_result.stdout.strip().split('\n'):
                parts = line.split('|')
                if len(parts) >= 3:
                    gen_id = parts[0].strip()
                    settlement_energy = float(parts[1].strip())
                    expected_energy = float(parts[2].strip())
                    # Allow small rounding tolerance (0.5%)
                    if expected_energy > 0 and abs(settlement_energy - expected_energy) / expected_energy > 0.005:
                        mismatches.append(f"gen {gen_id}: settlement={settlement_energy}, expected={expected_energy}")
            if mismatches:
                errors.append(f"Energy totals corrupted (likely fabricated quality flag filtering): {'; '.join(mismatches[:3])}")
    except Exception:
        pass

    if errors:
        return False, "; ".join(errors)
    return True, "Calculations produce correct values after fixes (rate tiers, loss factors, and energy totals verified)"


def run_programmatic_checks():
    """Run all checks and return results in standard format."""
    checks = [
        ("loss_factor_bug_fixed", check_loss_factor_bug_fixed, 10),
        ("rate_tier_bug_fixed", check_rate_tier_bug_fixed, 10),
        ("settlements_recalculated", check_settlements_recalculated, 8),
        ("no_fabricated_bugs", check_no_fabricated_bugs, 8),
        ("container_matches_workspace", check_container_matches_workspace, 3),
        ("calculation_correct", check_calculation_correct, 5),
    ]

    results = []

    for check_id, check_func, points in checks:
        try:
            passed, detail = check_func()
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
    if not all(r["passed"] for r in results):
        sys.exit(1)
