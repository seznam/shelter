#!/usr/bin/env python

from setuptools import setup, find_packages


setup(
    name="shelter",
    version='1.0.0',
    author='Seznam.cz, a.s.',
    author_email="advert-vyvoj@firma.seznam.cz",
    description=(
        "Simple Python's Tornado wrapper which provides helpers for creating"
        "a new project, writing management commands, service processes, ..."
    ),
    license="BSD",
    url='https://github.com/seznam/shelter',
    classifiers=[
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    packages=find_packages(include=['shelter*']),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'tornado>=4.2,<4.3',
        'six',
        'setproctitle<1.2',
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pytest-cov', 'pytest', 'mock'],
    entry_points={
        'console_scripts': [
            'shelter-admin = shelter.main:main',
        ]
    },
)
