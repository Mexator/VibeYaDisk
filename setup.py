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
    author = "Cursor (Промптил я, AHTOXA)"
    author_email = "ahtoxa@ahtoxa.ru"
    description="A Python CLI application that syncs directories with Yandex.Disk as a daemon process",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Mexator/VibeYaDisk",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
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
            "yadisk-sync=yadisk_sync.cli:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
    keywords="yandex disk sync daemon backup cloud storage",
    project_urls={
        "Bug Reports": "https://github.com/Mexator/VibeYaDisk/issues",
        "Source": "https://github.com/Mexator/VibeYaDisk",
        "Documentation": "https://github.com/Mexator/VibeYaDisk#readme",
    },
)




