#!/usr/bin/env python3
"""
Setup script untuk quality standards
Install pre-commit hooks dan konfigurasi quality monitoring
"""

import os
import shutil
from pathlib import Path

def setup_pre_commit_hook():
    """Setup pre-commit hook"""
    print("🔧 Setting up pre-commit hook...")

    # Git hooks directory
    hooks_dir = Path(".git/hooks")
    if not hooks_dir.exists():
        print("   ⚠️  .git directory not found. Is this a git repository?")
        return False

    # Pre-commit hook path
    pre_commit_hook = hooks_dir / "pre-commit"

    # Source script
    source_script = Path("scripts/pre-commit-hook.py")

    if not source_script.exists():
        print(f"   ❌ Pre-commit script not found: {source_script}")
        return False

    # Create hook script
    hook_content = f"""#!/bin/bash
# Auto-generated pre-commit hook
# Runs quality checks before commit

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$REPO_ROOT"
python scripts/pre-commit-hook.py

if [ $? -ne 0 ]; then
    echo "❌ Quality checks failed. Commit aborted."
    echo "💡 Fix the issues or use --no-verify to bypass"
    exit 1
fi

echo "✅ Quality checks passed. Proceeding with commit..."
"""

    try:
        with open(pre_commit_hook, 'w') as f:
            f.write(hook_content)

        # Make executable
        os.chmod(pre_commit_hook, 0o755)

        print(f"   ✅ Pre-commit hook installed: {pre_commit_hook}")
        return True

    except Exception as e:
        print(f"   ❌ Failed to install pre-commit hook: {e}")
        return False

def create_quality_config():
    """Create quality configuration file"""
    print("🔧 Creating quality configuration...")

    config_content = """# Quality Standards Configuration
# Configuration for automated quality monitoring

[quality]
# Minimum success rate for quality checks (0-100)
min_success_rate = 80

# Risk score thresholds
max_risk_score = 0.7
warning_risk_score = 0.5

# Code metrics thresholds
max_complexity = 30
max_loc = 300
max_dependencies = 15

# File patterns to include in checks
include_patterns = ["*.py"]
exclude_patterns = ["__pycache__/*", "*.pyc", ".git/*"]

# Security patterns to flag
dangerous_patterns = [
    "eval(",
    "exec(",
    "__import__(",
    "subprocess.call(",
    "os.system(",
    "input("
]

# Linting rules
max_line_length = 100
require_docstrings = true
allow_print_statements = false
"""

    config_path = Path(".qualityrc")
    try:
        with open(config_path, 'w') as f:
            f.write(config_content)

        print(f"   ✅ Quality config created: {config_path}")
        return True

    except Exception as e:
        print(f"   ❌ Failed to create quality config: {e}")
        return False

def create_quality_readme():
    """Create quality standards documentation"""
    print("🔧 Creating quality standards documentation...")

    readme_content = """# Code Quality Standards

## 🎯 Overview

This project implements automated code quality monitoring and review standards to maintain high code quality and reduce bug risk.

## 🛠️ Quality Tools

### Automated Checks
- **Syntax Validation**: Ensures Python code compiles without errors
- **Import Checks**: Validates all imports are resolvable
- **ML Risk Assessment**: Uses machine learning to predict bug likelihood
- **Security Scanning**: Detects potentially dangerous code patterns
- **Code Style Checks**: Enforces consistent formatting and practices

### Manual Reviews
- **Code Review Checklist**: Comprehensive checklist for peer reviews
- **Quality Gates**: Defined criteria for code acceptance

## 🚀 Quick Start

### Install Quality Standards
```bash
python scripts/setup_quality_standards.py
```

### Run Quality Checks
```bash
# Full quality monitoring
python scripts/quality_monitor.py

# ML audit only
cd crew && python audit_mcp_server.py

# Pre-commit checks (automatic)
git commit -m "Your commit message"
```

## 📊 Quality Metrics

### ML Risk Assessment
- **Low Risk (0.0-0.3)**: Code approved for production
- **Medium Risk (0.3-0.5)**: Code requires review
- **High Risk (0.5-0.7)**: Code needs refactoring
- **Critical Risk (0.7+)**: Code blocked from merge

### Code Metrics
- **Complexity**: Cyclomatic complexity score
- **Lines of Code**: Non-comment, non-empty lines
- **Dependencies**: Number of import statements

## 🔍 Pre-commit Hooks

Pre-commit hooks automatically run quality checks before each commit:

```bash
✅ Syntax Check
✅ Import Check
✅ Security Check
✅ Quality Monitor
```

To bypass checks (not recommended):
```bash
git commit --no-verify
```

## 📋 Code Review Process

### 1. Automated Checks
Run quality monitor and ensure all checks pass:
```bash
python scripts/quality_monitor.py
```

### 2. Manual Review
Use the code review checklist in `scripts/code_review_checklist.md`

### 3. Quality Gates
- ✅ **Pass**: All blocking issues resolved
- ⚠️ **Review**: Warning issues addressed
- ❌ **Fail**: Blocking issues present

## 🎛️ Configuration

Quality settings can be customized in `.qualityrc`:

```ini
[quality]
min_success_rate = 80
max_risk_score = 0.7
max_complexity = 30
```

## 📈 Continuous Improvement

- Quality reports are saved automatically
- Review findings inform process improvements
- ML model learns from code patterns
- Standards evolve based on project needs

## 🆘 Troubleshooting

### Pre-commit Hook Issues
```bash
# Check hook permissions
ls -la .git/hooks/pre-commit

# Reinstall hook
python scripts/setup_quality_standards.py
```

### Quality Monitor Failures
```bash
# Check Python environment
python --version

# Verify dependencies
pip list | grep pandas

# Run individual checks
python -c "import scripts.quality_monitor; print('Import OK')"
```

## 📞 Support

For quality standard questions:
1. Check this documentation
2. Review code review checklist
3. Consult team lead
4. Check recent quality reports

---

**Quality is not an act, it is a habit.** - Aristotle
"""

    readme_path = Path("QUALITY_README.md")
    try:
        with open(readme_path, 'w') as f:
            f.write(readme_content)

        print(f"   ✅ Quality README created: {readme_path}")
        return True

    except Exception as e:
        print(f"   ❌ Failed to create quality README: {e}")
        return False

def update_gitignore():
    """Update .gitignore for quality files"""
    print("🔧 Updating .gitignore...")

    gitignore_path = Path(".gitignore")
    quality_entries = [
        "\n# Quality monitoring",
        "quality_report_*.json",
        ".qualityrc",
    ]

    try:
        if gitignore_path.exists():
            content = gitignore_path.read_text()
            for entry in quality_entries:
                if entry not in content:
                    content += entry + "\n"
        else:
            content = "# Quality monitoring\n"
            content += "\n".join(quality_entries[1:]) + "\n"

        with open(gitignore_path, 'w') as f:
            f.write(content)

        print("   ✅ .gitignore updated")
        return True

    except Exception as e:
        print(f"   ❌ Failed to update .gitignore: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Code Quality Standards")
    print("=" * 50)

    setup_steps = [
        ("Install Pre-commit Hook", setup_pre_commit_hook),
        ("Create Quality Config", create_quality_config),
        ("Create Documentation", create_quality_readme),
        ("Update .gitignore", update_gitignore),
    ]

    completed_steps = []

    for step_name, step_func in setup_steps:
        print(f"\n📋 {step_name}...")
        try:
            if step_func():
                completed_steps.append(step_name)
                print(f"   ✅ {step_name} completed")
            else:
                print(f"   ❌ {step_name} failed")
        except Exception as e:
            print(f"   ❌ {step_name} failed with exception: {e}")

    print("\n" + "=" * 50)
    print("🎉 QUALITY STANDARDS SETUP COMPLETE!")
    print(f"✅ Completed: {len(completed_steps)}/{len(setup_steps)} steps")

    if len(completed_steps) == len(setup_steps):
        print("\n🚀 Next steps:")
        print("   1. Run quality monitor: python scripts/quality_monitor.py")
        print("   2. Make a test commit to verify pre-commit hooks")
        print("   3. Review QUALITY_README.md for detailed usage")
    else:
        print("\n⚠️  Some steps failed. You may need to:")
        print("   - Check file permissions")
        print("   - Ensure .git directory exists")
        print("   - Run setup as administrator if needed")

if __name__ == "__main__":
    main()
