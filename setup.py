#!/usr/bin/env python3
"""
Setup script for Yandex.Disk Sync Daemon
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
with open("requirements.txt") as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

setup(
    name="yadisk-sync-daemon",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python CLI application that syncs directories with Yandex.Disk as a daemon process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/yadisk-sync-daemon",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: System :: Archiving :: Backup",
        "Topic :: System :: Filesystems",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "yadisk-sync=main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="yandex disk sync daemon backup cloud storage",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/yadisk-sync-daemon/issues",
        "Source": "https://github.com/yourusername/yadisk-sync-daemon",
        "Documentation": "https://github.com/yourusername/yadisk-sync-daemon#readme",
    },
)




