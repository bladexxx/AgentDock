"""Packaging for the focused CLI-Anything Sand3D harness."""

from setuptools import find_namespace_packages, setup


setup(
    name="cli-anything-sand3d",
    version="0.1.0",
    description="One-shot Sand3D bracket GLB exporter",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={"cli_anything.sand3d": ["skills/*.md"]},
    install_requires=["click>=8.0", "sand3d>=1.6.3"],
    python_requires=">=3.11,!=3.12.*,<3.14",
    entry_points={
        "console_scripts": [
            "cli-anything-sand3d=cli_anything.sand3d.sand3d_cli:main",
        ],
    },
)
