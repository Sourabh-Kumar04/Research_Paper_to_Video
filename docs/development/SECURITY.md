# Security Configuration Guide

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
