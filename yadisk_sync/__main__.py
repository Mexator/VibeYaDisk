#!/usr/bin/env python3
"""
Entry point for running yadisk_sync as a module.

This allows the package to be run with: python -m yadisk_sync
"""

from .cli import cli

if __name__ == '__main__':
    cli()
