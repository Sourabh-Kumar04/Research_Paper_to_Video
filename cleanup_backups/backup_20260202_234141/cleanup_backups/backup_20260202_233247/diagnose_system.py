#!/usr/bin/env python3
"""
Comprehensive diagnostic script for RASO YouTube Automation system.
Checks for all types of errors and provides actionable fixes.
"""

import os
import sys
import subprocess
from pathlib import Path
import importlib.util


class DiagnosticRunner:
    """Run comprehensive diagnostics on the RASO system."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.errors_found = []
        self.warnings_found = []
        self.fixes_applied = []
    
    def run_all_diagnostics(self):
        """Run all diagnostic checks."""
        print("🔍 RASO System Diagnostics")
        print("=" * 60)
        print()
        
        self.check_python_version()
        self.check_directory_structure()
        self.check_environment_file()
        self.check_import_errors()
        self.check_dependencies()
        self.check_file_permissions()
        
        self.print_summary()
    
    def check_python_version(self):
        """Check Python version."""
        print("1️⃣ Checking Python Version...")
        version = sys.version_info
        
        if version.major >= 3 and version.minor >= 8:
            print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        else:
            error = f"Python 3.8+ required, found {version.major}.{version.minor}.{version.micro}"
            self.errors_found.append(error)
            print(f"   ❌ {error}")
        print()
    
    def check_directory_structure(self):
        """Check critical directories exist."""
        print("2️⃣ Checking Directory Structure...")
        
        critical_dirs = [
            'src/agents',
            'src/graph',
            'config/backend',
            'config/backend/models',
            'config/backend/services',
            'scripts',
            'output',
            'logs',
            'data',
            'temp',
        ]
        
        all_good = True
        for dir_path in critical_dirs:
            full_path = self.project_root / dir_path
            if full_path.exists():
                print(f"   ✅ {dir_path}")
            else:
                all_good = False
                error = f"Missing directory: {dir_path}"
                self.errors_found.append(error)
                print(f"   ❌ {error}")
                
                # Try to create it
                try:
                    full_path.mkdir(parents=True, exist_ok=True)
                    self.fixes_applied.append(f"Created {dir_path}")
                    print(f"      🔧 Created directory")
                except Exception as e:
                    print(f"      💥 Could not create: {e}")
        
        print()
    
    def check_environment_file(self):
        """Check .env file exists and has required variables."""
        print("3️⃣ Checking Environment Configuration...")
        
        env_file = self.project_root / '.env'
        
        if not env_file.exists():
            error = ".env file not found"
            self.errors_found.append(error)
            print(f"   ❌ {error}")
            
            # Check for .env.example
            env_example = self.project_root / '.env.example'
            if env_example.exists():
                print(f"      💡 Copy .env.example to .env and configure it")
            print()
            return
        
        print(f"   ✅ .env file exists")
        
        # Check for critical variables
        required_vars = [
            'RASO_ENV',
            'RASO_LOG_LEVEL',
            'RASO_API_PORT',
        ]
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
            
            missing_vars = []
            for var in required_vars:
                if f"{var}=" not in content:
                    missing_vars.append(var)
            
            if missing_vars:
                warning = f"Missing environment variables: {', '.join(missing_vars)}"
                self.warnings_found.append(warning)
                print(f"   ⚠️  {warning}")
            else:
                print(f"   ✅ All required variables present")
        
        except Exception as e:
            error = f"Could not read .env file: {e}"
            self.errors_found.append(error)
            print(f"   ❌ {error}")
        
        print()
    
    def check_import_errors(self):
        """Check for common import errors."""
        print("4️⃣ Checking Import Errors...")
        
        import_errors = []
        
        # Check for incorrect backend.models imports
        for py_file in self.project_root.rglob('*.py'):
            # Skip virtual environment and other excluded directories
            skip_dirs = {'.venv', 'node_modules', '__pycache__', '.git'}
            if any(skip in py_file.parts for skip in skip_dirs):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for incorrect imports
                if 'from backend.models' in content:
                    import_errors.append((py_file, 'from backend.models'))
                if 'from backend.services' in content:
                    import_errors.append((py_file, 'from backend.services'))
                if 'import backend.models' in content:
                    import_errors.append((py_file, 'import backend.models'))
            
            except Exception:
                pass
        
        if import_errors:
            print(f"   ❌ Found {len(import_errors)} files with incorrect imports")
            for file_path, error in import_errors[:5]:  # Show first 5
                rel_path = file_path.relative_to(self.project_root)
                print(f"      • {rel_path}: {error}")
            if len(import_errors) > 5:
                print(f"      ... and {len(import_errors) - 5} more")
            
            error_msg = f"Found incorrect imports in {len(import_errors)} files"
            self.errors_found.append(error_msg)
            print()
            print(f"      💡 Run: python fix_all_import_errors.py")
        else:
            print(f"   ✅ No import errors found")
        
        print()
    
    def check_dependencies(self):
        """Check if required Python packages are installed."""
        print("5️⃣ Checking Python Dependencies...")
        
        required_packages = [
            'fastapi',
            'uvicorn',
            'pydantic',
            'pydantic_settings',
            'langgraph',
            'langchain',
            'moviepy',
            'opencv-python',
            'pillow',
            'numpy',
            'aiohttp',
        ]
        
        missing_packages = []
        
        for package in required_packages:
            # Handle package name variations
            module_name = package.replace('-', '_')
            
            spec = importlib.util.find_spec(module_name)
            if spec is None:
                missing_packages.append(package)
                print(f"   ❌ {package}")
            else:
                print(f"   ✅ {package}")
        
        if missing_packages:
            error = f"Missing packages: {', '.join(missing_packages)}"
            self.errors_found.append(error)
            print()
            print(f"      💡 Run: pip install {' '.join(missing_packages)}")
        
        print()
    
    def check_file_permissions(self):
        """Check file permissions for critical files."""
        print("6️⃣ Checking File Permissions...")
        
        critical_files = [
            'main.py',
            'config/backend/main.py',
            'scripts/demo_unified_pipeline.py',
        ]
        
        permission_issues = []
        
        for file_path in critical_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                if os.access(full_path, os.R_OK):
                    print(f"   ✅ {file_path} (readable)")
                else:
                    permission_issues.append(file_path)
                    print(f"   ❌ {file_path} (not readable)")
            else:
                print(f"   ⚠️  {file_path} (not found)")
        
        if permission_issues:
            warning = f"Permission issues: {', '.join(permission_issues)}"
            self.warnings_found.append(warning)
        
        print()
    
    def print_summary(self):
        """Print diagnostic summary."""
        print("=" * 60)
        print("📊 Diagnostic Summary")
        print("=" * 60)
        
        if self.errors_found:
            print(f"\n❌ {len(self.errors_found)} Errors Found:")
            for i, error in enumerate(self.errors_found, 1):
                print(f"   {i}. {error}")
        
        if self.warnings_found:
            print(f"\n⚠️  {len(self.warnings_found)} Warnings:")
            for i, warning in enumerate(self.warnings_found, 1):
                print(f"   {i}. {warning}")
        
        if self.fixes_applied:
            print(f"\n🔧 {len(self.fixes_applied)} Fixes Applied:")
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"   {i}. {fix}")
        
        if not self.errors_found and not self.warnings_found:
            print("\n✅ All checks passed! System is healthy.")
            print("\n🚀 You can now run: python main.py")
        else:
            print("\n💡 Fix the errors above and run diagnostics again.")
            print("\nQuick fixes available:")
            print("   • python fix_all_import_errors.py  (fix import errors)")
            print("   • pip install -r requirements.txt  (install dependencies)")
        
        print()


def main():
    """Run diagnostics."""
    runner = DiagnosticRunner()
    runner.run_all_diagnostics()


if __name__ == "__main__":
    main()
