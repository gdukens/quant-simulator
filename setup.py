#!/usr/bin/env python3
"""
Setup script for QuantLib Pro SDK

This file provides additional configuration for building and distributing
the QuantLib Pro package. The main configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
import os
import re

# Read version from __init__.py
def get_version():
    version_file = os.path.join("quantlib_pro", "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r") as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*["\']([^"\']*)["\']', content)
            if match:
                return match.group(1)
    return "1.0.0"

# Read README
def get_long_description():
    readme_file = "SDK_README.md"
    if os.path.exists(readme_file):
        with open(readme_file, "r", encoding="utf-8") as f:
            return f.read()
    return "Enterprise quantitative finance toolkit for Python"

# Read requirements
def get_requirements():
    requirements = []
    req_file = "requirements.txt"
    if os.path.exists(req_file):
        with open(req_file, "r") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return requirements

if __name__ == "__main__":
    setup(
        name="quantlib-pro",
        version=get_version(),
        description="Enterprise Quantitative Finance Platform and SDK",
        long_description=get_long_description(),
        long_description_content_type="text/markdown",
        author="QuantLib Pro Team",
        author_email="info@quantlibpro.com",
        url="https://github.com/quantlib-pro/quantlib-pro",
        project_urls={
            "Documentation": "https://quantlib-pro.readthedocs.io",
            "Source": "https://github.com/quantlib-pro/quantlib-pro",
            "Tracker": "https://github.com/quantlib-pro/quantlib-pro/issues",
        },
        packages=find_packages(exclude=["tests*", "docs*", "examples*"]),
        include_package_data=True,
        package_data={
            "quantlib_pro": ["py.typed", "*.json", "*.yml", "*.yaml"],
        },
        python_requires=">=3.8",
        install_requires=get_requirements(),
        classifiers=[
            "Development Status :: 5 - Production/Stable",
            "Intended Audience :: Financial and Insurance Industry",
            "Intended Audience :: Developers",
            "Intended Audience :: Science/Research",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9", 
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Topic :: Office/Business :: Financial",
            "Topic :: Office/Business :: Financial :: Investment",
            "Topic :: Scientific/Engineering :: Mathematics",
            "Topic :: Software Development :: Libraries :: Python Modules",
            "Typing :: Typed",
        ],
        keywords=[
            "quantitative-finance", "portfolio-optimization", "risk-management",
            "options-pricing", "financial-modeling", "quant", "finance",
            "trading", "investment", "derivatives", "volatility", "var",
            "black-scholes", "monte-carlo", "backtesting"
        ],
        entry_points={
            "console_scripts": [
                "quantlib=quantlib_pro.cli:main",
            ],
        },
        zip_safe=False,
        
        # Extra metadata
        extras_require={
            "sdk": [
                "numpy>=1.26.4",
                "pandas>=2.2.3",
                "scipy>=1.12.0",
                "requests>=2.31.0"
            ],
            "full": [
                "streamlit>=1.32.0",
                "fastapi>=0.110.0",
                "plotly>=5.20.0",
                "redis>=5.0.0"
            ],
            "data": [
                "yfinance>=0.2.48",
                "alpha-vantage>=2.3.1",
                "fredapi>=0.5.0"
            ],
            "ml": [
                "scikit-learn>=1.4.0",
                "tensorflow>=2.15.0",
                "xgboost>=2.0.0"
            ],
            "dev": [
                "pytest>=8.0.0",
                "black>=24.0.0",
                "mypy>=1.8.0",
                "flake8>=7.0.0"
            ]
        }
    )