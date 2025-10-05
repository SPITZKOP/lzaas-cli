# LZaaS CLI

🚀 **Landing Zone as a Service - Command Line Interface**

A powerful CLI tool for managing AWS Account Factory (AFT) operations through the LZaaS service.

![Version](https://img.shields.io/badge/version-v1.0.0-blue.svg)
![Status](https://img.shields.io/badge/status-production--ready-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![LZaaS](https://img.shields.io/badge/LZaaS-v1.0.0-green.svg)

## Overview

LZaaS CLI provides a streamlined interface for:
- Creating and managing AWS accounts
- Monitoring AFT pipeline status
- Managing account templates
- Migrating existing accounts to LZaaS management

## Quick Start

```bash
# Install LZaaS CLI
./install-lzaas.sh

# Activate the environment
source lzaas-env/bin/activate

# Check system status
lzaas info

# Access complete user documentation
lzaas docs user-guide

# Create your first account
lzaas account create --template dev --email dev@company.com --client-id your-team
```

```bash
# Uinstall LZaaS CLI
./uninstall-lzaas.sh
```

## Installation

See the [Installation Guide](docs/INSTALLATION_GUIDE.md) for detailed setup instructions.

## Documentation

### User Documentation
- **[Complete User Guide](docs/USER_GUIDE.md)** - Comprehensive documentation with business logic explanations
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Command cheat sheet and syntax reference

### Access Documentation via CLI
```bash
# Complete user guide with business logic
lzaas docs user-guide

# Quick command reference
lzaas docs quick-reference

# Installation instructions
lzaas docs installation

# List all available documentation
lzaas docs list
```

### Technical Documentation
- [Installation Guide](docs/INSTALLATION_GUIDE.md)
- [Migration Guide](docs/MIGRATION_GUIDE.md)
- [LZaaS Internals](docs/ARCHITECTURE.md)
- [Release Notes](RELEASE_NOTES.md)

## Essential Commands

### Account Management
```bash
# Create new AWS accounts
lzaas account create --template dev --email dev@company.com --client-id team-alpha

# List existing accounts
lzaas account list

# Check account status
lzaas account status --request-id dev-2025-001
```

### Templates
```bash
# List available account templates
lzaas template list

# Show template details
lzaas template show --name dev
```

### Migration
```bash
# List organizational units
lzaas migrate list-ous

# Migrate existing accounts
lzaas migrate existing-ou --account-id 123456789012 --target-ou "Development" --dry-run
```

### System Status
```bash
# Check AFT pipeline health
lzaas status pipeline

# Display system information
lzaas info
```

### Documentation Access
```bash
# Access complete user guide
lzaas docs user-guide

# Quick command reference
lzaas docs quick-reference

# List all documentation
lzaas docs list
```

## Architecture

The LZaaS CLI interacts with AWS services to manage account lifecycle:

```
LZaaS CLI → DynamoDB (Account Requests) → AFT Pipeline → AWS Organizations
```

## Configuration

The CLI uses AWS profiles for authentication. Configure your AWS credentials:

```bash
# Using AWS SSO (recommended)
aws configure sso

# Using access keys
aws configure --profile lzaas-production

# Use specific profile
lzaas --profile lzaas-production account list
```

## Account Templates

| Template | Purpose | Security Level | Use Case |
|----------|---------|----------------|----------|
| `dev` | Development | Standard | Feature development, testing |
| `staging` | Pre-production | Production-like | UAT, integration testing |
| `production` | Live workloads | Maximum | Production deployments |
| `sandbox` | Experimentation | Basic | Learning, individual testing |

## Support

For comprehensive help and documentation:

1. **User Guide**: `lzaas docs user-guide` - Complete documentation with business logic
2. **Quick Reference**: `lzaas docs quick-reference` - Command cheat sheet
3. **Command Help**: `lzaas --help` or `lzaas <command> --help`
4. **System Status**: `lzaas info` - Check service health
5. **Administrator**: Contact your LZaaS administrator for access issues

## What's New in v1.1.0

- ✅ **Enhanced Documentation**: Comprehensive user guide with business logic explanations
- ✅ **Docs Command**: Built-in documentation access via `lzaas docs`
- ✅ **Migration Support**: Tools for migrating existing accounts to LZaaS management
- ✅ **Improved CLI**: Better error handling and user experience
- ✅ **Template System**: Standardized account configurations for different use cases

## Version

Current version: 1.1.0 (October 1, 2025)

---

**💡 Pro Tip**: Start with `lzaas docs user-guide` for complete documentation including AWS profile configuration, business logic explanations, and detailed workflows.
