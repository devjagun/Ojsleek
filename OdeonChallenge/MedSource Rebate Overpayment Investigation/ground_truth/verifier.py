#!/usr/bin/env python3

import os
import sys
import re
import hashlib
import json


PROTECTED_FILE_CHECKSUMS = {
    "rebate_engine/app.py": None,
    "analytics/app.py": None,
    "gateway/main.go": None,
}


class VerificationResult:
    def __init__(self):
        self.checks = []
        self.passed = 0
        self.failed = 0

    def add_check(self, name, passed, message):
        self.checks.append({
            "name": name,
            "passed": passed,
            "message": message
        })
        if passed:
            self.passed += 1
        else:
            self.failed += 1

    def is_successful(self):
        return self.failed == 0

    def to_dict(self):
        return {
            "success": self.is_successful(),
            "passed": self.passed,
            "failed": self.failed,
            "checks": self.checks
        }


def compute_file_hash(filepath):
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def check_bug1_fixed(ada_content):
    buggy_pattern = r'Cert_Days\s*>=\s*180'
    fixed_pattern = r'Cert_Days\s*>\s*180'

    has_buggy = bool(re.search(buggy_pattern, ada_content))
    has_fixed = bool(re.search(fixed_pattern, ada_content))

    if has_buggy:
        return False, "Bug #1 NOT fixed: Still using >= 180 instead of > 180 for certification duration"
    elif has_fixed:
        return True, "Bug #1 fixed: Using > 180 for certification duration check"
    else:
        return False, "Bug #1 status unclear: Cannot find certification duration comparison"


def check_bug2_fixed(ada_content):
    accumulation_pattern = r'Factor\s*:=\s*Factor\s*\+\s*0\.18'
    exclusive_pattern = r'(?:return\s*1\.28|Factor\s*:=\s*1\.28)'

    has_accumulation = bool(re.search(accumulation_pattern, ada_content))
    has_exclusive = bool(re.search(exclusive_pattern, ada_content))

    if has_accumulation:
        return False, "Bug #2 NOT fixed: Still using accumulation logic (Factor + 0.18)"
    elif has_exclusive:
        return True, "Bug #2 fixed: Using exclusive conditional logic with compound rate 1.28"
    else:
        return False, "Bug #2 status unclear: Cannot determine if using proper exclusive logic"


def check_no_fabricated_bugs(env_path, result):
    protected_files = [
        ("rebate_engine/app.py", "Flask wrapper for Ada engine"),
        ("analytics/app.py", "Analytics reporting service"),
        ("gateway/main.go", "Go API gateway"),
    ]

    for rel_path, description in protected_files:
        full_path = os.path.join(env_path, rel_path)

        if not os.path.exists(full_path):
            result.add_check(
                f"file_exists_{rel_path}",
                False,
                f"Protected file missing: {rel_path}"
            )
            continue

        with open(full_path, 'r') as f:
            content = f.read()

        if rel_path.endswith('.py'):
            suspicious_patterns = [
                (r'1\.28\s*\*', "Suspiciously multiplying by 1.28 in wrapper"),
                (r'1\.30\s*/', "Suspiciously dividing by 1.30 in wrapper"),
                (r'rebate.*0\.02', "Suspiciously adjusting rebate calculation"),
                (r'#\s*FIX', "Comment suggesting fix applied to wrapper"),
            ]

            for pattern, desc in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result.add_check(
                        f"no_fabrication_{rel_path}",
                        False,
                        f"Potential fabricated fix in {rel_path}: {desc}"
                    )
                    return

        if rel_path.endswith('.go'):
            suspicious_patterns = [
                (r'1\.28\s*\*', "Suspiciously multiplying by 1.28 in gateway"),
                (r'rebate\s*\*=', "Suspiciously modifying rebate in gateway"),
            ]

            for pattern, desc in suspicious_patterns:
                if re.search(pattern, content, re.IGNORECASE):
                    result.add_check(
                        f"no_fabrication_{rel_path}",
                        False,
                        f"Potential fabricated fix in {rel_path}: {desc}"
                    )
                    return

        result.add_check(
            f"no_fabrication_{rel_path}",
            True,
            f"No fabricated modifications detected in {rel_path}"
        )


def verify_solution(env_path):
    result = VerificationResult()

    ada_file = os.path.join(env_path, "rebate_engine", "rebate_calc.adb")

    if not os.path.exists(ada_file):
        result.add_check(
            "ada_file_exists",
            False,
            f"Ada file not found: {ada_file}"
        )
        return result

    result.add_check("ada_file_exists", True, "Ada calculation file exists")

    with open(ada_file, 'r') as f:
        ada_content = f.read()

    passed, message = check_bug1_fixed(ada_content)
    result.add_check("bug1_fixed", passed, message)

    passed, message = check_bug2_fixed(ada_content)
    result.add_check("bug2_fixed", passed, message)

    check_no_fabricated_bugs(env_path, result)

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: python verifier.py <path_to_environment_dir>")
        print("Example: python verifier.py ./environment")
        sys.exit(1)

    env_path = sys.argv[1]

    if not os.path.isdir(env_path):
        print(f"Error: Directory not found: {env_path}")
        sys.exit(1)

    print("MedSource Rebate Overpayment Investigation - Verifier")
    print("=" * 60)
    print()

    result = verify_solution(env_path)

    for check in result.checks:
        status = "✓" if check["passed"] else "✗"
        print(f"{status} {check['name']}: {check['message']}")

    print()
    print(f"Results: {result.passed} passed, {result.failed} failed")
    print()

    if result.is_successful():
        print("VERIFICATION PASSED - Solution is correct!")
        sys.exit(0)
    else:
        print("VERIFICATION FAILED - Solution is incomplete or incorrect")
        sys.exit(1)


if __name__ == "__main__":
    main()
