# !/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import find_packages, setup
import re


requirements = ["aylak==0.0.6", "aiofiles"]

with open("pm2/__init__.py", encoding="utf-8") as f:
    version = re.findall(r"__version__ = \"(.+)\"", f.read())[0]

with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="pm2",
    version=version,
    url="https://github.com/y4kupkaya/pm2",
    description="Python wrapper for PM2",
    keywords=["process-manager", "pm2", "pm2-py"],
    author="y4kupkaya",
    author_email="contact@yakupkaya.net.tr",
    license="GNU AFFERO GENERAL PUBLIC LICENSE (v3)",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: Implementation",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet",
        "Topic :: Communications",
        "Topic :: Communications :: Chat",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
    ],
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=requirements,
    zip_safe=False,
    long_description=long_description,
    long_description_content_type="text/markdown",
)
