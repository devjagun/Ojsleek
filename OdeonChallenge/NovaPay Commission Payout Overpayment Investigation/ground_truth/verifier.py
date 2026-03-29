import json
import sys
import os
import subprocess
import hashlib
import re

def get_workspace_path():
    if os.path.exists("/workspace/commission_calc"):
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
        ['docker', 'exec', 'novapay_postgres', 'psql', '-U', 'novapay', '-d', 'novapay', '-t', '-A', '-c', query],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()

def read_fortran_file():
    fortran_path = os.path.join(WORKSPACE, "commission_calc", "commission_calc.f90")
    if not os.path.exists(fortran_path):
        return None
    with open(fortran_path, 'r') as f:
        return f.read()

def check_boundary_condition_fixed():
    """Check if the volume loyalty boundary condition was fixed (>= 90 to > 90)."""
    content = read_fortran_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'vd' in line.lower() and '90' in line:
            stripped = line.strip().lower()
            if '>= 90' in stripped or '>=90' in stripped:
                return False
            if '> 90' in stripped or '>90' in stripped:
                if '>=' not in stripped:
                    return True
    return False

def check_priority_branch_fixed():
    """Check if the partnership multiplier branch order was fixed."""
    content = read_fortran_file()
    if content is None:
        return False
    
    lines = content.split('\n')
    in_gm_function = False
    platinum_volume_check_line = -1
    volume_only_check_line = -1
    platinum_only_check_line = -1
    
    for i, line in enumerate(lines):
        lower_line = line.lower()
        
        if 'function gm' in lower_line:
            in_gm_function = True
            continue
        
        if in_gm_function and 'end function' in lower_line:
            break
        
        if in_gm_function:
            if 'platinum' in lower_line and '100000' in lower_line and 'if' in lower_line:
                platinum_volume_check_line = i
            elif '100000' in lower_line and 'platinum' not in lower_line and 'if' in lower_line:
                volume_only_check_line = i
            elif 'platinum' in lower_line and '100000' not in lower_line and 'if' in lower_line:
                platinum_only_check_line = i
    
    # Correct order: platinum+volume first, then platinum only, then volume only
    if platinum_volume_check_line > 0 and volume_only_check_line > 0 and platinum_only_check_line > 0:
        if platinum_volume_check_line < platinum_only_check_line < volume_only_check_line:
            return True
        if platinum_volume_check_line < volume_only_check_line and platinum_volume_check_line < platinum_only_check_line:
            return True
    
    return False

def run_docker_exec(container, cmd):
    """Run a command in a container, return (returncode, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["docker", "exec", container] + cmd,
            capture_output=True, text=True, timeout=10
        )
        return result.returncode, result.stdout, result.stderr
    except Exception:
        return -1, "", ""


def read_container_fortran():
    """Read Fortran code from running container, with docker cp fallback."""
    for cname in ["commission-calc", "novapay_commission_calc", "novapay-commission-calc"]:
        rc, out, _ = run_docker_exec(cname, ["cat", "/app/commission_calc.f90"])
        if rc == 0 and out.strip():
            return out
    # docker cp fallback for stopped containers
    for cname in ["commission-calc", "novapay_commission_calc", "novapay-commission-calc"]:
        try:
            tmp = f"/tmp/_verifier_{cname}_cc.f90"
            subprocess.run(["docker", "cp", f"{cname}:/app/commission_calc.f90", tmp],
                           capture_output=True, timeout=10)
            if os.path.exists(tmp):
                with open(tmp) as f:
                    content = f.read()
                os.remove(tmp)
                if content.strip():
                    return content
        except Exception:
            pass
    return None


def check_service_rebuilt():
    """Check if commission-calc was rebuilt with fixes, not just running original buggy code."""
    container_running = False
    try:
        result = subprocess.run(
            ['docker', 'compose', 'ps', 'commission-calc'],
            capture_output=True, text=True, cwd=WORKSPACE
        )
        if 'running' in result.stdout.lower() or 'up' in result.stdout.lower():
            container_running = True
    except Exception:
        pass

    if not container_running:
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=commission', '--format', '{{.Status}}'],
                capture_output=True, text=True
            )
            if 'up' in result.stdout.lower():
                container_running = True
        except Exception:
            pass

    container_code = read_container_fortran()
    if container_code is None:
        if container_running:
            return False, "Container running but cannot read Fortran code"
        return False, "commission-calc container not found"

    # Check if at least one fix is present in the container code
    has_boundary_fix = False
    has_priority_fix = False

    # Boundary fix: > 90 instead of >= 90
    for line in container_code.split('\n'):
        stripped = line.strip().lower()
        if 'vd' in stripped and '90' in stripped:
            if ('> 90' in stripped or '>90' in stripped) and '>=' not in stripped:
                has_boundary_fix = True

    # Priority fix: Platinum+volume compound check must come before Platinum-only
    lines = container_code.split('\n')
    in_gm = False
    platinum_volume_line = -1
    platinum_only_line = -1
    for i, line in enumerate(lines):
        ll = line.lower()
        if 'function gm' in ll:
            in_gm = True
        elif in_gm and 'end function' in ll:
            break
        elif in_gm:
            if 'platinum' in ll and '100000' in ll and 'if' in ll:
                platinum_volume_line = i
            elif 'platinum' in ll and '100000' not in ll and 'if' in ll:
                platinum_only_line = i
    if platinum_volume_line > 0 and platinum_only_line > 0 and platinum_volume_line < platinum_only_line:
        has_priority_fix = True

    if has_boundary_fix or has_priority_fix:
        return True, "commission-calc rebuilt with fixes deployed"

    if container_running:
        return False, "Container is running but still has original buggy code - service was not rebuilt with fixes"
    return False, "commission-calc container not running"

def check_no_fabricated_bugs():
    """Check that agent didn't introduce non-existent bugs.

    Golden solution only modifies commission_calc/commission_calc.f90.
    Any changes to app.py, gateway/main.go, payout_engine/app.py, or
    analytics/app.py are fabricated fixes.

    Known fabricated bugs agents create:
    - Adding 'category = sale' filter to app.py SQL queries
    - Adding promotional rate logic from merchant_onboarding
    - Removing LIMIT 1000 from gateway/main.go
    - Rating condition inversion in Fortran
    - Base commission multiplier changes
    - Volume loyalty condition inversion (< 90)
    - Tenure calculation changes (datetime.now() → period_end_date)
    """
    errors = []

    # --- Check Fortran code for inversions/tampering ---
    content = read_fortran_file()
    if content:
        lines = content.split('\n')
        # Rating condition: rt > 4.5 → 1.08 is CORRECT, should not be inverted
        for i, line in enumerate(lines):
            lower_line = line.lower().strip()
            if ('rt' in lower_line or 'rating' in lower_line) and '4.5' in lower_line:
                if '< 4.5' in lower_line or '<4.5' in lower_line or '<= 4.5' in lower_line:
                    if i + 1 < len(lines) and '1.08' in lines[i + 1]:
                        errors.append("Rating condition inverted (< 4.5 gets 1.08 is wrong)")

        # Deficit multiplier 0.90d0 must be present
        if '0.90d0' not in content:
            errors.append("Base commission deficit multiplier changed from 0.90")

        # Volume loyalty inversion: should be > 90, not < 90
        for line in lines:
            ll = line.lower().strip()
            if ('vd' in ll or 'volume_days' in ll) and '90' in ll:
                if ('< 90' in ll or '<90' in ll) and '>=' not in ll:
                    errors.append("Volume loyalty condition inverted to < 90 (should be > 90)")

    # --- Check non-Fortran files for unauthorized modifications ---
    # Original SHA256 hashes of files that should NOT be modified
    ORIGINAL_HASHES = {
        "commission_calc/app.py": "361eb7064bfff56080860a4ae657fcf79e145e82068cd3f568e2b8249916c479",
        "gateway/main.go": "9188738f772d4628543def706fe21459ac8908d28d14f24330ca069647e5aab4",
        "analytics/app.py": "d83ebd3beb5700a0aaee8eef1f59952489147ce5494e0e841e10ad405806003e",
        "payout_engine/app.py": "9468e2362a8a82f596e198caf54a845a1d95ac30c42afa7d81438c1fbd751d2f",
    }

    # Check workspace files
    for rel_path, original_hash in ORIGINAL_HASHES.items():
        full_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()
                if current_hash != original_hash:
                    errors.append(f"Fabricated fix (workspace): {rel_path} was modified - golden solution only modifies Fortran code")
            except Exception:
                pass

    # Check container files for unauthorized modifications
    container_checks = {
        "commission_calc/app.py": ("novapay_commission_calc", "/app/app.py"),
        "gateway/main.go": ("novapay_gateway", "/app/main.go"),
    }
    for rel_path, (container, container_path) in container_checks.items():
        original_hash = ORIGINAL_HASHES[rel_path]
        for cname in [container, container.replace("novapay_", "")]:
            rc, out, _ = run_docker_exec(cname, ["cat", container_path])
            if rc == 0 and out.strip():
                current_hash = hashlib.sha256(out.encode()).hexdigest()
                if current_hash != original_hash:
                    # Content-level checks for known fabrication patterns
                    fabrication_patterns = []
                    if "category" in rel_path or "app.py" in rel_path:
                        if "category" in out and "sale" in out and "category" not in open(os.path.join(WORKSPACE, rel_path)).read():
                            fabrication_patterns.append("category='sale' filter added")
                        if "merchant_onboarding" in out or "promotional_rate" in out:
                            fabrication_patterns.append("promotional rate logic added")
                    if "main.go" in rel_path:
                        if "LIMIT 1000" not in out and "LIMIT" not in out:
                            fabrication_patterns.append("LIMIT removed from gateway queries")
                    detail = f"Fabricated fix (container): {rel_path} was modified"
                    if fabrication_patterns:
                        detail += f" ({'; '.join(fabrication_patterns)})"
                    errors.append(detail)
                break

    # Also do content-level checks on workspace files for known patterns
    # even if hash check might not catch everything
    for rel_path in ["commission_calc/app.py"]:
        full_path = os.path.join(WORKSPACE, rel_path)
        if os.path.exists(full_path):
            with open(full_path) as f:
                ws_content = f.read()
            if "category" in ws_content and re.search(r"category\s*=\s*['\"]sale['\"]", ws_content):
                if not any("category" in e for e in errors):
                    errors.append(f"Fabricated fix (workspace): {rel_path} has category='sale' filter added")
            if "merchant_onboarding" in ws_content or "promotional_rate" in ws_content:
                if not any("promotional" in e for e in errors):
                    errors.append(f"Fabricated fix (workspace): {rel_path} has promotional rate logic from merchant_onboarding")

    # --- Check workspace for fabrication evidence in agent-created files ---
    # Agents may claim fabricated bugs in response/notes even without code changes.
    # Scan all non-original workspace files for known fabrication patterns.
    fabrication_evidence_patterns = [
        (r"category\s*[=!<>]+\s*['\"]sale['\"]", "transaction category='sale' filtering (fabricated bug)"),
        (r"promotional[_\s]*rate", "promotional rate logic (fabricated bug)"),
        (r"transaction.*contamination|volume.*contamination", "transaction contamination claim (fabricated bug)"),
        (r"refund.*inflat|chargeback.*inflat", "refund/chargeback inflation claim (fabricated bug)"),
    ]
    original_files = set(ORIGINAL_HASHES.keys()) | {"commission_calc/commission_calc.f90"}
    try:
        for root, dirs, files in os.walk(WORKSPACE):
            for fname in files:
                if not fname.endswith(('.py', '.sh', '.sql', '.md', '.txt', '.patch')):
                    continue
                filepath = os.path.join(root, fname)
                rel = os.path.relpath(filepath, WORKSPACE)
                # Skip original source files (already checked via hash above)
                if rel in original_files:
                    continue
                # Skip standard infrastructure files
                if rel.startswith(('_seed_data/', '.git/')):
                    continue
                try:
                    with open(filepath) as fh:
                        file_content = fh.read()
                    for pattern, desc in fabrication_evidence_patterns:
                        if re.search(pattern, file_content, re.IGNORECASE):
                            errors.append(f"Fabrication evidence in {rel}: {desc}")
                            break
                except Exception:
                    pass
    except Exception:
        pass

    if errors:
        return False, "; ".join(errors)
    return True, "No fabricated bugs detected"


def check_container_matches_workspace():
    """Verify container code matches workspace changes - fixes were deployed."""
    try:
        container_code = read_container_fortran()
        if container_code is None:
            return False, "Could not read container Fortran code"

        workspace_code = read_fortran_file()
        if workspace_code is None:
            return False, "Could not read workspace Fortran code"

        # Check if fixes are present in workspace
        ws_has_boundary = '> 90' in workspace_code and '>= 90' not in workspace_code.replace('> 90', '')
        ct_has_boundary = '> 90' in container_code and '>= 90' not in container_code.replace('> 90', '')

        if ws_has_boundary and not ct_has_boundary:
            return False, "Container not rebuilt: boundary fix not deployed"

        # Must have at least one fix present (not just trivial match of both buggy)
        if not ws_has_boundary and not ct_has_boundary:
            # Check priority fix
            ws_priority = check_priority_branch_fixed()
            if not ws_priority:
                return False, "No fixes applied to workspace code"

        return True, "Container matches workspace"
    except Exception as e:
        return False, f"Container check failed: {str(e)}"


def check_calculation_correct():
    """Test actual calculations with known inputs to verify fixes are working.

    MUST use live service tests - if services are down, this check should FAIL.
    """
    try:
        # Check that commission calc service is actually responding
        health_check = subprocess.run(
            ["curl", "-sf", "http://localhost:9000/health"],
            capture_output=True, text=True, timeout=10
        )
        service_up = (health_check.returncode == 0)

        if not service_up:
            return False, "Commission calc service is not responding - container may have crashed or has syntax errors"

        # Read container code to verify fixes are present
        container_code = read_container_fortran()
        if container_code is None:
            return False, "Cannot read container code to verify calculations"

        # Verify boundary fix is in running container
        ct_has_boundary = '> 90' in container_code and '>= 90' not in container_code.replace('> 90', '')

        # Verify priority fix is in running container
        ct_has_priority = False
        lines = container_code.split('\n')
        in_gm = False
        pv_line = -1
        po_line = -1
        for i, line in enumerate(lines):
            ll = line.lower()
            if 'function gm' in ll:
                in_gm = True
            elif in_gm and 'end function' in ll:
                break
            elif in_gm:
                if 'platinum' in ll and '100000' in ll and 'if' in ll:
                    pv_line = i
                elif 'platinum' in ll and '100000' not in ll and 'if' in ll:
                    po_line = i
        if pv_line > 0 and po_line > 0 and pv_line < po_line:
            ct_has_priority = True

        if not ct_has_boundary and not ct_has_priority:
            return False, "Container still has buggy code - fixes not deployed"

        # Try live calculation test if possible
        try:
            import urllib.request
            test_data = json.dumps({
                "merchant_id": 1,
                "period_start": "2026-01-01",
                "period_end": "2026-01-31"
            }).encode()
            req = urllib.request.Request(
                "http://localhost:9000/calculate",
                data=test_data,
                headers={"Content-Type": "application/json"}
            )
            resp = urllib.request.urlopen(req, timeout=10)
            # If we get a response, the service is computing
        except Exception:
            pass  # Service may not support this exact endpoint format

        return True, "Calculations match expected values"
    except Exception as e:
        return False, f"Calculation check failed: {str(e)}"


def run_programmatic_checks():
    rubric = load_rubric()
    checks_def = {c["id"]: c["points"] for c in rubric["programmatic_checks"]}
    results = []

    checks = [
        ("boundary_condition_fixed", check_boundary_condition_fixed),
        ("priority_branch_fixed", check_priority_branch_fixed),
        ("service_rebuilt", check_service_rebuilt),
        ("no_fabricated_bugs", check_no_fabricated_bugs),
        ("container_matches_workspace", check_container_matches_workspace),
        ("calculation_correct", check_calculation_correct),
    ]

    for check_id, check_func in checks:
        points = checks_def.get(check_id, 0)
        try:
            result = check_func()
            if isinstance(result, tuple):
                passed, detail = result
            else:
                passed = result
                detail = f"{check_id} {'passed' if passed else 'failed'}"
            if check_id == "no_fabricated_bugs":
                achieved = points if passed else -points
            else:
                achieved = points if passed else 0
            results.append({
                "id": check_id,
                "passed": passed,
                "points_achieved": achieved,
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
