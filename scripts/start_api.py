#!/usr/bin/env python3
"""
Start the SurfRehab v2 API server locally
"""

import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def main():
    # Load environment variables
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"⚠️  No .env file found at {env_file}")
        print("Run: python scripts/setup_multi_tenant.py first")
        return 1
    
    # Set Python path
    src_path = project_root / 'src'
    os.environ['PYTHONPATH'] = str(src_path)
    
    # Change to src directory
    os.chdir(src_path)
    
    # Start the API server
    port = os.getenv('PORT', '8000')
    
    print(f"🚀 Starting SurfRehab v2 API on port {port}")
    print(f"📖 API docs will be available at: http://localhost:{port}/docs")
    print(f"🔧 Health check: http://localhost:{port}/health")
    print("Press Ctrl+C to stop\n")
    
    try:
        subprocess.run([
            sys.executable, '-m', 'uvicorn',
            'api.main:app',
            '--host', '0.0.0.0',
            '--port', port,
            '--reload',
            '--log-level', 'info'
        ])
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main()) 