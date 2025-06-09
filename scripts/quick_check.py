#!/usr/bin/env python3
"""
Quick validation script - Basic checks before pushing
"""

import os
import sys
from pathlib import Path

def check_requirements():
    """Check if requirements.txt exists and is readable"""
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    try:
        with open(req_file) as f:
            lines = f.readlines()
            if len(lines) < 5:  # Should have more than a few dependencies
                print("❌ requirements.txt seems too short")
                return False
        print("✅ requirements.txt looks good")
        return True
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_main_files():
    """Check that main application files exist"""
    important_files = [
        "src/api/main.py",
        "src/database.py", 
        "Dockerfile",
        "RAILWAY_SETUP.md"
    ]
    
    missing = []
    for file_path in important_files:
        if not Path(file_path).exists():
            missing.append(file_path)
    
    if missing:
        print(f"❌ Missing important files: {missing}")
        return False
    
    print("✅ All important files present")
    return True

def check_python_syntax():
    """Basic Python syntax check on key files"""
    key_files = [
        "src/api/main.py",
        "src/database.py"
    ]
    
    for file_path in key_files:
        try:
            with open(file_path) as f:
                compile(f.read(), file_path, 'exec')
        except SyntaxError as e:
            print(f"❌ Syntax error in {file_path}: {e}")
            return False
        except Exception as e:
            print(f"❌ Error checking {file_path}: {e}")
            return False
    
    print("✅ Python syntax checks passed")
    return True

def check_cryptography_version():
    """Check if cryptography version is valid"""
    try:
        with open("requirements.txt") as f:
            content = f.read()
            if "cryptography==41.0.8" in content:
                print("❌ Cryptography version 41.0.8 is not available - update to 41.0.7")
                return False
            elif "cryptography==41.0.7" in content:
                print("✅ Cryptography version looks good")
                return True
            else:
                print("⚠️  Cryptography version not found in requirements.txt")
                return True
    except Exception as e:
        print(f"❌ Error checking cryptography version: {e}")
        return False

def main():
    """Run quick validation checks"""
    print("🚀 Running quick validation checks...")
    print("=" * 40)
    
    checks = [
        ("Requirements file", check_requirements),
        ("Important files", check_main_files),
        ("Python syntax", check_python_syntax),
        ("Cryptography version", check_cryptography_version),
    ]
    
    failed = []
    
    for name, check_func in checks:
        print(f"\n🔍 Checking {name}...")
        if not check_func():
            failed.append(name)
    
    print("\n" + "=" * 40)
    
    if failed:
        print(f"❌ {len(failed)} checks failed: {failed}")
        print("🛑 Fix issues before pushing!")
        return 1
    else:
        print("✅ All quick checks passed!")
        print("🚀 Ready to commit and push")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 