#!/usr/bin/env python3
"""
Code Quality Monitoring Script
Menjalankan berbagai checks kualitas kode secara otomatis
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

class CodeQualityMonitor:
    """Monitor kualitas kode dengan multiple checks"""

    def __init__(self, project_root=None):
        self.project_root = Path(project_root or Path(__file__).parent.parent)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {},
            "summary": {}
        }

    def run_all_checks(self):
        """Jalankan semua quality checks"""
        print("🔍 Running Code Quality Monitoring...")
        print("=" * 50)

        checks = [
            ("syntax_check", self.check_syntax),
            ("import_check", self.check_imports),
            ("complexity_audit", self.run_ml_audit),
            ("linting", self.run_linting),
            ("security_scan", self.security_scan),
        ]

        passed = 0
        total = len(checks)

        for check_name, check_func in checks:
            print(f"\n📋 Running {check_name}...")
            try:
                result = check_func()
                self.results["checks"][check_name] = result
                if result.get("status") == "PASS":
                    passed += 1
                    print(f"   ✅ {check_name}: PASS")
                else:
                    print(f"   ❌ {check_name}: FAIL - {result.get('message', 'Unknown error')}")
            except Exception as e:
                self.results["checks"][check_name] = {
                    "status": "ERROR",
                    "message": str(e)
                }
                print(f"   ❌ {check_name}: ERROR - {str(e)}")

        # Summary
        self.results["summary"] = {
            "total_checks": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total)*100:.1f}%" if total > 0 else "0%"
        }

        print("\n📊 SUMMARY:")
        print(f"   Total Checks: {total}")
        print(f"   Passed: {passed}")
        print(f"   Failed: {total - passed}")
        print(f"   Success Rate: {self.results['summary']['success_rate']}")

        return self.results

    def check_syntax(self):
        """Check Python syntax"""
        python_files = list(self.project_root.rglob("*.py"))
        errors = []
        checked_files = 0

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                compile(content, str(file_path), 'exec')
                checked_files += 1
            except UnicodeDecodeError:
                # Skip binary files
                continue
            except SyntaxError as e:
                errors.append(f"{file_path}: {e}")

        if errors:
            return {
                "status": "FAIL",
                "message": f"Syntax errors found: {len(errors)}",
                "details": errors
            }

        return {
            "status": "PASS",
            "message": f"All {checked_files} Python files have valid syntax"
        }

    def check_imports(self):
        """Check for import errors"""
        python_files = list(self.project_root.rglob("*.py"))
        import_errors = []
        checked_files = 0

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                # Try to compile the module
                compile(content, str(file_path), 'exec')
                checked_files += 1
            except UnicodeDecodeError:
                # Skip binary files
                continue
            except ImportError as e:
                import_errors.append(f"{file_path}: Import error - {str(e)}")
            except SyntaxError as e:
                # Syntax errors are handled by syntax check
                checked_files += 1
            except Exception as e:
                import_errors.append(f"{file_path}: {str(e)}")

        if import_errors:
            return {
                "status": "FAIL",
                "message": f"Import/compilation errors found: {len(import_errors)}",
                "details": import_errors
            }

        return {
            "status": "PASS",
            "message": f"All {checked_files} files compiled successfully"
        }

    def run_ml_audit(self):
        """Run ML-based code audit"""
        try:
            # Import the audit script
            sys.path.insert(0, str(self.project_root / "crew"))
            from audit_mcp_server import code_metrics_extractor, CodeMLAnalyzer

            # Audit MCP server
            mcp_server_path = self.project_root / "mcp-server" / "mcp_server.py"
            if not mcp_server_path.exists():
                return {
                    "status": "SKIP",
                    "message": "MCP server file not found"
                }

            analyzer = CodeMLAnalyzer()
            metrics = code_metrics_extractor(str(mcp_server_path))
            assessment = analyzer.analyze_risk(
                metrics['complexity'],
                metrics['loc'],
                metrics['dependencies']
            )

            if assessment['risk_score'] > 0.5:
                return {
                    "status": "WARN",
                    "message": f"High risk detected (score: {assessment['risk_score']})",
                    "details": assessment
                }

            return {
                "status": "PASS",
                "message": f"ML audit passed (score: {assessment['risk_score']})",
                "details": assessment
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"ML audit failed: {str(e)}"
            }

    def run_linting(self):
        """Run basic linting checks"""
        try:
            # Check for common issues
            python_files = list(self.project_root.rglob("*.py"))
            issues = []
            checked_files = 0

            for file_path in python_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    checked_files += 1

                    # Check for print statements (should use logging)
                    if 'print(' in content and 'main.py' not in str(file_path):
                        issues.append(f"{file_path}: Contains print statements")

                    # Check for TODO comments
                    if 'TODO' in content or 'FIXME' in content:
                        issues.append(f"{file_path}: Contains TODO/FIXME comments")

                    # Check for long lines (>100 chars)
                    long_lines = [i+1 for i, line in enumerate(content.split('\n'))
                                if len(line) > 100 and not line.strip().startswith('#')]
                    if long_lines:
                        issues.append(f"{file_path}: {len(long_lines)} lines > 100 characters")

                except UnicodeDecodeError:
                    # Skip binary files
                    continue

            if issues:
                return {
                    "status": "WARN",
                    "message": f"Code style issues found: {len(issues)}",
                    "details": issues
                }

            return {
                "status": "PASS",
                "message": f"No major code style issues found in {checked_files} files"
            }

        except Exception as e:
            return {
                "status": "ERROR",
                "message": f"Linting failed: {str(e)}"
            }

    def security_scan(self):
        """Basic security scan"""
        python_files = list(self.project_root.rglob("*.py"))
        security_issues = []
        checked_files = 0

        for file_path in python_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                checked_files += 1

                # Check for dangerous patterns
                dangerous_patterns = [
                    'eval(',
                    'exec(',
                    '__import__(',
                    'subprocess.call(',
                    'os.system(',
                    'input('  # Can be dangerous in some contexts
                ]

                for pattern in dangerous_patterns:
                    if pattern in content:
                        security_issues.append(f"{file_path}: Contains {pattern}")

            except UnicodeDecodeError:
                # Skip binary files
                continue

        if security_issues:
            return {
                "status": "FAIL",
                "message": f"Security issues found: {len(security_issues)}",
                "details": security_issues
            }

        return {
            "status": "PASS",
            "message": f"No obvious security issues found in {checked_files} files"
        }

    def save_report(self, output_path=None):
        """Save monitoring results to file"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.project_root / f"quality_report_{timestamp}.json"

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Report saved to: {output_path}")
        return output_path

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description="Code Quality Monitoring")
    parser.add_argument("--path", help="Project root path")
    parser.add_argument("--output", help="Output file path")

    args = parser.parse_args()

    monitor = CodeQualityMonitor(args.path)
    results = monitor.run_all_checks()
    report_path = monitor.save_report(args.output)

    # Exit with appropriate code
    success_rate = float(results["summary"]["success_rate"].rstrip('%'))
    sys.exit(0 if success_rate >= 80 else 1)

if __name__ == "__main__":
    main()
