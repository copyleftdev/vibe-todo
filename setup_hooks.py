#!/usr/bin/env python3
"""
Setup script for Git hooks in the Vibe Todo project.
This script installs the pre-commit hook to ensure all tests pass before committing.
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def setup_git_hooks():
    """Set up Git hooks for the project."""
    print("Setting up Git hooks for the Vibe Todo project...")
    
    # Get the repository root
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], 
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        print("Error: Not a git repository. Please run this script from within the git repository.")
        return False
    
    # Define paths
    hooks_dir = os.path.join(repo_root, ".git", "hooks")
    pre_commit_hook_path = os.path.join(hooks_dir, "pre-commit")
    pre_commit_script_path = os.path.join(repo_root, "pre-commit-hook.sh")
    
    # Ensure hooks directory exists
    if not os.path.exists(hooks_dir):
        print(f"Creating hooks directory: {hooks_dir}")
        os.makedirs(hooks_dir)
    
    # Check if pre-commit hook already exists
    if os.path.exists(pre_commit_hook_path):
        backup_path = pre_commit_hook_path + ".backup"
        print(f"Backing up existing hook to {backup_path}")
        shutil.copy2(pre_commit_hook_path, backup_path)
    
    # Create symbolic link to our hook script
    print(f"Creating pre-commit hook: {pre_commit_hook_path}")
    try:
        # On Windows, symlinks might not work well, so we use a wrapper script
        if os.name == 'nt':  # Windows
            with open(pre_commit_hook_path, 'w') as f:
                f.write(f"""#!/bin/sh
# This is a wrapper script for the pre-commit hook
{pre_commit_script_path}
exit $?
""")
        else:  # Unix/Linux/Mac
            # If file exists, remove it first
            if os.path.exists(pre_commit_hook_path):
                os.remove(pre_commit_hook_path)
            # Create symbolic link
            os.symlink(pre_commit_script_path, pre_commit_hook_path)
        
        # Make the hook executable
        os.chmod(pre_commit_hook_path, 0o755)
        print("Pre-commit hook installed successfully!")
        
        return True
    except Exception as e:
        print(f"Error installing pre-commit hook: {e}")
        return False

def create_test_automation_readme():
    """Create a README file explaining the test automation setup."""
    readme_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_AUTOMATION.md")
    
    with open(readme_path, 'w') as f:
        f.write("""# Test Automation for Vibe Todo

This document explains the test automation setup for the Vibe Todo project.

## Pre-commit Hook

A pre-commit hook has been set up to ensure all tests pass before allowing a commit. This enforces the rule that all tests, especially Hypothesis tests, must pass before any code can be committed or merged.

### What the Hook Does

The pre-commit hook runs the following tests:

1. **Unit Tests** - Basic functionality tests
2. **Hypothesis Tests** - Property-based tests that validate system properties
3. **Regression Tests** - Tests for known edge cases and potential vulnerabilities
4. **Benchmark Tests** (in quick mode) - Ensures performance meets SLA requirements

If any tests fail, the commit is rejected with a message indicating which tests failed.

### Installation

The pre-commit hook is installed by running:

```
python setup_hooks.py
```

This script creates a symbolic link from `.git/hooks/pre-commit` to `pre-commit-hook.sh`.

### Manual Testing

You can manually run the tests using the following commands:

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_unit.py
pytest tests/test_hypothesis.py
pytest tests/test_regression.py

# Run benchmark tests (full mode)
python tests/test_benchmark.py

# Run benchmark tests (quick mode for pre-commit)
python tests/test_benchmark.py --quick
```

## Continuous Integration

For a more robust setup, consider integrating with a CI/CD system like:

- GitHub Actions
- Jenkins
- GitLab CI
- Travis CI

This would run the complete test suite on every push and pull request.

## Evolutionary Testing

The system includes evolutionary testing that uses the DEAP library to discover edge cases and potential vulnerabilities. This testing evolves inputs over time to find problematic scenarios.

To run evolutionary tests:

```bash
python tests/test_evolutionary.py
```

This can be resource-intensive, so it's not included in the pre-commit hook, but should be run regularly during development and definitely before major releases.
""")
    
    print(f"Created test automation README: {readme_path}")
    return True

if __name__ == "__main__":
    # Setup Git hooks
    if setup_git_hooks():
        # Create the README file
        create_test_automation_readme()
        print("\nSetup complete! The pre-commit hook will now run tests before each commit.")
        print("For more information, see TEST_AUTOMATION.md")
    else:
        sys.exit(1)
