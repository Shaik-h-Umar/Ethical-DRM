"""
Setup script for EthicalDRM package.
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "EthicalDRM - Ethical Digital Rights Management Kit for Indie Creators"

# Read requirements
def read_requirements():
    try:
        with open('requirements.txt', 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return []

setup(
    name="ethicaldrm",
    version="1.0.0",
    author="Ramij Raj",
    author_email="ramijraj.ethicaldrm@proton.me",
    description="Ethical Digital Rights Management Kit for Indie Creators",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/ramijraj/ethicaldrm",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Multimedia :: Video",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.5.0",
        ],
        "api": [
            "gunicorn>=21.2.0",
            "flask-cors>=4.0.0",
        ],
        "telegram": [
            "telethon>=1.28.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "ethicaldrm=ethicaldrm.cli:main",
            "ethicaldrm-api=ethicaldrm.api.app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "ethicaldrm": [
            "*.txt",
            "*.md",
            "*.json",
        ],
    },
    keywords=[
        "drm",
        "watermarking",
        "leak-detection",
        "content-protection",
        "piracy-detection",
        "video-watermarking",
        "indie-creators",
        "ethical-drm",
    ],
    project_urls={
        "Bug Reports": "https://github.com/ramijraj/ethicaldrm/issues",
        "Source": "https://github.com/ramijraj/ethicaldrm",
        "Documentation": "https://github.com/ramijraj/ethicaldrm/wiki",
    },
)