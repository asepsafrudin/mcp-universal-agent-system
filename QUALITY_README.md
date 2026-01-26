# Code Quality Standards

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
