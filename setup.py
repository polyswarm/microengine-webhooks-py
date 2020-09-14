# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

try:
    long_description = open("README.rst").read()
except IOError:
    long_description = ""

setup(
    name="microenginewebhookspy",
    version="0.1.0",
    description="Exemplar microengine using webhooks for upcoming API changes",
    license="MIT",
    author="PolySwarm Developers",
    packages=find_packages(),
    install_requires=[
        "celery",
        "Flask",
        "requests"
    ],
    long_description=long_description,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
