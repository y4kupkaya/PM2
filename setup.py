# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
import re


requirements = ["aiofiles>=0.8.0"]
dev_requirements = [
    "pytest>=6.0",
    "pytest-cov>=2.10",
    "pytest-asyncio>=0.18",
    "black>=22.0",
    "flake8>=4.0",
    "mypy>=0.910",
]

with open("pm2/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pm2",
    version=version,
    url="https://projects.yakupkaya.me/pm2",
    description="Professional Python wrapper for PM2 (Process Manager 2) with async support",
    keywords=[
        "process-manager",
        "pm2",
        "pm2-wrapper",
        "async",
        "process-monitoring",
        "devops",
    ],
    author="y4kupkaya",
    author_email="contact@yakupkaya.me",
    license="GNU General Public License v3 (GPLv3)",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Operating System :: POSIX",
        "Operating System :: MacOS",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: System :: Systems Administration",
        "Topic :: System :: Monitoring",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Utilities",
    ],
    packages=find_packages(exclude=["tests", "tests.*", "docs", "docs.*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": dev_requirements,
        "test": ["pytest>=6.0", "pytest-asyncio>=0.18", "pytest-cov>=2.10"],
    },
    zip_safe=False,
    include_package_data=True,
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={
        "Homepage": "https://projects.yakupkaya.me/pm2",
        "Documentation": "https://docs.yakupkaya.me/pm2",
        "Repository": "https://github.com/y4kupkaya/PM2",
        "Bug Reports": "https://github.com/y4kupkaya/PM2/issues",
        "Contribute": "https://github.com/y4kupkaya/PM2/blob/main/CONTRIBUTING.md",
    },
)
