#  Run: pipx install git+https://github.com/EEKIM10/internal-file-server
import os

from setuptools import setup
import subprocess

setup(
    name="internal-file-server",
    version=subprocess.run(
        ("git", "rev-parse", "--short", "HEAD"), encoding="utf-8", capture_output=True
    ).stdout.strip()
    or os.urandom(3).hex() + "-random",
    packages=["src"],
    url="",
    license="",
    author="nexy7574",
    author_email="",
    description="",
    include_package_data=True,
    install_requires=[
        "fastapi==0.78.0",
        "aiofiles==0.8.0",
        "uvicorn[standard]==0.18.2",
        "click==8.1.3",
        "python-pam==2.0.2",
        "humanize==4.2.3",
        "six==1.16.0",
    ],
    package_data={"src": ["base.html"]},
    entry_points={"console_scripts": ["http-file-server = src.run:run_server"]},
)
