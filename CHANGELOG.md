# Changelog

All notable changes to the LZaaS CLI will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-10-01

### Added
- Initial release of LZaaS CLI
- Account management commands (`account create`, `account list`, `account status`)
- Template management commands (`template list`, `template show`)
- Status monitoring commands (`status check`, `status overview`, `status pipelines`)
- Migration commands (`migrate existing-ou`, `migrate list-ous`)
- Built-in documentation access (`docs user-guide`, `docs quick-reference`)
- Comprehensive user documentation with business logic explanations
- AWS profile configuration support (SSO, access keys, environment variables)
- Account templates: dev, staging, production, sandbox
- DynamoDB integration for account request tracking
- AFT pipeline status monitoring
- Rich CLI interface with colored output and tables
- Comprehensive error handling and validation
- Installation and uninstallation scripts

### Features
- **Account Creation**: Automated AWS account provisioning through AFT
- **Template System**: Pre-configured account templates for different use cases
- **Status Monitoring**: Real-time tracking of account creation progress
- **Migration Support**: Tools for migrating existing accounts to LZaaS management
- **Documentation Integration**: Built-in access to user guides and references
- **AWS Integration**: Seamless integration with AWS Organizations and AFT

### Documentation
- Complete User Guide with business context and workflows
- Quick Reference for command syntax and common operations
- Installation Guide with multiple setup methods
- Troubleshooting guide with common issues and solutions
- AWS profile configuration with detailed explanations

### Security
- No sensitive credentials stored in CLI
- AWS profile-based authentication
- Input validation and sanitization
- Secure API interactions with AWS services

## [Unreleased]

### Planned
- API integration for programmatic access
- GUI web interface for non-technical users
- Enhanced reporting and analytics
- Bulk account operations
- Custom template creation
- Integration with external ITSM systems
- Advanced monitoring and alerting
- Multi-region support
- Cost optimization recommendations

---

## Release Notes

### v1.0.0 - Initial Release

This is the first public release of the LZaaS CLI, providing a comprehensive command-line interface for AWS Account Factory automation. The CLI enables teams to:

- **Create AWS accounts** using standardized templates
- **Monitor account creation** progress in real-time
- **Migrate existing accounts** to LZaaS management
- **Access comprehensive documentation** directly from the CLI

The release includes complete user-facing documentation that explains both the technical implementation and business logic behind each operation, making it accessible to teams of all technical levels.

**Installation**: `pip install lzaas-cli`

**Documentation**: Run `lzaas docs user-guide` for complete documentation

**Support**: See the User Guide for troubleshooting and support channels
