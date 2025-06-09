#!/usr/bin/env python3
"""
Build validation script - Run before pushing to check dependencies and basic functionality
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - PASSED")
            return True
        else:
            print(f"❌ {description} - FAILED")
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        return False

def validate_requirements():
    """Validate that requirements.txt can be installed"""
    print("🔍 Validating requirements.txt...")
    
    # Create a temporary virtual environment for testing
    temp_venv = ".temp_build_test"
    
    commands = [
        f"python3 -m venv {temp_venv}",
        f"{temp_venv}/bin/pip install --upgrade pip",
        f"{temp_venv}/bin/pip install -r requirements.txt"
    ]
    
    try:
        for cmd in commands:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Requirements validation failed: {result.stderr}")
                return False
        
        print("✅ Requirements validation - PASSED")
        return True
    
    except Exception as e:
        print(f"❌ Requirements validation - ERROR: {e}")
        return False
    
    finally:
        # Cleanup
        subprocess.run(f"rm -rf {temp_venv}", shell=True, capture_output=True)

def validate_docker_build():
    """Validate Docker build"""
    return run_command(
        "docker build -t routiq-backend-test .",
        "Docker build validation"
    )

def validate_python_syntax():
    """Check Python syntax across the codebase"""
    return run_command(
        "python3 -m py_compile src/api/main.py src/database.py",
        "Python syntax validation"
    )

def main():
    """Run all validation checks"""
    print("🚀 Starting build validation...")
    print("=" * 50)
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    checks = [
        ("Requirements Installation", validate_requirements),
        ("Python Syntax", validate_python_syntax),
        ("Docker Build", validate_docker_build),
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        if not check_func():
            failed_checks.append(check_name)
        print()
    
    print("=" * 50)
    if failed_checks:
        print(f"❌ BUILD VALIDATION FAILED - {len(failed_checks)} checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        print("\n🛑 DO NOT PUSH - Fix issues above first!")
        sys.exit(1)
    else:
        print("✅ ALL VALIDATIONS PASSED - Safe to push!")
        print("🚀 You can now push to GitHub and deploy to Railway")
        sys.exit(0)

if __name__ == "__main__":
    main() 