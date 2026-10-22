from setuptools import setup, find_packages

setup(
    name="file_monitor",
    version="1.1.1",
    description="Dynatrace OneAgent Extension 2.0 — File Monitor",
    author="CareFirst BlueCross BlueShield",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=[
        "dt-extensions-sdk>=1.0.0",
    ],
)
