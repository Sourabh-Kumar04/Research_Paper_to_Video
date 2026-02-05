#!/usr/bin/env python3
"""
Execute Security Hardening for RASO Codebase
"""

from pathlib import Path
from security_hardener import SecurityHardener

def main():
    """Execute security hardening."""
    root_path = Path(".")
    
    # Initialize hardener (not dry run)
    hardener = SecurityHardener(root_path, dry_run=False)
    
    print("🔒 Executing RASO Security Hardening")
    print("=" * 50)
    
    # Execute security hardening
    result = hardener.secure_configuration()
    
    print(f"\n✅ Security hardening complete!")
    print(f"  • Secrets found: {result.secrets_found}")
    print(f"  • Secrets replaced: {result.secrets_replaced}")
    print(f"  • Templates created: {result.templates_created}")
    print(f"  • Config files secured: {result.config_files_secured}")
    
    if result.errors:
        print(f"  ⚠️ Errors: {len(result.errors)}")
        for error in result.errors:
            print(f"    • {error}")

if __name__ == "__main__":
    main()