#!/usr/bin/env python3

import os
import sys
import re


def fix_rebate_calc_ada(env_path):
    ada_file = os.path.join(env_path, "rebate_engine", "rebate_calc.adb")

    if not os.path.exists(ada_file):
        return False, f"Ada file not found: {ada_file}"

    with open(ada_file, 'r') as f:
        content = f.read()

    original_content = content

    content = re.sub(
        r'Qualifies_Cert\s*:=\s*\(Cert_Days\s*>=\s*180\)',
        'Qualifies_Cert := (Cert_Days > 180)',
        content
    )

    buggy_pattern = r'''if Has_Spec_Cert and Qualifies_Cert then
         Factor := Factor \+ 0\.18;
      end if;

      if Is_High_Volume then
         Factor := Factor \+ 0\.12;
      end if;

      Factor := Float\(Integer\(Factor \* 100\.0 \+ 0\.5\)\) / 100\.0;
      return Factor;'''

    fixed_logic = '''if Has_Spec_Cert and Qualifies_Cert and Is_High_Volume then
         Factor := 1.28;
      elsif Has_Spec_Cert and Qualifies_Cert then
         Factor := 1.18;
      elsif Is_High_Volume then
         Factor := 1.12;
      else
         Factor := 1.00;
      end if;

      return Factor;'''

    content = re.sub(buggy_pattern, fixed_logic, content, flags=re.DOTALL)

    if content == original_content:
        return False, "No changes were applied - patterns may have already been fixed or not found"

    with open(ada_file, 'w') as f:
        f.write(content)

    return True, "Successfully applied both fixes to rebate_calc.adb"


def main():
    if len(sys.argv) < 2:
        print("Usage: python golden_solution.py <path_to_environment_dir>")
        print("Example: python golden_solution.py ./environment")
        sys.exit(1)

    env_path = sys.argv[1]

    if not os.path.isdir(env_path):
        print(f"Error: Directory not found: {env_path}")
        sys.exit(1)

    print("MedSource Rebate Overpayment Investigation - Golden Solution")
    print("=" * 60)
    print()

    print("Applying fixes to rebate_calc.adb...")
    success, message = fix_rebate_calc_ada(env_path)

    if success:
        print(f"OK {message}")
        print()
        print("Fixes applied:")
        print("  1. Changed certification duration check from >= 180 to > 180")
        print("  2. Changed product mix factor from accumulation to exclusive logic")
        print()
        print("The rebate calculation should now be correct per PRMS specification.")
        sys.exit(0)
    else:
        print(f"FAIL {message}")
        sys.exit(1)


if __name__ == "__main__":
    main()
