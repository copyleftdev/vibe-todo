#!/usr/bin/env python3
"""
Test Runner for Vibe Todo project
Runs all tests to ensure code quality before committing or merging changes
"""
import os
import sys
import subprocess
import time
import json
from datetime import datetime

# Colors for terminal output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 80}{Colors.ENDC}\n")

def print_result(name, passed):
    """Print a test result with appropriate coloring"""
    status = f"{Colors.GREEN}PASSED{Colors.ENDC}" if passed else f"{Colors.RED}FAILED{Colors.ENDC}"
    print(f"{Colors.BOLD}{name}:{Colors.ENDC} {status}")

def run_command(command, env=None):
    """Run a command and return success status and output"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            env=env
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def run_all_tests(quick_mode=False, output_report=True):
    """
    Run all tests for the project
    
    Args:
        quick_mode (bool): If True, run a faster subset of tests
        output_report (bool): If True, save a test report to the reports directory
    
    Returns:
        bool: True if all tests passed, False otherwise
    """
    print_header("VIBE TODO - TEST RUNNER")
    print(f"Running in {'QUICK' if quick_mode else 'FULL'} mode")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Ensure we're in the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(project_root)
    
    # Set up environment with correct PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = project_root
    
    # Results storage
    results = {
        "timestamp": datetime.now().isoformat(),
        "tests": {},
        "overall_result": None
    }
    
    all_passed = True
    
    # Run unit tests
    print_header("Running Unit Tests")
    unit_passed, unit_stdout, unit_stderr = run_command("pytest tests/test_unit.py -v", env)
    print(unit_stdout)
    if unit_stderr.strip():
        print(f"{Colors.RED}{unit_stderr}{Colors.ENDC}")
    print_result("Unit Tests", unit_passed)
    results["tests"]["unit"] = {
        "passed": unit_passed,
        "output": unit_stdout
    }
    all_passed = all_passed and unit_passed
    
    # Run hypothesis tests
    print_header("Running Hypothesis Tests")
    hypothesis_passed, hypothesis_stdout, hypothesis_stderr = run_command("pytest tests/test_hypothesis.py -v", env)
    print(hypothesis_stdout)
    if hypothesis_stderr.strip():
        print(f"{Colors.RED}{hypothesis_stderr}{Colors.ENDC}")
    print_result("Hypothesis Tests", hypothesis_passed)
    results["tests"]["hypothesis"] = {
        "passed": hypothesis_passed,
        "output": hypothesis_stdout
    }
    all_passed = all_passed and hypothesis_passed
    
    # Run regression tests
    print_header("Running Regression Tests")
    regression_passed, regression_stdout, regression_stderr = run_command("pytest tests/test_regression.py -v", env)
    print(regression_stdout)
    if regression_stderr.strip():
        print(f"{Colors.RED}{regression_stderr}{Colors.ENDC}")
    print_result("Regression Tests", regression_passed)
    results["tests"]["regression"] = {
        "passed": regression_passed,
        "output": regression_stdout
    }
    all_passed = all_passed and regression_passed
    
    # Run benchmark tests
    print_header("Running Benchmark Tests")
    benchmark_cmd = "python tests/test_benchmark.py --quick" if quick_mode else "python tests/test_benchmark.py"
    benchmark_passed, benchmark_stdout, benchmark_stderr = run_command(benchmark_cmd, env)
    print(benchmark_stdout[:1000] + "..." if len(benchmark_stdout) > 1000 else benchmark_stdout)
    if benchmark_stderr.strip():
        print(f"{Colors.RED}{benchmark_stderr}{Colors.ENDC}")
    print_result("Benchmark Tests", benchmark_passed)
    results["tests"]["benchmark"] = {
        "passed": benchmark_passed,
        "output": benchmark_stdout[:5000]  # Limit output size
    }
    all_passed = all_passed and benchmark_passed
    
    # Run evolutionary tests only in full mode and if explicitly requested
    if not quick_mode and "--evolutionary" in sys.argv:
        print_header("Running Evolutionary Tests")
        evolutionary_passed, evolutionary_stdout, evolutionary_stderr = run_command("python tests/test_evolutionary.py --quick", env)
        print(evolutionary_stdout[:1000] + "..." if len(evolutionary_stdout) > 1000 else evolutionary_stdout)
        if evolutionary_stderr.strip():
            print(f"{Colors.RED}{evolutionary_stderr}{Colors.ENDC}")
        print_result("Evolutionary Tests", evolutionary_passed)
        results["tests"]["evolutionary"] = {
            "passed": evolutionary_passed,
            "output": evolutionary_stdout[:5000]  # Limit output size
        }
        all_passed = all_passed and evolutionary_passed
    
    # Print overall result
    print_header("OVERALL RESULT")
    overall_result = "PASSED" if all_passed else "FAILED"
    color = Colors.GREEN if all_passed else Colors.RED
    print(f"{color}{Colors.BOLD}{overall_result}{Colors.ENDC}")
    
    results["overall_result"] = all_passed
    
    # Generate report if requested
    if output_report:
        # Ensure reports directory exists
        reports_dir = os.path.join(project_root, "reports")
        os.makedirs(reports_dir, exist_ok=True)
        
        # Create timestamp for report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(reports_dir, f"test_report_{timestamp}.json")
        
        # Write JSON report
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\nTest report saved to: {report_file}")
        
        # Generate markdown report
        md_report = f"""# Vibe Todo Test Report
**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Mode:** {'QUICK' if quick_mode else 'FULL'}
**Overall Result:** {'✅ PASSED' if all_passed else '❌ FAILED'}

## Test Results

| Test Suite | Result |
|------------|--------|
| Unit Tests | {'✅ PASSED' if results["tests"]["unit"]["passed"] else '❌ FAILED'} |
| Hypothesis Tests | {'✅ PASSED' if results["tests"]["hypothesis"]["passed"] else '❌ FAILED'} |
| Regression Tests | {'✅ PASSED' if results["tests"]["regression"]["passed"] else '❌ FAILED'} |
| Benchmark Tests | {'✅ PASSED' if results["tests"]["benchmark"]["passed"] else '❌ FAILED'} |
"""
        
        if "evolutionary" in results["tests"]:
            md_report += f"| Evolutionary Tests | {'✅ PASSED' if results['tests']['evolutionary']['passed'] else '❌ FAILED'} |\n"
        
        md_report += """
## Test Details

### Unit Tests
These tests validate the basic functionality of the Todo application.

### Hypothesis Tests
Property-based tests that ensure the application behaves correctly with random inputs.

### Regression Tests
Tests that verify the application correctly handles edge cases and potential vulnerabilities.

### Benchmark Tests
Performance tests that ensure the application meets SLA requirements.
"""
        
        if "evolutionary" in results["tests"]:
            md_report += """
### Evolutionary Tests
Tests that use genetic algorithms to evolve inputs that might break the system.
"""
            
        md_report += f"""
## Note

According to our project rules, all Hypothesis tests **must** pass before any code can be committed or merged.

## SLA Compliance

All operations are required to meet a Service-Level Agreement (SLA) of **10 milliseconds maximum latency per task operation**.
The benchmark tests verify this requirement is met.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Write markdown report
        md_report_file = os.path.join(reports_dir, f"test_report_{timestamp}.md")
        with open(md_report_file, 'w') as f:
            f.write(md_report)
        
        print(f"Markdown report saved to: {md_report_file}")
    
    return all_passed

if __name__ == "__main__":
    quick_mode = "--quick" in sys.argv
    success = run_all_tests(quick_mode=quick_mode)
    
    # Exit with appropriate code for CI/CD integration
    sys.exit(0 if success else 1)
