"""Setup configuration for AEVORUN: Learned Temporal Test-Scenario Prioritization.
"""

from setuptools import setup, find_packages

setup(
    name="aevorun",
    version="1.0.0",
    description="Learned Temporal Test-Scenario Prioritization (Model: AEVORUN-T1)",
    long_description=open("README.md", "r", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    author="Arin Goel",
    url="https://aevorun.pages.dev",
    project_urls={
        "Documentation": "https://aevorun.pages.dev/#docs",
        "Source": "https://github.com/A35-777/AEVORUN",
        "Issue Tracker": "https://github.com/A35-777/AEVORUN/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "aevorun": ["checkpoints/*", "data/*.json"],
    },
    python_requires=">=3.10",
    install_requires=[
        "numpy>=1.24.0",
        "torch>=2.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "ruff>=0.3.0",
            "build>=1.0.0",
            "twine>=4.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "aevorun=aevorun.cli:main",
        ],
        "pytest11": [
            "aevorun=aevorun.pytest_plugin",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Software Development :: Testing",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
)

