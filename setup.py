#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
import re


setup(
    name='factur-x-ng',
    version='0.8.5',
    author='Alexis de Lattre, Manuel Riel, Harshit Joshi',
    author_email='hello@invoice-x.com',
    url='https://github.com/invoice-x/factur-x-ng',
    description='Factur-X: electronic invoicing standard for Germany & France',
    long_description=open('README.rst').read(),
    license='BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: BSD License',
        "Operating System :: OS Independent",
    ],
    keywords='e-invoice ZUGFeRD Factur-X Chorus',
    packages=find_packages(),
    install_requires=[r.strip() for r in
                      open('requirement.txt').read().splitlines()],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': [
            'facturx = bin.cli:main', ],
    },
)
