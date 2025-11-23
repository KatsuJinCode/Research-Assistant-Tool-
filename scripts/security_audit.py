"""
Security Audit Script

Performs comprehensive security audit of the application.
Checks:
- Dependency vulnerabilities (safety)
- Code security issues (bandit)
- Configuration security
- Secrets exposure
- File permissions
- API security headers

Usage:
    python scripts/security_audit.py
    python scripts/security_audit.py --detailed
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.core.logging_config import setup_logging

logger = setup_logging("security_audit", log_level="INFO")


class SecurityAuditor:
    """Security audit manager"""

    def __init__(self):
        self.findings = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        self.timestamp = datetime.now().isoformat()

    def run_safety_check(self) -> Dict[str, Any]:
        """
        Check for known vulnerabilities in dependencies.

        Returns:
            Safety check results
        """
        logger.info("Running safety check for dependency vulnerabilities...")

        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                logger.info("✓ No known vulnerabilities found")
                return {
                    "status": "pass",
                    "vulnerabilities": []
                }

            # Parse vulnerabilities
            vulnerabilities = json.loads(result.stdout)

            logger.warning(f"⚠ Found {len(vulnerabilities)} vulnerabilities")

            for vuln in vulnerabilities:
                severity = vuln.get("severity", "medium").lower()
                self.findings[severity].append({
                    "type": "dependency_vulnerability",
                    "package": vuln.get("package"),
                    "version": vuln.get("installed_version"),
                    "vulnerability": vuln.get("vulnerability"),
                    "advisory": vuln.get("advisory")
                })

            return {
                "status": "fail",
                "vulnerabilities": vulnerabilities
            }

        except FileNotFoundError:
            logger.error("safety not installed. Install with: pip install safety")
            return {"status": "error", "message": "safety not installed"}
        except Exception as e:
            logger.error(f"Safety check failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def run_bandit_check(self) -> Dict[str, Any]:
        """
        Check code for security issues.

        Returns:
            Bandit check results
        """
        logger.info("Running bandit for code security issues...")

        try:
            # Run bandit
            result = subprocess.run(
                ["bandit", "-r", "backend/", "web_ui/", "-f", "json"],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                results = json.loads(result.stdout)
                issues = results.get("results", [])

                if not issues:
                    logger.info("✓ No security issues found in code")
                    return {"status": "pass", "issues": []}

                logger.warning(f"⚠ Found {len(issues)} security issues")

                for issue in issues:
                    severity = issue.get("issue_severity", "MEDIUM").lower()
                    if severity == "undefined":
                        severity = "medium"

                    self.findings[severity].append({
                        "type": "code_security_issue",
                        "test_id": issue.get("test_id"),
                        "test_name": issue.get("test_name"),
                        "file": issue.get("filename"),
                        "line": issue.get("line_number"),
                        "code": issue.get("code"),
                        "severity": issue.get("issue_severity"),
                        "confidence": issue.get("issue_confidence")
                    })

                return {"status": "warn", "issues": issues}

        except FileNotFoundError:
            logger.error("bandit not installed. Install with: pip install bandit")
            return {"status": "error", "message": "bandit not installed"}
        except Exception as e:
            logger.error(f"Bandit check failed: {str(e)}")
            return {"status": "error", "message": str(e)}

    def check_secrets_exposure(self) -> Dict[str, Any]:
        """
        Check for exposed secrets in code.

        Returns:
            Secrets check results
        """
        logger.info("Checking for exposed secrets...")

        secret_patterns = [
            "password",
            "api_key",
            "secret",
            "token",
            "private_key"
        ]

        exposed_secrets = []

        # Check key files
        files_to_check = [
            ".env",
            ".env.local",
            "config.py",
            "settings.py"
        ]

        for file_pattern in files_to_check:
            for file_path in Path(".").rglob(file_pattern):
                if file_path.is_file() and not str(file_path).startswith(".git"):
                    try:
                        content = file_path.read_text()
                        for pattern in secret_patterns:
                            if pattern in content.lower():
                                exposed_secrets.append({
                                    "file": str(file_path),
                                    "pattern": pattern
                                })
                    except:
                        pass

        if exposed_secrets:
            logger.warning(f"⚠ Found {len(exposed_secrets)} potential secret exposures")
            for secret in exposed_secrets:
                self.findings["medium"].append({
                    "type": "potential_secret_exposure",
                    "file": secret["file"],
                    "pattern": secret["pattern"]
                })
            return {"status": "warn", "exposures": exposed_secrets}

        logger.info("✓ No secrets exposure detected")
        return {"status": "pass", "exposures": []}

    def check_configuration_security(self) -> Dict[str, Any]:
        """
        Check security configuration.

        Returns:
            Configuration check results
        """
        logger.info("Checking security configuration...")

        issues = []

        # Check Docker configuration
        dockerfile_path = Path("Dockerfile")
        if dockerfile_path.exists():
            content = dockerfile_path.read_text()

            # Check for running as root
            if "USER root" in content:
                issues.append({
                    "file": "Dockerfile",
                    "issue": "Running as root user",
                    "recommendation": "Use non-root user"
                })

        # Check docker-compose security
        compose_path = Path("docker-compose.yml")
        if compose_path.exists():
            content = compose_path.read_text()

            # Check for default passwords
            if "password" in content.lower() and "password:" in content.lower():
                issues.append({
                    "file": "docker-compose.yml",
                    "issue": "Default passwords detected",
                    "recommendation": "Use environment variables for passwords"
                })

        if issues:
            logger.warning(f"⚠ Found {len(issues)} configuration issues")
            for issue in issues:
                self.findings["medium"].append({
                    "type": "configuration_issue",
                    **issue
                })
            return {"status": "warn", "issues": issues}

        logger.info("✓ Configuration security checks passed")
        return {"status": "pass", "issues": []}

    def check_file_permissions(self) -> Dict[str, Any]:
        """
        Check sensitive file permissions.

        Returns:
            File permission check results
        """
        logger.info("Checking file permissions...")

        issues = []

        # Files that should have restricted permissions
        sensitive_files = [
            ".env",
            ".env.local",
            "config.py",
            "secrets.json"
        ]

        for filename in sensitive_files:
            for file_path in Path(".").rglob(filename):
                if file_path.is_file():
                    # Check permissions (Unix-like systems only)
                    try:
                        mode = file_path.stat().st_mode
                        # Check if file is world-readable (o+r)
                        if mode & 0o004:
                            issues.append({
                                "file": str(file_path),
                                "issue": "File is world-readable",
                                "recommendation": "chmod 600 or 640"
                            })
                    except:
                        pass

        if issues:
            logger.warning(f"⚠ Found {len(issues)} file permission issues")
            for issue in issues:
                self.findings["low"].append({
                    "type": "file_permission_issue",
                    **issue
                })
            return {"status": "warn", "issues": issues}

        logger.info("✓ File permission checks passed")
        return {"status": "pass", "issues": []}

    def generate_report(self, output_file: str = "security_report.json"):
        """
        Generate security audit report.

        Args:
            output_file: Output file path
        """
        logger.info(f"Generating security report: {output_file}")

        # Count findings by severity
        total_findings = sum(len(findings) for findings in self.findings.values())

        report = {
            "timestamp": self.timestamp,
            "total_findings": total_findings,
            "findings_by_severity": {
                severity: len(findings)
                for severity, findings in self.findings.items()
            },
            "findings": self.findings,
            "summary": {
                "critical_issues": len(self.findings["critical"]),
                "high_issues": len(self.findings["high"]),
                "medium_issues": len(self.findings["medium"]),
                "low_issues": len(self.findings["low"]),
                "info_items": len(self.findings["info"])
            },
            "recommendations": self.get_recommendations()
        }

        # Save report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_path}")

        # Print summary
        self.print_summary(report)

    def get_recommendations(self) -> List[str]:
        """Get security recommendations based on findings"""
        recommendations = []

        if self.findings["critical"]:
            recommendations.append("⚠️ CRITICAL: Address critical security issues immediately")

        if self.findings["high"]:
            recommendations.append("⚠️ HIGH: Review and fix high-priority security issues")

        if self.findings["medium"]:
            recommendations.append("Review and address medium-priority issues")

        recommendations.extend([
            "Keep dependencies up to date",
            "Use environment variables for secrets",
            "Enable security headers in production",
            "Implement rate limiting",
            "Use HTTPS in production",
            "Regular security audits"
        ])

        return recommendations

    def print_summary(self, report: Dict):
        """Print security summary to console"""
        print("\n" + "=" * 60)
        print("SECURITY AUDIT SUMMARY")
        print("=" * 60)

        summary = report["summary"]
        print(f"\nTotal Findings: {report['total_findings']}")
        print(f"  Critical: {summary['critical_issues']}")
        print(f"  High:     {summary['high_issues']}")
        print(f"  Medium:   {summary['medium_issues']}")
        print(f"  Low:      {summary['low_issues']}")

        if summary["critical_issues"] > 0 or summary["high_issues"] > 0:
            print("\n⚠️  WARNING: Critical or high-priority issues found!")
            print("   Review the security report immediately.")

        print("\n" + "=" * 60)
        print("RECOMMENDATIONS")
        print("=" * 60)

        for i, rec in enumerate(report["recommendations"], 1):
            print(f"{i}. {rec}")

        print("\n" + "=" * 60)


def main():
    """Main security audit script"""
    import argparse

    parser = argparse.ArgumentParser(description="Security audit utility")
    parser.add_argument(
        "--detailed",
        action="store_true",
        help="Run detailed audit (slower)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="security_report.json",
        help="Output file (default: security_report.json)"
    )

    args = parser.parse_args()

    auditor = SecurityAuditor()

    try:
        # Run all security checks
        auditor.run_safety_check()
        auditor.run_bandit_check()
        auditor.check_secrets_exposure()
        auditor.check_configuration_security()
        auditor.check_file_permissions()

        # Generate report
        auditor.generate_report(args.output)

        # Exit with error code if critical/high issues found
        if auditor.findings["critical"] or auditor.findings["high"]:
            logger.error("Security audit found critical or high-priority issues")
            sys.exit(1)

        logger.info("Security audit completed successfully")
        sys.exit(0)

    except Exception as e:
        logger.error(f"Security audit failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
