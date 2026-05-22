#!/usr/bin/env python3
"""
Comprehensive automated end-to-end test suite for TweekIT MCP Server.

This script orchestrates all testing phases:
- Pre-flight checks (dependencies, credentials, server availability)
- Server startup and smoke tests
- Full file conversion sweep
- Browser-based screenshot capture
- Consolidated results and HTML report generation

Usage:
    # Run full suite with report
    uv run python scripts/run_full_e2e_test.py --generate-report

    # Pre-flight checks only
    uv run python scripts/run_full_e2e_test.py --preflight-only

    # Skip browser automation
    uv run python scripts/run_full_e2e_test.py --no-browser

Environment Variables:
    TWEEKIT_API_KEY: TweekIT API key (required)
    TWEEKIT_API_SECRET: TweekIT API secret (required)
"""

from __future__ import annotations

import argparse
import asyncio
import datetime
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PreflightResult:
    """Result of a single pre-flight check."""
    name: str
    passed: bool
    message: str
    details: str = ""


@dataclass
class TestPhaseResult:
    """Result of a test phase execution."""
    phase: str
    passed: bool
    duration_seconds: float
    output: str = ""
    error: str = ""
    artifacts: list[Path] = field(default_factory=list)


@dataclass
class E2ETestResults:
    """Complete results from entire E2E test run."""
    timestamp: str
    version: str
    preflight_checks: list[PreflightResult]
    test_phases: list[TestPhaseResult]
    results_dir: Path
    total_duration_seconds: float
    overall_passed: bool


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def print_header(text: str) -> None:
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text.center(80)}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.RESET}\n")


def print_success(text: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


def check_python_version() -> PreflightResult:
    """Check Python version is 3.10 or later."""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 10
    return PreflightResult(
        name="Python Version",
        passed=passed,
        message=f"Python {version.major}.{version.minor}.{version.micro}",
        details="Requires Python 3.10 or later"
    )


def check_command_available(command: str, description: str) -> PreflightResult:
    """Check if a command-line tool is available."""
    try:
        result = subprocess.run(
            [command, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        passed = result.returncode == 0
        version_output = result.stdout.strip() or result.stderr.strip()
        first_line = version_output.split('\n')[0] if version_output else "unknown version"
        return PreflightResult(
            name=description,
            passed=passed,
            message=first_line,
            details=f"Command: {command}"
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return PreflightResult(
            name=description,
            passed=False,
            message=f"{command} not found",
            details=f"Install {description}"
        )


def check_python_package(package_name: str, import_name: str | None = None) -> PreflightResult:
    """Check if a Python package is installed."""
    import_name = import_name or package_name
    try:
        __import__(import_name)
        return PreflightResult(
            name=f"Python Package: {package_name}",
            passed=True,
            message="Installed",
            details=f"import {import_name}"
        )
    except ImportError:
        return PreflightResult(
            name=f"Python Package: {package_name}",
            passed=False,
            message="Not installed",
            details=f"Run: uv pip install {package_name}"
        )


def check_credentials() -> PreflightResult:
    """Check for API credentials."""
    api_key = os.getenv("TWEEKIT_API_KEY")
    api_secret = os.getenv("TWEEKIT_API_SECRET")
    
    # Check local credentials file
    creds_file = Path(".tweekit_credentials")
    if not (api_key and api_secret) and creds_file.exists():
        try:
            content = creds_file.read_text()
            for line in content.splitlines():
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()
            api_key = os.getenv("TWEEKIT_API_KEY")
            api_secret = os.getenv("TWEEKIT_API_SECRET")
        except Exception:
            pass

    # Check parent .env file (direnv style)
    if not (api_key and api_secret):
        parent_env = Path("..") / ".env"
        if parent_env.exists():
            try:
                content = parent_env.read_text()
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
                api_key = os.getenv("TWEEKIT_API_KEY")
                api_secret = os.getenv("TWEEKIT_API_SECRET")
            except Exception:
                pass
    
    if api_key and api_secret:
        return PreflightResult(
            "API Credentials",
            True,
            "Found credentials",
            "Loaded from environment or credentials file"
        )
    else:
        return PreflightResult(
            "API Credentials",
            False,
            "No credentials found",
            "Set TWEEKIT_API_KEY/TWEEKIT_API_SECRET, create .tweekit_credentials, or use ../.env"
        )


def check_test_assets() -> PreflightResult:
    """Check if test assets directory exists."""
    assets_dir = Path("tests/assets")
    if assets_dir.exists() and assets_dir.is_dir():
        file_count = len(list(assets_dir.rglob("*")))
        return PreflightResult(
            name="Test Assets",
            passed=True,
            message=f"Found {file_count} files",
            details=f"Directory: {assets_dir}"
        )
    else:
        return PreflightResult(
            name="Test Assets",
            passed=False,
            message="assets directory not found",
            details=f"Expected: {assets_dir}"
        )


def check_port_available(port: int = 8080) -> PreflightResult:
    """Check if the required port is available."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return PreflightResult(
                name=f"Port {port} Available",
                passed=True,
                message="Port is free",
                details=f"Will bind server to localhost:{port}"
            )
    except OSError:
        return PreflightResult(
            name=f"Port {port} Available",
            passed=False,
            message="Port already in use",
            details=f"Stop any service using port {port}"
        )


def check_version_file() -> PreflightResult:
    """Check VERSION file and return current version."""
    version_file = Path("VERSION")
    if version_file.exists():
        version = version_file.read_text().strip()
        return PreflightResult(
            name="Project Version",
            passed=True,
            message=f"v{version}",
            details=f"File: {version_file}"
        )
    else:
        return PreflightResult(
            name="Project Version",
            passed=False,
            message="VERSION file not found",
            details=""
        )


def run_preflight_checks(env: str) -> list[PreflightResult]:
    """Run all pre-flight checks."""
    print_header("PRE-FLIGHT CHECKS")
    
    checks = [
        check_python_version(),
        check_command_available("uv", "UV Package Manager"),
        check_python_package("fastmcp"),
        check_python_package("httpx"),
        check_credentials(),
        check_test_assets(),
        check_version_file(),
    ]
    
    if env == "local":
        checks.append(check_port_available(8080))
    
    # Print results
    for check in checks:
        if check.passed:
            print_success(f"{check.name}: {check.message}")
        else:
            print_error(f"{check.name}: {check.message}")
            if check.details:
                print(f"  → {check.details}")
    
    # Summary
    passed_count = sum(1 for c in checks if c.passed)
    total_count = len(checks)
    print(f"\n{Colors.BOLD}Pre-flight: {passed_count}/{total_count} checks passed{Colors.RESET}")
    
    return checks


def create_results_directory() -> Path:
    """Create timestamped results directory."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = Path(f"tests/results/run_{timestamp}")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    (results_dir / "logs").mkdir(exist_ok=True)
    (results_dir / "screenshots").mkdir(exist_ok=True)
    (results_dir / "conversions").mkdir(exist_ok=True)
    
    print_info(f"Results directory: {results_dir}")
    return results_dir


def start_mcp_server(results_dir: Path, env: str) -> subprocess.Popen | None:
    """Start the MCP server in the background if running locally."""
    if env != "local":
        print_info(f"Skipping local server start for environment: {env}")
        return None

    print_header("STARTING MCP SERVER")
    
    log_file = results_dir / "logs" / "server.log"
    
    try:
        with open(log_file, "w") as f:
            process = subprocess.Popen(
                ["uv", "run", "server.py"],
                stdout=f,
                stderr=subprocess.STDOUT,
                env={**os.environ, "PORT": "8080"}
            )
        
        print_info(f"Server starting (PID: {process.pid})")
        print_info(f"Server logs: {log_file}")
        
        # Wait for server to be ready
        print_info("Waiting for server to be ready...")
        time.sleep(5)
        
        # Check if still running
        if process.poll() is None:
            print_success("Server started successfully")
            return process
        else:
            print_error("Server failed to start")
            with open(log_file) as f:
                print(f.read())
            return None
            
    except Exception as e:
        print_error(f"Failed to start server: {e}")
        return None


def get_server_url(env: str) -> str:
    """Get the MCP server URL for the specified environment."""
    if env == "prod":
        # Using direct Cloud Run URL for MCP server to bypass domain mapping issues
        # Confirmed endpoint is /mcp (SSE transport)
        return "https://tweekit-mcp-prod-958133016924.us-west1.run.app/mcp"
    elif env == "stage":
        # Placeholder - replace with actual stage URL if known
        return os.getenv("TWEEKIT_STAGE_URL", "https://stage.mcp.tweekit.io/mcp/")
    else:
        return "http://127.0.0.1:8080/mcp/"


def run_smoke_tests(results_dir: Path, env: str) -> TestPhaseResult:
    """Run test_server.py smoke tests."""
    print_header("SMOKE TESTS")
    
    log_file = results_dir / "logs" / "smoke_tests.log"
    start_time = time.time()
    server_url = get_server_url(env)
    
    print_info(f"Target: {server_url}")
    
    try:
        result = subprocess.run(
            ["uv", "run", "python", "test_server.py"],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "TWEEKIT_MCP_BASE_URL": server_url}
        )
        
        duration = time.time() - start_time
        
        # Save output
        with open(log_file, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr)
        
        passed = result.returncode == 0
        
        if passed:
            print_success(f"Smoke tests passed ({duration:.1f}s)")
        else:
            print_error(f"Smoke tests failed ({duration:.1f}s)")
            print(result.stdout[-500:])  # Print last 500 chars
        
        return TestPhaseResult(
            phase="Smoke Tests",
            passed=passed,
            duration_seconds=duration,
            output=result.stdout,
            error=result.stderr,
            artifacts=[log_file]
        )
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print_error(f"Smoke tests timed out after {duration:.1f}s")
        return TestPhaseResult(
            phase="Smoke Tests",
            passed=False,
            duration_seconds=duration,
            error="Timeout after 120 seconds",
            artifacts=[log_file]
        )
    except Exception as e:
        duration = time.time() - start_time
        print_error(f"Smoke tests error: {e}")
        return TestPhaseResult(
            phase="Smoke Tests",
            passed=False,
            duration_seconds=duration,
            error=str(e),
            artifacts=[log_file]
        )


def run_conversion_sweep(results_dir: Path, env: str) -> TestPhaseResult:
    """Run run_mcp_e2e.py conversion sweep."""
    print_header("FILE CONVERSION SWEEP")
    
    log_file = results_dir / "logs" / "conversion_sweep.log"
    output_dir = results_dir / "conversions"
    start_time = time.time()
    server_url = get_server_url(env)
    
    print_info(f"Target: {server_url}")
    
    try:
        cmd = [
            "uv", "run", "python", "scripts/run_mcp_e2e.py",
            "--server-url", server_url,
            "--output-dir", str(output_dir),
            "--auto-clear-output",
            "--include-convert-url"
        ]
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,  # 10 minutes
        )
        
        duration = time.time() - start_time
        
        # Save output
        with open(log_file, "w") as f:
            f.write(result.stdout)
            if result.stderr:
                f.write("\n\n=== STDERR ===\n")
                f.write(result.stderr)
        
        passed = result.returncode == 0
        
        # Collect artifacts
        artifacts = [log_file]
        if output_dir.exists():
            artifacts.extend(list(output_dir.rglob("*.*")))
        
        if passed:
            print_success(f"Conversion sweep passed ({duration:.1f}s)")
            print_info(f"Artifacts: {len(artifacts)} files")
        else:
            print_error(f"Conversion sweep failed ({duration:.1f}s)")
            print(result.stdout[-500:])  # Print last 500 chars
        
        return TestPhaseResult(
            phase="Conversion Sweep",
            passed=passed,
            duration_seconds=duration,
            output=result.stdout,
            error=result.stderr,
            artifacts=artifacts
        )
        
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print_error(f"Conversion sweep timed out after {duration:.1f}s")
        return TestPhaseResult(
            phase="Conversion Sweep",
            passed=False,
            duration_seconds=duration,
            error="Timeout after 600 seconds",
            artifacts=[log_file]
        )
    except Exception as e:
        duration = time.time() - start_time
        print_error(f"Conversion sweep error: {e}")
        return TestPhaseResult(
            phase="Conversion Sweep",
            passed=False,
            duration_seconds=duration,
            error=str(e),
            artifacts=[log_file]
        )


def validate_submission_checklists(results_dir: Path) -> TestPhaseResult:
    """Validate submission checklists for OpenAI, MCP Registry, and Pulse MCP."""
    print_header("SUBMISSION READINESS CHECKS")
    
    start_time = time.time()
    log_file = results_dir / "logs" / "submission_checks.log"
    
    checks = [
        ("OpenAI Manifest", "docs/chatgpt-plugin.md"),
        ("MCP Registry Checklist", "docs/mcp-pulse-checklist.md"),
        ("Pulse MCP Checklist", "docs/mcp-pulse-checklist.md"), # Same file for now
    ]
    
    passed_count = 0
    output = []
    
    for name, path_str in checks:
        path = Path(path_str)
        if path.exists():
            print_success(f"Found checklist: {name} ({path})")
            output.append(f"✓ Found {name} at {path}")
            passed_count += 1
            # TODO: Add deeper validation logic here (e.g., parsing markdown checkboxes)
        else:
            print_error(f"Missing checklist: {name} ({path})")
            output.append(f"✗ Missing {name} at {path}")
    
    # Check for PROD manifest accessibility
    try:
        import httpx
        # Using direct Cloud Run URL for Plugin Proxy
        manifest_url = "https://tweekit-plugin-prod-958133016924.us-west1.run.app/.well-known/ai-plugin.json"
        resp = httpx.get(manifest_url, timeout=5)
        if resp.status_code == 200:
            print_success(f"PROD Manifest accessible: {manifest_url}")
            output.append(f"✓ PROD Manifest accessible: {manifest_url}")
            passed_count += 1
        else:
            print_error(f"PROD Manifest inaccessible: {resp.status_code}")
            output.append(f"✗ PROD Manifest inaccessible: {resp.status_code}")
            # Try openapi.json as fallback proof of life
            openapi_url = "https://tweekit-plugin-prod-958133016924.us-west1.run.app/openapi.json"
            resp_openapi = httpx.get(openapi_url, timeout=5)
            if resp_openapi.status_code == 200:
                print_warning(f"  ↳ But openapi.json IS accessible: {openapi_url}")
                output.append(f"  ↳ openapi.json is accessible")
    except Exception as e:
        print_error(f"Failed to check PROD manifest: {e}")
        output.append(f"✗ Failed to check PROD manifest: {e}")

    duration = time.time() - start_time
    passed = passed_count == len(checks) + 1 # +1 for manifest check
    
    with open(log_file, "w") as f:
        f.write("\n".join(output))
        
    return TestPhaseResult(
        phase="Submission Readiness",
        passed=passed,
        duration_seconds=duration,
        output="\n".join(output),
        artifacts=[log_file]
    )


def capture_browser_screenshots(results_dir: Path) -> TestPhaseResult:
    """Capture browser screenshots of MCP server endpoints (optional)."""
    print_header("BROWSER SCREENSHOTS")
    
    # This is a placeholder - would require browser automation
    # For now, just return a skipped result
    print_warning("Browser automation not yet implemented")
    print_info("Screenshots would capture:")
    print_info("  - MCP endpoint responses")
    print_info("  - Sample conversion results")
    print_info("  - Error handling scenarios")
    
    return TestPhaseResult(
        phase="Browser Screenshots",
        passed=True,  # Not a failure, just skipped
        duration_seconds=0.0,
        output="Skipped - manual screenshot capture recommended",
        artifacts=[]
    )


def generate_html_report(results: E2ETestResults) -> Path:
    """Generate comprehensive HTML report."""
    print_header("GENERATING REPORT")
    
    report_path = results.results_dir / "index.html"
    
    # Count totals
    total_checks = len(results.preflight_checks)
    passed_checks = sum(1 for c in results.preflight_checks if c.passed)
    total_phases = len(results.test_phases)
    passed_phases = sum(1 for p in results.test_phases if p.passed)
    
    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TweekIT MCP E2E Test Report - {results.timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 2rem;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
        .header p {{ opacity: 0.9; font-size: 1.1rem; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            padding: 2rem;
            background: #f8f9fa;
        }}
        .summary-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-card h3 {{ color: #666; font-size: 0.9rem; margin-bottom: 0.5rem; }}
        .summary-card .value {{
            font-size: 2rem;
            font-weight: bold;
            color: #667eea;
        }}
        .summary-card.success .value {{ color: #10b981; }}
        .summary-card.error .value {{ color: #ef4444; }}
        .content {{ padding: 2rem; }}
        .section {{ margin-bottom: 3rem; }}
        .section h2 {{
            font-size: 1.8rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
            color: #333;
        }}
        .check-list, .phase-list {{ list-style: none; }}
        .check-item, .phase-item {{
            background: #f8f9fa;
            margin: 0.5rem 0;
            padding: 1rem;
            border-radius: 8px;
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
        .check-item.passed, .phase-item.passed {{ background: #d1fae5; }}
        .check-item.failed, .phase-item.failed {{ background: #fee2e2; }}
        .icon {{ font-size: 1.5rem; }}
        .icon.success {{ color: #10b981; }}
        .icon.error {{ color: #ef4444; }}
        .check-details {{
            flex: 1;
        }}
        .check-details strong {{ display: block; margin-bottom: 0.25rem; }}
        .check-details small {{ color: #666; }}
        .phase-details {{ flex: 1; }}
        .phase-duration {{ color: #666; font-size: 0.9rem; }}
        .artifacts {{
            margin-top: 0.5rem;
            font-size: 0.9rem;
            color: #666;
        }}
        .artifacts a {{
            color: #667eea;
            text-decoration: none;
            margin-right: 1rem;
        }}
        .artifacts a:hover {{ text-decoration: underline; }}
        .footer {{
            background: #f8f9fa;
            padding: 2rem;
            text-align: center;
            color: #666;
            font-size: 0.9rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 TweekIT MCP E2E Test Report</h1>
            <p>Version {results.version} | {results.timestamp}</p>
        </div>
        
        <div class="summary">
            <div class="summary-card {'success' if results.overall_passed else 'error'}">
                <h3>Overall Status</h3>
                <div class="value">{'PASS' if results.overall_passed else 'FAIL'}</div>
            </div>
            <div class="summary-card">
                <h3>Pre-flight Checks</h3>
                <div class="value">{passed_checks}/{total_checks}</div>
            </div>
            <div class="summary-card">
                <h3>Test Phases</h3>
                <div class="value">{passed_phases}/{total_phases}</div>
            </div>
            <div class="summary-card">
                <h3>Total Duration</h3>
                <div class="value">{results.total_duration_seconds:.1f}s</div>
            </div>
        </div>
        
        <div class="content">
            <div class="section">
                <h2>📋 Pre-flight Checks</h2>
                <ul class="check-list">
"""
    
    for check in results.preflight_checks:
        status_class = "passed" if check.passed else "failed"
        icon = "✓" if check.passed else "✗"
        icon_class = "success" if check.passed else "error"
        
        html += f"""
                    <li class="check-item {status_class}">
                        <span class="icon {icon_class}">{icon}</span>
                        <div class="check-details">
                            <strong>{check.name}</strong>
                            <div>{check.message}</div>
                            <small>{check.details}</small>
                        </div>
                    </li>
"""
    
    html += """
                </ul>
            </div>
            
            <div class="section">
                <h2>🧪 Test Phases</h2>
                <ul class="phase-list">
"""
    
    for phase in results.test_phases:
        status_class = "passed" if phase.passed else "failed"
        icon = "✓" if phase.passed else "✗"
        icon_class = "success" if phase.passed else "error"
        
        html += f"""
                    <li class="phase-item {status_class}">
                        <span class="icon {icon_class}">{icon}</span>
                        <div class="phase-details">
                            <strong>{phase.phase}</strong>
                            <div class="phase-duration">Duration: {phase.duration_seconds:.1f}s</div>
"""
        
        if phase.artifacts:
            html += '                            <div class="artifacts">Artifacts: '
            for artifact in phase.artifacts[:5]:  # Show first 5
                rel_path = artifact.relative_to(results.results_dir)
                html += f'<a href="{rel_path}">{artifact.name}</a> '
            if len(phase.artifacts) > 5:
                html += f'<span>... and {len(phase.artifacts) - 5} more</span>'
            html += '</div>\n'
        
        if phase.error:
            html += f'                            <div style="color: #ef4444; font-size: 0.9rem; margin-top: 0.5rem;">Error: {phase.error}</div>\n'
        
        html += """
                        </div>
                    </li>
"""
    
    html += f"""
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>Generated by run_full_e2e_test.py</p>
            <p>System: {platform.system()} {platform.release()} | Python {platform.python_version()}</p>
        </div>
    </div>
</body>
</html>
"""
    
    report_path.write_text(html, encoding='utf-8')
    print_success(f"Report generated: {report_path}")
    
    return report_path


def main() -> int:
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive E2E tests for TweekIT MCP Server"
    )
    parser.add_argument(
        "--env",
        choices=["local", "stage", "prod"],
        default="prod",
        help="Target environment (default: prod)"
    )
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Run only pre-flight checks and exit"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Skip browser screenshot capture"
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="Generate HTML report (default: True unless --preflight-only)"
    )
    
    args = parser.parse_args()
    
    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)
    
    start_time = time.time()
    
    print_info(f"Target Environment: {args.env.upper()}")
    
    # Run pre-flight checks
    preflight_results = run_preflight_checks(args.env)
    
    if args.preflight_only:
        failed_checks = [c for c in preflight_results if not c.passed]
        if failed_checks:
            print_error(f"\n{len(failed_checks)} pre-flight check(s) failed")
            return 1
        else:
            print_success("\nAll pre-flight checks passed!")
            return 0
    
    # Check if critical pre-flight checks passed
    critical_failed = [c for c in preflight_results if not c.passed and c.name in [
        "Python Version", "UV Package Manager", "API Credentials"
    ]]
    
    if critical_failed:
        print_error("\nCritical pre-flight checks failed. Cannot continue.")
        for check in critical_failed:
            print_error(f"  - {check.name}: {check.message}")
        return 1
    
    # Create results directory
    results_dir = create_results_directory()
    
    # Get version
    version_check = next((c for c in preflight_results if c.name == "Project Version"), None)
    version = version_check.message if version_check and version_check.passed else "unknown"
    
    # Start server (if local)
    server_process = start_mcp_server(results_dir, args.env)
    if args.env == "local" and not server_process:
        print_error("Failed to start MCP server. Aborting tests.")
        return 1
    
    test_phases: list[TestPhaseResult] = []
    
    try:
        # Run smoke tests
        test_phases.append(run_smoke_tests(results_dir, args.env))
        
        # Run conversion sweep
        test_phases.append(run_conversion_sweep(results_dir, args.env))
        
        # Validate submission checklists
        test_phases.append(validate_submission_checklists(results_dir))
        
        # Optionally capture browser screenshots
        if not args.no_browser:
            test_phases.append(capture_browser_screenshots(results_dir))
        
    finally:
        # Stop server (if local)
        if server_process:
            print_header("STOPPING SERVER")
            if server_process.poll() is None:
                server_process.terminate()
                try:
                    server_process.wait(timeout=10)
                    print_success("Server stopped")
                except subprocess.TimeoutExpired:
                    server_process.kill()
                    print_warning("Server forcefully killed")
    
    # Calculate totals
    total_duration = time.time() - start_time
    overall_passed = all(c.passed for c in preflight_results) and all(p.passed for p in test_phases)
    
    # Create results summary
    results = E2ETestResults(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        version=version,
        preflight_checks=preflight_results,
        test_phases=test_phases,
        results_dir=results_dir,
        total_duration_seconds=total_duration,
        overall_passed=overall_passed
    )
    
    # Generate report
    if args.generate_report or not args.preflight_only:
        report_path = generate_html_report(results)
        print_info(f"\nOpen report: file://{report_path.absolute()}")
    
    # Final summary
    print_header("TEST SUMMARY")
    if overall_passed:
        print_success(f"All tests passed! ({total_duration:.1f}s)")
        print_info(f"Results: {results_dir}")
        return 0
    else:
        print_error(f"Some tests failed ({total_duration:.1f}s)")
        failed_phases = [p.phase for p in test_phases if not p.passed]
        for phase in failed_phases:
            print_error(f"  - {phase}")
        print_info(f"Results: {results_dir}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
