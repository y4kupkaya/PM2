
# 🚀 PM2 Python Library

## Professional Python wrapper for PM2 Process Manager

[![PyPI version](https://badge.fury.io/py/pm2.svg)](https://badge.fury.io/py/pm2)
[![Python Support](https://img.shields.io/pypi/pyversions/pm2.svg)](https://pypi.org/project/pm2/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Downloads](https://pepy.tech/badge/pm2)](https://pepy.tech/project/pm2)

**🔥 [Project Homepage](https://projects.yakupkaya.me/pm2) | 📚 [Complete Documentation](https://docs.yakupkaya.me/pm2)**

---

> **⚠️ IMPORTANT:** This project received its **first major update since January 2024**, featuring a **complete rewrite from scratch**. The previous buggy version has been entirely redesigned and significantly improved. Please refer to the **[new documentation site](https://docs.yakupkaya.me/pm2)** for the latest information.

**🌍 Language:** [🇺🇸 English](README.md) | [🇹🇷 Türkçe](README_TR.md)

### ✨ Overview

A powerful, production-ready Python library that provides seamless integration with **[PM2 Process Manager](https://pm2.keymetrics.io/)** - the industry-standard runtime process manager for Node.js applications. This library extends PM2's capabilities to Python environments, enabling developers and system administrators to programmatically control their processes with the reliability and flexibility of Python.

**PM2** is a battle-tested, feature-rich production process manager that has been trusted by thousands of companies worldwide to manage their Node.js applications in production environments. Our Python wrapper brings this enterprise-grade process management power directly to your Python applications and scripts.

**🎯 Perfect for:** Web applications, microservices, background tasks, data processing pipelines, and production deployments.

### 🚨 New Version Notice

This library received its **first major update since January 2024** and has been **completely rewritten from scratch** to address all issues from the previous version. The new version features:

- **Complete code rewrite** with modern Python practices
- **Enhanced reliability** and error handling
- **Comprehensive documentation** at **[docs.yakupkaya.me/pm2](https://docs.yakupkaya.me/pm2)**
- **Professional project page** at **[projects.yakupkaya.me/pm2](https://projects.yakupkaya.me/pm2)**

### 🚀 Key Features

| Feature | Description |
|---------|-------------|
| **🔄 Complete Process Control** | Start, stop, restart, reload, and delete processes |
| **⚡ Async & Sync Support** | Both synchronous and asynchronous interfaces |
| **📊 Real-time Monitoring** | CPU, memory, uptime, and performance metrics |
| **🛡️ Production Ready** | Comprehensive error handling and robust architecture |
| **🔧 Flexible Configuration** | Environment variables, custom settings, and deployment options |
| **📝 Rich Process Info** | Detailed insights including logs, status, and health metrics |

### 📖 Documentation

**👆 Please visit our main documentation site for complete information:**

- **🌟 [Project Homepage](https://projects.yakupkaya.me/pm2)** - Official project page
- **🏠 [Main Documentation](https://docs.yakupkaya.me/pm2)** - Complete guide and tutorials
- **🔥 [Examples](https://projects.yakupkaya.me/pm2/examples.html)** - Practical code examples
- **⚙️ [Advanced Usage](https://projects.yakupkaya.me/pm2/advanced-usage.html)** - Advanced patterns and configurations
- **🔧 [Troubleshooting](https://projects.yakupkaya.me/pm2/troubleshooting.html)** - Solutions to common issues

### 📦 Installation

```bash
# Install from PyPI (recommended)
pip install pm2

# Or install from source
git clone https://github.com/y4kupkaya/PM2.git
cd PM2
pip install -e .
```

### ⚡ Quick Start

```python
from pm2 import PM2Manager

# Initialize PM2 manager
pm2 = PM2Manager()

# Start a process
process = pm2.start_app(
    script="app.py",
    name="my-app",
    env={"PORT": "3000"}
)

# Monitor the process
print(f"Status: {process.status}")
print(f"CPU: {process.metrics.cpu}%")
print(f"Memory: {process.metrics.memory_mb} MB")

# List all processes
for proc in pm2.list_processes():
    print(f"{proc.name}: {proc.status}")
```

### 🌟 Why Choose PM2 Python Library?

- **🎯 Production Ready** - Battle-tested in production environments
- **📈 High Performance** - Optimized for minimal overhead
- **🔒 Type Safe** - Full type hints and mypy compatibility  
- **🧪 Well Tested** - Comprehensive test suite with 95%+ coverage
- **📚 Great Documentation** - Extensive docs with real-world examples

---

## 📋 Prerequisites

**PM2** must be installed on your system. PM2 is the world's most popular production process manager for Node.js applications, trusted by companies like Microsoft, IBM, and Netflix for managing critical production workloads.

```bash
# Install PM2 globally
npm install -g pm2

# Verify installation
pm2 --version
```

**About PM2:** PM2 (Process Manager 2) is an advanced, production-grade runtime and process manager for Node.js applications. It provides features like automatic restarts, load balancing, memory monitoring, and seamless deployments. Learn more at [pm2.keymetrics.io](https://pm2.keymetrics.io/).

## 🔧 Advanced Usage

For advanced patterns, async operations, production deployments, and complex configurations, visit our **[Advanced Usage Guide](https://projects.yakupkaya.me/pm2/advanced-usage.html)**.

## 🐛 Troubleshooting

Having issues? Check our **[Troubleshooting Guide](https://projects.yakupkaya.me/pm2/troubleshooting.html)** for solutions to common problems.

## 🤝 Contributing

We welcome contributions! Please see our **[Contributing Guidelines](CONTRIBUTING.md)** for details.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **PM2 Team** - For creating the amazing PM2 process manager
- **Community Contributors** - Thank you for your valuable contributions
- **Users** - For testing and providing feedback to make this library better

## 📞 Support

- 🌟 [Project Homepage](https://projects.yakupkaya.me/pm2)
- 📚 [Documentation](https://docs.yakupkaya.me/pm2)
- 🐛 [Issue Tracker](https://github.com/y4kupkaya/PM2/issues)
- 📧 [Author Website](https://yakupkaya.me)

---

**Made with ❤️ by [Yakup Kaya](https://yakupkaya.me)**
