#!/usr/bin/env python3
"""
Security Hardener for RASO Codebase
Secures configuration files, removes exposed secrets, and creates secure templates.
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass
import hashlib

logger = logging.getLogger(__name__)


@dataclass
class SecretLocation:
    """Information about a detected secret."""
    file_path: Path
    line_number: int
    secret_type: str
    secret_value: str
    context: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'file_path': str(self.file_path),
            'line_number': self.line_number,
            'secret_type': self.secret_type,
            'secret_value': self.secret_value[:10] + "..." if len(self.secret_value) > 10 else self.secret_value,
            'context': self.context
        }


@dataclass
class SecurityResult:
    """Results of security hardening operations."""
    secrets_found: int
    secrets_replaced: int
    templates_created: int
    config_files_secured: int
    errors: List[str]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'secrets_found': self.secrets_found,
            'secrets_replaced': self.secrets_replaced,
            'templates_created': self.templates_created,
            'config_files_secured': self.config_files_secured,
            'errors': self.errors
        }


class SecurityHardener:
    """Secures configuration and removes exposed secrets from codebase."""
    
    def __init__(self, root_path: Path, dry_run: bool = False):
        """Initialize security hardener."""
        self.root_path = Path(root_path)
        self.dry_run = dry_run
        
        # Secret detection patterns
        self.secret_patterns = {
            'api_key': [
                r'(?i)(api[_-]?key|apikey)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
                r'(?i)(key)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{32,})["\']',
            ],
            'google_api_key': [
                r'(?i)(google[_-]?api[_-]?key|raso[_-]?google[_-]?api[_-]?key)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            ],
            'openai_api_key': [
                r'(?i)(openai[_-]?api[_-]?key)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
                r'sk-[a-zA-Z0-9]{48}',
            ],
            'anthropic_api_key': [
                r'(?i)(anthropic[_-]?api[_-]?key)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{20,})["\']',
            ],
            'database_url': [
                r'(?i)(database[_-]?url|db[_-]?url)\s*[=:]\s*["\']([^"\']+://[^"\']+)["\']',
            ],
            'password': [
                r'(?i)(password|passwd|pwd)\s*[=:]\s*["\']([^"\']{8,})["\']',
            ],
            'secret_key': [
                r'(?i)(secret[_-]?key|secret)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{16,})["\']',
            ],
            'jwt_secret': [
                r'(?i)(jwt[_-]?secret|token[_-]?secret)\s*[=:]\s*["\']([a-zA-Z0-9_\-]{16,})["\']',
            ]
        }
        
        # Configuration file patterns
        self.config_file_patterns = [
            '.env*',
            '*.json',
            '*.yaml',
            '*.yml',
            '*.toml',
            '*.ini',
            'config.py',
            'settings.py'
        ]
        
    def scan_for_secrets(self) -> List[SecretLocation]:
        """Scan all files for exposed secrets."""
        logger.info("Scanning for exposed secrets")
        
        secrets = []
        
        # Get all files to scan
        files_to_scan = self._get_files_to_scan()
        
        for file_path in files_to_scan:
            try:
                file_secrets = self._scan_file_for_secrets(file_path)
                secrets.extend(file_secrets)
            except Exception as e:
                logger.error(f"Error scanning {file_path}: {e}")
        
        logger.info(f"Secret scan complete: {len(secrets)} secrets found")
        return secrets
    
    def _get_files_to_scan(self) -> List[Path]:
        """Get list of files to scan for secrets."""
        files = []
        
        # Scan configuration files
        for pattern in self.config_file_patterns:
            files.extend(self.root_path.glob(pattern))
            files.extend(self.root_path.rglob(pattern))
        
        # Scan Python files
        files.extend(self.root_path.rglob('*.py'))
        
        # Remove duplicates and exclude certain directories
        exclude_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.hypothesis', 'cleanup_backups'}
        unique_files = []
        
        for file_path in files:
            # Check if file is in excluded directory
            if any(exclude_dir in file_path.parts for exclude_dir in exclude_dirs):
                continue
            
            if file_path not in unique_files and file_path.is_file():
                unique_files.append(file_path)
        
        return unique_files
    
    def _scan_file_for_secrets(self, file_path: Path) -> List[SecretLocation]:
        """Scan a single file for secrets."""
        secrets = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#') or line.startswith('//'):
                    continue
                
                # Check each secret pattern
                for secret_type, patterns in self.secret_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, line)
                        for match in matches:
                            # Extract the secret value
                            if match.groups():
                                secret_value = match.group(-1)  # Last group is usually the secret
                            else:
                                secret_value = match.group(0)
                            
                            # Skip obvious placeholders
                            if self._is_placeholder(secret_value):
                                continue
                            
                            secret = SecretLocation(
                                file_path=file_path,
                                line_number=line_num,
                                secret_type=secret_type,
                                secret_value=secret_value,
                                context=line[:100]  # First 100 chars for context
                            )
                            secrets.append(secret)
                            
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
        
        return secrets
    
    def _is_placeholder(self, value: str) -> bool:
        """Check if a value is likely a placeholder."""
        placeholder_indicators = [
            'your_', 'your-', 'example', 'placeholder', 'replace_', 'change_',
            'xxx', 'yyy', 'zzz', 'test', 'demo', 'sample', 'fake',
            '123', '000', 'abc', 'def', 'null', 'none', 'empty'
        ]
        
        value_lower = value.lower()
        return any(indicator in value_lower for indicator in placeholder_indicators)
    
    def replace_secrets_with_placeholders(self, secrets: List[SecretLocation]) -> SecurityResult:
        """Replace found secrets with secure placeholders."""
        logger.info(f"Replacing {len(secrets)} secrets with placeholders")
        
        secrets_replaced = 0
        errors = []
        
        # Group secrets by file for efficient processing
        secrets_by_file = {}
        for secret in secrets:
            if secret.file_path not in secrets_by_file:
                secrets_by_file[secret.file_path] = []
            secrets_by_file[secret.file_path].append(secret)
        
        # Process each file
        for file_path, file_secrets in secrets_by_file.items():
            try:
                if self.dry_run:
                    logger.info(f"DRY RUN: Would replace {len(file_secrets)} secrets in {file_path}")
                    secrets_replaced += len(file_secrets)
                else:
                    replaced = self._replace_secrets_in_file(file_path, file_secrets)
                    secrets_replaced += replaced
                    
            except Exception as e:
                error_msg = f"Failed to replace secrets in {file_path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = SecurityResult(
            secrets_found=len(secrets),
            secrets_replaced=secrets_replaced,
            templates_created=0,
            config_files_secured=len(secrets_by_file),
            errors=errors
        )
        
        logger.info(f"Secret replacement complete: {secrets_replaced} secrets replaced")
        return result
    
    def _replace_secrets_in_file(self, file_path: Path, secrets: List[SecretLocation]) -> int:
        """Replace secrets in a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            replacements = 0
            
            # Sort secrets by line number (descending) to avoid offset issues
            secrets.sort(key=lambda s: s.line_number, reverse=True)
            
            for secret in secrets:
                # Generate appropriate placeholder
                placeholder = self._generate_placeholder(secret.secret_type, secret.secret_value)
                
                # Replace the secret value
                content = content.replace(secret.secret_value, placeholder)
                replacements += 1
                
                logger.debug(f"Replaced {secret.secret_type} in {file_path}:{secret.line_number}")
            
            # Write back the file if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return replacements
            
        except Exception as e:
            logger.error(f"Error replacing secrets in {file_path}: {e}")
            return 0
    
    def _generate_placeholder(self, secret_type: str, original_value: str) -> str:
        """Generate an appropriate placeholder for a secret."""
        placeholders = {
            'api_key': 'your_api_key_here',
            'google_api_key': 'your_google_api_key_here',
            'openai_api_key': 'your_openai_api_key_here',
            'anthropic_api_key': 'your_anthropic_api_key_here',
            'database_url': 'your_database_url_here',
            'password': 'your_password_here',
            'secret_key': 'your_secret_key_here',
            'jwt_secret': 'your_jwt_secret_here'
        }
        
        return placeholders.get(secret_type, 'your_secret_here')
    
    def create_secure_templates(self) -> SecurityResult:
        """Create secure configuration templates."""
        logger.info("Creating secure configuration templates")
        
        templates_created = 0
        errors = []
        
        # Find existing configuration files
        config_files = []
        for pattern in self.config_file_patterns:
            config_files.extend(self.root_path.glob(pattern))
        
        # Create .env.example from .env files
        env_files = [f for f in config_files if f.name.startswith('.env') and not f.name.endswith('.example')]
        
        for env_file in env_files:
            try:
                template_path = env_file.parent / f"{env_file.name}.example"
                
                if self.dry_run:
                    logger.info(f"DRY RUN: Would create template {template_path}")
                    templates_created += 1
                else:
                    self._create_env_template(env_file, template_path)
                    templates_created += 1
                    logger.info(f"Created template: {template_path}")
                    
            except Exception as e:
                error_msg = f"Failed to create template for {env_file}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Create security documentation
        try:
            if not self.dry_run:
                self._create_security_documentation()
                templates_created += 1
        except Exception as e:
            error_msg = f"Failed to create security documentation: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        result = SecurityResult(
            secrets_found=0,
            secrets_replaced=0,
            templates_created=templates_created,
            config_files_secured=0,
            errors=errors
        )
        
        logger.info(f"Template creation complete: {templates_created} templates created")
        return result
    
    def _create_env_template(self, env_file: Path, template_path: Path) -> None:
        """Create a secure .env.example template from an .env file."""
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            template_lines = []
            template_lines.append("# Environment Configuration Template\n")
            template_lines.append("# Copy this file to .env and fill in your actual values\n")
            template_lines.append("# DO NOT commit .env files to version control!\n\n")
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    template_lines.append(line + '\n')
                    continue
                
                # Process environment variable lines
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    
                    # Generate placeholder based on key name
                    placeholder = self._generate_env_placeholder(key)
                    template_lines.append(f"{key}={placeholder}\n")
                else:
                    template_lines.append(line + '\n')
            
            # Write template file
            with open(template_path, 'w', encoding='utf-8') as f:
                f.writelines(template_lines)
                
        except Exception as e:
            raise Exception(f"Error creating env template: {e}")
    
    def _generate_env_placeholder(self, key: str) -> str:
        """Generate placeholder value for environment variable."""
        key_lower = key.lower()
        
        if 'api_key' in key_lower or 'key' in key_lower:
            return 'your_api_key_here'
        elif 'password' in key_lower or 'pwd' in key_lower:
            return 'your_password_here'
        elif 'url' in key_lower:
            return 'your_url_here'
        elif 'secret' in key_lower:
            return 'your_secret_here'
        elif 'token' in key_lower:
            return 'your_token_here'
        elif 'host' in key_lower:
            return 'localhost'
        elif 'port' in key_lower:
            return '8000'
        elif 'debug' in key_lower:
            return 'false'
        elif 'env' in key_lower or 'environment' in key_lower:
            return 'production'
        else:
            return 'your_value_here'
    
    def _create_security_documentation(self) -> None:
        """Create security best practices documentation."""
        docs_path = self.root_path / 'docs'
        docs_path.mkdir(exist_ok=True)
        
        security_doc_path = docs_path / 'SECURITY.md'
        
        security_content = """# Security Configuration Guide

## Environment Variables

This project uses environment variables for configuration. Follow these security best practices:

### 1. Environment Files

- **NEVER** commit `.env` files to version control
- Use `.env.example` as a template for required variables
- Copy `.env.example` to `.env` and fill in your actual values

### 2. API Keys and Secrets

- Store all API keys and secrets in environment variables
- Use strong, unique secrets for production
- Rotate API keys regularly
- Never hardcode secrets in source code

### 3. Required Environment Variables

Copy `.env.example` to `.env` and configure these variables:

```bash
# Google Gemini API (Primary LLM)
RASO_GOOGLE_API_KEY=your_google_api_key_here

# Backup LLM Providers (Optional)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Database Configuration
DATABASE_URL=your_database_url_here

# Application Settings
SECRET_KEY=your_secret_key_here
DEBUG=false
ENVIRONMENT=production
```

### 4. Production Deployment

For production deployment:

1. Use a secure secrets management system (AWS Secrets Manager, Azure Key Vault, etc.)
2. Set environment variables through your deployment platform
3. Enable HTTPS/TLS for all communications
4. Use strong authentication and authorization
5. Regularly audit and rotate secrets

### 5. Development Setup

For local development:

1. Copy `.env.example` to `.env`
2. Fill in your development API keys
3. Never commit your `.env` file
4. Use different API keys for development and production

## Security Checklist

- [ ] All secrets moved to environment variables
- [ ] `.env` files added to `.gitignore`
- [ ] `.env.example` templates created
- [ ] Production secrets configured securely
- [ ] API keys rotated regularly
- [ ] HTTPS enabled in production
- [ ] Security headers configured
- [ ] Dependencies regularly updated

## Reporting Security Issues

If you discover a security vulnerability, please report it to the maintainers privately.
Do not create public issues for security vulnerabilities.
"""
        
        with open(security_doc_path, 'w', encoding='utf-8') as f:
            f.write(security_content)
    
    def remove_duplicate_configs(self) -> SecurityResult:
        """Remove duplicate configuration files."""
        logger.info("Removing duplicate configuration files")
        
        files_removed = 0
        errors = []
        
        # Find duplicate config files
        duplicate_patterns = [
            '.env.backup',
            '.env.production',
            '.env.local',
            'config.backup.py',
            'settings.backup.py'
        ]
        
        for pattern in duplicate_patterns:
            duplicate_files = list(self.root_path.rglob(pattern))
            
            for file_path in duplicate_files:
                try:
                    if self.dry_run:
                        logger.info(f"DRY RUN: Would remove duplicate config {file_path}")
                        files_removed += 1
                    else:
                        file_path.unlink()
                        files_removed += 1
                        logger.info(f"Removed duplicate config: {file_path}")
                        
                except Exception as e:
                    error_msg = f"Failed to remove {file_path}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
        
        result = SecurityResult(
            secrets_found=0,
            secrets_replaced=0,
            templates_created=0,
            config_files_secured=files_removed,
            errors=errors
        )
        
        logger.info(f"Duplicate config removal complete: {files_removed} files removed")
        return result
    
    def secure_configuration(self) -> SecurityResult:
        """Execute complete security hardening process."""
        logger.info("Starting complete security hardening")
        
        # Step 1: Scan for secrets
        secrets = self.scan_for_secrets()
        
        # Step 2: Replace secrets with placeholders
        replace_result = self.replace_secrets_with_placeholders(secrets)
        
        # Step 3: Create secure templates
        template_result = self.create_secure_templates()
        
        # Step 4: Remove duplicate configs
        duplicate_result = self.remove_duplicate_configs()
        
        # Combine results
        final_result = SecurityResult(
            secrets_found=replace_result.secrets_found,
            secrets_replaced=replace_result.secrets_replaced,
            templates_created=template_result.templates_created,
            config_files_secured=replace_result.config_files_secured + duplicate_result.config_files_secured,
            errors=replace_result.errors + template_result.errors + duplicate_result.errors
        )
        
        logger.info(f"Security hardening complete: {final_result.secrets_found} secrets found, "
                   f"{final_result.secrets_replaced} replaced, {final_result.templates_created} templates created")
        
        return final_result


def main():
    """Main function for testing security hardener."""
    root_path = Path(".")
    
    # Initialize hardener in dry run mode
    hardener = SecurityHardener(root_path, dry_run=True)
    
    print("🔒 RASO Security Hardener")
    print("=" * 50)
    
    # Scan for secrets
    print("\n🔍 Scanning for exposed secrets...")
    secrets = hardener.scan_for_secrets()
    
    print(f"  • Found {len(secrets)} potential secrets")
    
    # Show sample secrets (safely)
    if secrets:
        print(f"\n📋 Sample findings:")
        for secret in secrets[:5]:
            print(f"  • {secret.secret_type} in {secret.file_path}:{secret.line_number}")
    
    # Test security hardening (dry run)
    print(f"\n🚀 Testing security hardening (dry run)...")
    result = hardener.secure_configuration()
    
    print(f"  ✅ Would replace {result.secrets_replaced} secrets")
    print(f"  ✅ Would create {result.templates_created} templates")
    print(f"  ✅ Would secure {result.config_files_secured} config files")
    
    if result.errors:
        print(f"  ⚠️ {len(result.errors)} errors would occur:")
        for error in result.errors[:3]:
            print(f"    • {error}")
    
    # Save results
    results_path = Path("security_analysis.json")
    with open(results_path, 'w') as f:
        json.dump({
            'secrets_found': [s.to_dict() for s in secrets],
            'security_result': result.to_dict()
        }, f, indent=2)
    
    print(f"\n📄 Security analysis saved: {results_path}")


if __name__ == "__main__":
    main()