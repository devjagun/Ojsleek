#!/usr/bin/env python3
import subprocess
import os
import time

def get_workspace_path():
    if os.path.exists("/workspace/loss_calculator"):
        return "/workspace"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), "environment")

WORKSPACE = get_workspace_path()
FORTRAN_PATH = os.path.join(WORKSPACE, "loss_calculator", "loss_calculator.f90")
PYTHON_PATH = os.path.join(WORKSPACE, "settlement_engine", "app.py")

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def fix_fortran_loss_calculator():
    content = read_file(FORTRAN_PATH)
    
    old_code = "        if (emwh > thresh) then"
    new_code = "        if (emwh >= thresh) then"
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        write_file(FORTRAN_PATH, content)
        return True
    return False

def fix_settlement_rate_tier():
    content = read_file(PYTHON_PATH)
    
    old_code = """        if loc_type is not None and loc_type == location_type:
            return float(rate)
        elif loc_type is None:"""
    
    new_code = """        if loc_type is not None and loc_type == location_type:
            if min_cf is None or capacity_factor >= float(min_cf):
                return float(rate)
        elif loc_type is None:"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        write_file(PYTHON_PATH, content)
        return True
    return False

def rebuild_services():
    os.chdir(WORKSPACE)
    subprocess.run(
        ["docker", "compose", "build", "loss_calculator", "settlement_engine"],
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["docker", "compose", "up", "-d", "loss_calculator", "settlement_engine"],
        check=True,
        capture_output=True
    )
    time.sleep(5)

def recalculate_settlements():
    periods = [
        ("2025-10-01T00:00:00", "2025-10-08T00:00:00"),
        ("2025-10-08T00:00:00", "2025-10-15T00:00:00"),
        ("2025-10-15T00:00:00", "2025-10-22T00:00:00"),
        ("2025-10-22T00:00:00", "2025-11-01T00:00:00"),
        ("2025-11-01T00:00:00", "2025-11-08T00:00:00"),
        ("2025-11-08T00:00:00", "2025-11-15T00:00:00"),
    ]

    for start, end in periods:
        cmd = [
            "curl", "-sf", "-X", "POST",
            "http://localhost:8080/api/recalculate_all",
            "-H", "Content-Type: application/json",
            "-d", f'{{"period_start": "{start}", "period_end": "{end}"}}'
        ]
        subprocess.run(cmd, capture_output=True, text=True)
        time.sleep(1)

def main():
    print("Fixing Fortran loss calculator boundary condition...")
    if fix_fortran_loss_calculator():
        print("  Fixed: Changed > to >= for threshold comparison")
    else:
        print("  Already fixed or pattern not found")

    print("Fixing Python rate tier selection...")
    if fix_settlement_rate_tier():
        print("  Fixed: Added capacity factor check for location-matching tiers")
    else:
        print("  Already fixed or pattern not found")

    print("Rebuilding services...")
    rebuild_services()
    print("  Services rebuilt")

    print("Recalculating settlements...")
    recalculate_settlements()
    print("  Settlements recalculated")

    print("Golden solution applied successfully")

if __name__ == "__main__":
    main()
