#!/usr/bin/env python3
import subprocess
import json
import hashlib
import sys

ORIGINAL_HASHES = {
    "gateway/main.go": None,
    "loss_calculator/server.py": None,
    "loss_calculator/requirements.txt": None,
    "settlement_engine/requirements.txt": None,
}

def run_docker_exec(container, cmd):
    full_cmd = ["docker", "exec", container] + cmd
    result = subprocess.run(full_cmd, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr

def run_curl(url):
    result = subprocess.run(["curl", "-sf", url], capture_output=True, text=True)
    return result.returncode, result.stdout

def compute_file_hash(container, filepath):
    rc, stdout, _ = run_docker_exec(container, ["cat", filepath])
    if rc == 0:
        return hashlib.sha256(stdout.encode()).hexdigest()
    return None

def check_loss_factor_bug_fixed():
    container = "gridpeak_loss_calc"
    rc, content, _ = run_docker_exec(container, ["cat", "/app/loss_calculator.f90"])

    if rc != 0:
        return False, "Could not read loss_calculator.f90"

    if "if (emwh >= thresh) then" in content:
        return True, "Threshold comparison correctly uses >= operator"

    if "if (emwh > thresh) then" in content:
        return False, "Threshold comparison still uses > instead of >="

    return False, "Could not determine threshold comparison operator"

def check_rate_tier_bug_fixed():
    container = "gridpeak_settlement"
    rc, content, _ = run_docker_exec(container, ["cat", "/app/app.py"])

    if rc != 0:
        return False, "Could not read app.py"

    buggy_pattern = """        if loc_type is not None and loc_type == location_type:
            return float(rate)
        elif loc_type is None:"""

    fixed_pattern = """        if loc_type is not None and loc_type == location_type:
            if min_cf is None or capacity_factor >= float(min_cf):
                return float(rate)
        elif loc_type is None:"""

    if fixed_pattern in content:
        return True, "Rate tier selection correctly checks capacity factor for location matches"

    if buggy_pattern in content:
        return False, "Rate tier selection still skips capacity factor check for location matches"

    return False, "Could not determine rate tier selection logic"

def check_settlements_recalculated():
    rc, output = run_curl("http://localhost:8080/api/settlements?period_start=2025-10-01")

    if rc != 0:
        return False, "Could not query settlements API"

    try:
        settlements = json.loads(output)
        if not settlements or len(settlements) == 0:
            return False, "No settlements found"

        industrial_low_cf = []
        for s in settlements:
            if s.get("capacity_factor", 1.0) < 0.75:
                industrial_low_cf.append(s)

        return True, f"Found {len(settlements)} settlements"
    except json.JSONDecodeError:
        return False, "Invalid JSON response from settlements API"

def check_no_fabricated_bugs():
    modified_unexpected = []

    loss_server_rc, loss_server_content, _ = run_docker_exec("gridpeak_loss_calc", ["cat", "/app/server.py"])
    if loss_server_rc == 0:
        if "BUG" in loss_server_content.upper() or "HACK" in loss_server_content.upper():
            modified_unexpected.append("loss_calculator/server.py contains suspicious modifications")

        if "settlement" in loss_server_content.lower() and "override" in loss_server_content.lower():
            modified_unexpected.append("loss_calculator/server.py may contain result overrides")

    settle_rc, settle_content, _ = run_docker_exec("gridpeak_settlement", ["cat", "/app/app.py"])
    if settle_rc == 0:
        if settle_content.count("return float(rate)") > 10:
            modified_unexpected.append("settlement_engine/app.py has excessive rate returns")

        if "direct_rate" in settle_content.lower() or "hardcode" in settle_content.lower():
            modified_unexpected.append("settlement_engine/app.py may contain hardcoded values")

    if modified_unexpected:
        return False, "; ".join(modified_unexpected)

    return True, "No unexpected file modifications detected"

def verify_loss_deductions_applied():
    cmd = [
        "docker", "exec", "gridpeak_postgres",
        "psql", "-U", "gridpeak", "-d", "energy_market",
        "-t", "-A", "-c",
        "SELECT COUNT(*) FROM settlements WHERE loss_factor_applied > 1.0 AND energy_mwh >= 99.5 AND energy_mwh <= 100.5"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False, "Could not query database"

    try:
        count = int(result.stdout.strip())
        if count > 0:
            return True, f"Found {count} threshold-volume settlements with proper loss factors"
        else:
            return False, "No threshold-volume settlements have loss factors > 1.0"
    except ValueError:
        return False, "Invalid count returned from database"

def verify_industrial_rates_correct():
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
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        return False, "Could not query database"

    try:
        count = int(result.stdout.strip())
        if count == 0:
            return True, "Low capacity factor industrial generators have appropriate rates"
        else:
            return False, f"Found {count} industrial generators with low CF but high rates"
    except ValueError:
        return False, "Invalid count returned from database"

def run_programmatic_checks():
    """Run all checks and return results in standard format."""
    checks = [
        ("loss_factor_bug_fixed", check_loss_factor_bug_fixed, 15),
        ("rate_tier_bug_fixed", check_rate_tier_bug_fixed, 15),
        ("settlements_recalculated", check_settlements_recalculated, 10),
        ("no_fabricated_bugs", check_no_fabricated_bugs, 10),
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
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    if not all(r["passed"] for r in results):
        sys.exit(1)
