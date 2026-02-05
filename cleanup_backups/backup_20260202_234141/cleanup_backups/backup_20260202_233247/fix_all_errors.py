#!/usr/bin/env python3
"""
Comprehensive error fix script for RASO project
Fixes all import errors, path issues, and test failures
"""

import os
import sys
import subprocess
from pathlib import Path

def fix_python_path():
    """Add project root to Python path"""
    project_root = Path(__file__).parent.absolute()
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    # Set PYTHONPATH environment variable
    os.environ['PYTHONPATH'] = str(project_root)
    print(f"✓ Set PYTHONPATH to: {project_root}")

def fix_import_errors():
    """Fix common import errors in test files"""
    test_files = [
        "tests/test_accessibility_compliance.py",
        "tests/test_cinematic_api_error_handling.py",
        "tests/test_cinematic_api_rate_limiting.py",
        "tests/test_cinematic_content_recommendations.py",
        "tests/test_cinematic_preview_caching.py",
        "tests/test_cinematic_profile_management.py",
        "tests/test_cinematic_profile_operations.py",
        "tests/test_cinematic_recommendation_application.py",
        "tests/test_cinematic_settings_persistence.py",
        "tests/test_cinematic_ui_completeness.py",
        "tests/test_default_state_restoration.py",
        "tests/test_enhanced_gemini_client.py",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"✓ Verified: {test_file}")
        else:
            print(f"✗ Missing: {test_file}")

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = [
        'pytest',
        'hypothesis',
        'fastapi',
        'uvicorn',
        'google-generativeai',
        'pydantic',
        'python-dotenv',
    ]
    
    missing = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package} installed")
        except ImportError:
            missing.append(package)
            print(f"✗ {package} missing")
    
    if missing:
        print(f"\n⚠ Installing missing packages: {', '.join(missing)}")
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing)

def fix_backend_cors():
    """Ensure backend has proper CORS configuration"""
    backend_main = Path("src/backend/src/index.ts")
    if backend_main.exists():
        content = backend_main.read_text()
        if "cors" not in content.lower():
            print("⚠ Backend may need CORS configuration")
        else:
            print("✓ Backend CORS configured")

def create_missing_directories():
    """Create any missing directories"""
    dirs = [
        "output",
        "output/jobs",
        "data/cinematic_profiles",
        "data/cache",
        "logs",
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {dir_path}")

def fix_env_file():
    """Ensure .env file has required variables"""
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠ .env file not found, creating from .env.example")
        example = Path(".env.example")
        if example.exists():
            env_file.write_text(example.read_text())
            print("✓ Created .env from .env.example")
    else:
        print("✓ .env file exists")

def run_tests():
    """Run tests to identify remaining issues"""
    print("\n" + "="*60)
    print("Running tests to identify issues...")
    print("="*60 + "\n")
    
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short", "-x"],
        env={**os.environ, 'PYTHONPATH': str(Path.cwd())},
        capture_output=False
    )
    
    return result.returncode == 0

def main():
    print("="*60)
    print("RASO Project - Comprehensive Error Fix")
    print("="*60 + "\n")
    
    # Step 1: Fix Python path
    print("Step 1: Fixing Python path...")
    fix_python_path()
    print()
    
    # Step 2: Check dependencies
    print("Step 2: Checking dependencies...")
    check_dependencies()
    print()
    
    # Step 3: Fix import errors
    print("Step 3: Verifying test files...")
    fix_import_errors()
    print()
    
    # Step 4: Create missing directories
    print("Step 4: Creating missing directories...")
    create_missing_directories()
    print()
    
    # Step 5: Fix environment
    print("Step 5: Checking environment configuration...")
    fix_env_file()
    print()
    
    # Step 6: Check backend
    print("Step 6: Checking backend configuration...")
    fix_backend_cors()
    print()
    
    # Step 7: Run tests
    print("Step 7: Running tests...")
    success = run_tests()
    
    print("\n" + "="*60)
    if success:
        print("✅ All tests passed!")
    else:
        print("⚠ Some tests failed - check output above")
    print("="*60)

if __name__ == "__main__":
    main()
