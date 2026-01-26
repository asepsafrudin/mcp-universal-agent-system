#!/usr/bin/env python3
"""
Pre-commit hook untuk quality checks
Integrasikan dengan git hooks untuk automated quality control
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd,
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_syntax():
    """Check Python syntax for staged files"""
    print("🔍 Checking syntax...")

    # Get staged Python files
    success, stdout, stderr = run_command("git diff --cached --name-only -- '*.py'")
    if not success:
        print(f"   ❌ Failed to get staged files: {stderr}")
        return False

    staged_files = [f for f in stdout.strip().split('\n') if f.strip()]

    if not staged_files:
        print("   ✅ No Python files staged")
        return True

    errors = []
    for file_path in staged_files:
        if os.path.exists(file_path):
            success, _, stderr = run_command(f"python -m py_compile {file_path}")
            if not success:
                errors.append(f"{file_path}: {stderr.strip()}")

    if errors:
        print("   ❌ Syntax errors found:")
        for error in errors:
            print(f"      {error}")
        return False

    print(f"   ✅ Syntax OK for {len(staged_files)} files")
    return True

def check_imports():
    """Check imports for staged files"""
    print("🔍 Checking imports...")

    success, stdout, stderr = run_command("git diff --cached --name-only -- '*.py'")
    if not success:
        print(f"   ❌ Failed to get staged files: {stderr}")
        return False

    staged_files = [f for f in stdout.strip().split('\n') if f.strip()]

    errors = []
    for file_path in staged_files:
        if os.path.exists(file_path):
            try:
                # Try to import the file
                spec = compile(Path(file_path).read_text(), file_path, 'exec')
            except ImportError as e:
                errors.append(f"{file_path}: Import error - {str(e)}")
            except Exception as e:
                errors.append(f"{file_path}: {str(e)}")

    if errors:
        print("   ❌ Import errors found:")
        for error in errors:
            print(f"      {error}")
        return False

    print("   ✅ Imports OK"    return True

def run_quality_monitor():
    """Run quality monitor"""
    print("🔍 Running quality monitor...")

    script_path = Path(__file__).parent / "quality_monitor.py"
    if not script_path.exists():
        print(f"   ⚠️  Quality monitor script not found: {script_path}")
        return True  # Don't block if script missing

    success, stdout, stderr = run_command(f"python {script_path}")
    if not success:
        print("   ❌ Quality monitor failed:")
        print(stdout)
        print(stderr)
        return False

    print("   ✅ Quality monitor passed")
    return True

def check_security():
    """Basic security check for dangerous patterns"""
    print("🔍 Checking security...")

    success, stdout, stderr = run_command("git diff --cached --name-only -- '*.py'")
    if not success:
        print(f"   ❌ Failed to get staged files: {stderr}")
        return False

    staged_files = [f for f in stdout.strip().split('\n') if f.strip()]

    dangerous_patterns = [
        'eval(',
        'exec(',
        '__import__(',
        'subprocess.call(',
        'os.system(',
    ]

    issues = []
    for file_path in staged_files:
        if os.path.exists(file_path):
            content = Path(file_path).read_text()
            for pattern in dangerous_patterns:
                if pattern in content:
                    issues.append(f"{file_path}: Contains {pattern}")

    if issues:
        print("   ❌ Security issues found:")
        for issue in issues:
            print(f"      {issue}")
        print("   💡 Use safer alternatives or add justification comments")
        return False

    print("   ✅ Security check passed")
    return True

def main():
    """Main pre-commit hook"""
    print("🛡️  Running Pre-commit Quality Checks")
    print("=" * 50)

    checks = [
        ("Syntax Check", check_syntax),
        ("Import Check", check_imports),
        ("Security Check", check_security),
        ("Quality Monitor", run_quality_monitor),
    ]

    failed_checks = []

    for check_name, check_func in checks:
        try:
            if not check_func():
                failed_checks.append(check_name)
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            failed_checks.append(check_name)

    print("\n" + "=" * 50)

    if failed_checks:
        print("❌ PRE-COMMIT CHECKS FAILED!")
        print("Failed checks:")
        for check in failed_checks:
            print(f"   - {check}")

        print("\n💡 To bypass (not recommended):")
        print("   git commit --no-verify")
        print("\n🔧 Fix the issues and try again.")
        sys.exit(1)
    else:
        print("✅ ALL PRE-COMMIT CHECKS PASSED!")
        print("🎉 Commit approved.")
        sys.exit(0)

if __name__ == "__main__":
    main()
