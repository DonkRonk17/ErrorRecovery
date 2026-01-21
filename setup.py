#!/usr/bin/env python3
"""Setup script for ErrorRecovery."""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="errorrecovery",
    version="1.0.0",
    author="Forge (Team Brain)",
    author_email="logan@metaphy.dev",
    description="Intelligent error detection and recovery system with pattern matching and learning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/DonkRonk17/ErrorRecovery",
    py_modules=["errorrecovery"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Recovery Tools",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "errorrecovery=errorrecovery:main",
        ],
    },
    keywords=[
        "error-handling",
        "recovery",
        "retry",
        "fallback",
        "pattern-matching",
        "automation",
        "team-brain",
        "q-mode"
    ],
    project_urls={
        "Bug Reports": "https://github.com/DonkRonk17/ErrorRecovery/issues",
        "Source": "https://github.com/DonkRonk17/ErrorRecovery",
    },
)
