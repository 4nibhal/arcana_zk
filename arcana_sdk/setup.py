"""
Setup script for Arcana ZK SDK
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="arcana-zk-sdk",
    version="0.1.0",
    author="Arcana Team",
    author_email="team@arcana-zk.com",
    description="A minimal SDK for interacting with the Arcana ZK Protocol API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/arcana-zk/arcana-zk-protocol",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/arcana-zk/arcana-zk-protocol/issues",
        "Source": "https://github.com/arcana-zk/arcana-zk-protocol",
        "Documentation": "https://docs.arcana-zk.com",
    },
) 