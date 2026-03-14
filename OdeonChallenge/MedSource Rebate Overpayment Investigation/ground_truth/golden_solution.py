#!/usr/bin/env python3
import subprocess
import os

def get_workspace_path():
    if os.path.exists("/workspace/rebate_engine"):
        return "/workspace"
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(os.path.dirname(script_dir), "environment")

WORKSPACE = get_workspace_path()
ADA_PATH = os.path.join(WORKSPACE, "rebate_engine", "rebate_calc.adb")

def read_file(path):
    with open(path, 'r') as f:
        return f.read()

def write_file(path, content):
    with open(path, 'w') as f:
        f.write(content)

def fix_rebate_calc_ada():
    content = read_file(ADA_PATH)
    original_content = content

    # Fix 1: Change certification duration check from >= 180 to > 180
    content = content.replace(
        'Qualifies_Cert := (Cert_Days >= 180);',
        'Qualifies_Cert := (Cert_Days > 180);'
    )

    # Fix 2: Change product mix factor from accumulation to exclusive logic
    old_logic = """      if Has_Spec_Cert and Qualifies_Cert then
         Factor := Factor + 0.18;
      end if;

      if Is_High_Volume then
         Factor := Factor + 0.12;
      end if;

      Factor := Float(Integer(Factor * 100.0 + 0.5)) / 100.0;
      return Factor;"""

    new_logic = """      if Has_Spec_Cert and Qualifies_Cert and Is_High_Volume then
         Factor := 1.28;
      elsif Has_Spec_Cert and Qualifies_Cert then
         Factor := 1.18;
      elsif Is_High_Volume then
         Factor := 1.12;
      else
         Factor := 1.00;
      end if;

      return Factor;"""

    content = content.replace(old_logic, new_logic)

    if content == original_content:
        return False

    write_file(ADA_PATH, content)
    return True

def rebuild_service():
    os.chdir(WORKSPACE)
    subprocess.run(
        ["docker", "compose", "build", "rebate-engine"],
        check=True,
        capture_output=True
    )
    subprocess.run(
        ["docker", "compose", "up", "-d", "rebate-engine"],
        check=True,
        capture_output=True
    )

def main():
    print("Fixing Ada rebate calculator...")
    if fix_rebate_calc_ada():
        print("  Fixed: Changed certification check and product mix logic")
    else:
        print("  Already fixed or pattern not found")

    print("Rebuilding service...")
    rebuild_service()
    print("  Service rebuilt")

    print("Golden solution applied successfully")

if __name__ == "__main__":
    main()
