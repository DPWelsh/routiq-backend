#!/usr/bin/env python3
"""
Test Runner for Routiq Backend API
Provides easy commands to run different types of tests
"""

import os
import sys
import subprocess
import argparse
import time
import requests

def check_server_running(base_url="http://localhost:8000"):
    """Check if the API server is running"""
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False

def start_server_if_needed():
    """Start the API server if it's not running"""
    if check_server_running():
        print("✅ API server is already running")
        return True
    
    print("🚀 Starting API server...")
    try:
        # Start server in background
        subprocess.Popen([
            "python3", "-m", "uvicorn", "src.api.main:app", 
            "--reload", "--host", "0.0.0.0", "--port", "8000"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for server to start
        for i in range(10):
            time.sleep(2)
            if check_server_running():
                print("✅ API server started successfully")
                return True
            print(f"⏳ Waiting for server to start... ({i+1}/10)")
        
        print("❌ Failed to start API server")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def run_tests(test_type="all", verbose=False, stop_on_first_failure=False):
    """Run the specified tests"""
    
    # Ensure server is running
    if not start_server_if_needed():
        sys.exit(1)
    
    # Build pytest command
    cmd = ["python3", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if stop_on_first_failure:
        cmd.append("-x")
    
    # Add test type filters
    if test_type == "fast":
        cmd.extend(["-m", "not slow"])
    elif test_type == "slow":
        cmd.extend(["-m", "slow"])
    elif test_type == "integration":
        cmd.extend(["-m", "integration"])
    elif test_type == "load":
        cmd.extend(["-m", "load"])
    elif test_type == "unit":
        cmd.extend(["-m", "not integration and not load"])
    
    # Add coverage if available
    try:
        import coverage
        cmd.extend(["--cov=src", "--cov-report=html", "--cov-report=term"])
    except ImportError:
        pass
    
    print(f"🧪 Running {test_type} tests...")
    print(f"Command: {' '.join(cmd)}")
    
    # Run tests
    result = subprocess.run(cmd)
    return result.returncode

def main():
    parser = argparse.ArgumentParser(description="Run Routiq Backend API tests")
    parser.add_argument(
        "test_type", 
        choices=["all", "fast", "slow", "unit", "integration", "load"],
        default="all",
        nargs="?",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "-v", "--verbose", 
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-x", "--stop-on-first-failure",
        action="store_true", 
        help="Stop on first failure"
    )
    parser.add_argument(
        "--no-server-check",
        action="store_true",
        help="Skip server startup check"
    )
    
    args = parser.parse_args()
    
    if not args.no_server_check:
        # Check if server is running
        if not check_server_running():
            print("❌ API server is not running at http://localhost:8000")
            print("Please start the server first with:")
            print("  python3 -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000")
            print("\nOr run with automatic server startup (experimental):")
            print("  python3 run_tests.py --no-server-check")
            sys.exit(1)
    
    # Run tests
    exit_code = run_tests(
        test_type=args.test_type,
        verbose=args.verbose,
        stop_on_first_failure=args.stop_on_first_failure
    )
    
    if exit_code == 0:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 