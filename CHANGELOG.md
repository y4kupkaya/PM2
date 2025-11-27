# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-28

### ✨ Added

- **Complete rewrite from scratch** - The entire library has been rebuilt with modern Python practices
- **Full PM2 API coverage** - Support for all major PM2 operations (start, stop, restart, delete, reload, etc.)
- **Async and sync support** - Both synchronous and asynchronous interfaces available
- **Real-time process monitoring** - CPU, memory, uptime, and performance metrics
- **Comprehensive error handling** - Custom exception hierarchy with detailed error messages
- **Type safety** - Full type hints for better IDE support and type checking
- **Professional documentation** - Complete documentation at [docs.yakupkaya.me/pm2](https://docs.yakupkaya.me/pm2)
- **Extensive test coverage** - 95%+ test coverage with both unit and integration tests
- **Production-ready architecture** - Robust design suitable for enterprise environments

### 🔧 Technical Features

- **PM2Manager class** - Main interface for all PM2 operations
- **ProcessStatus enum** - Type-safe process status handling
- **PM2Process dataclass** - Rich process information with metrics
- **Context manager support** - Easy resource management with `async with` and `with` statements
- **Configurable PM2 binary path** - Support for custom PM2 installations
- **Cross-platform compatibility** - Windows, macOS, and Linux support
- **Python 3.8+ support** - Compatible with modern Python versions

### 📚 Documentation

- **Professional project page** - [projects.yakupkaya.me/pm2](https://projects.yakupkaya.me/pm2)
- **Comprehensive documentation** - [docs.yakupkaya.me/pm2](https://docs.yakupkaya.me/pm2)
- **Dual-language README** - English and Turkish documentation
- **Contributing guidelines** - Detailed contribution instructions
- **Code examples** - Practical usage examples and tutorials

### 🛡️ Quality & Reliability

- **GNU General Public License v3.0** - Open source license
- **Professional CI/CD** - Automated testing and quality checks
- **Code formatting** - Black formatter with consistent style
- **Linting** - flake8 and mypy for code quality
- **Pre-commit hooks** - Automated code quality enforcement

### 🚨 Breaking Changes

- **Complete API redesign** - This is a major version with breaking changes from any previous versions
- **New import structure** - Import from `pm2` package instead of previous structure
- **Changed method signatures** - All methods have been redesigned for better usability
- **New error handling** - Custom exception classes replace generic exceptions

### 📦 Dependencies

- **aiofiles>=0.8.0** - For async file operations
- **Python>=3.8** - Minimum Python version requirement

### 🎯 Migration Notes

This version represents a complete rewrite. If upgrading from a previous version:

1. Review the new API in the documentation
2. Update import statements to use the new structure
3. Adapt code to use the new PM2Manager class
4. Update error handling to use new exception classes

---

**Note**: This is the first major release after a complete rewrite. The previous version had significant issues and has been completely rebuilt for production use.

For more details, visit:

- **Project Homepage**: [projects.yakupkaya.me/pm2](https://projects.yakupkaya.me/pm2)
- **Documentation**: [docs.yakupkaya.me/pm2](https://docs.yakupkaya.me/pm2)
- **GitHub Repository**: [github.com/y4kupkaya/PM2](https://github.com/y4kupkaya/PM2)
