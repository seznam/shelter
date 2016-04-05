#!/usr/bin/env python

import sys

from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):

    user_options = [
        ('pytest-args=', 'a', "Arguments to pass to py.test"),
    ]

    def initialize_options(self):
        TestCommand.initialize_options(self)
        self.pytest_args = []

    def run_tests(self):
        import pytest
        errno = pytest.main(self.pytest_args)
        sys.exit(errno)


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
    tests_require=[
        'pytest-cov',
        'pytest',
        'mock',
    ],
    test_suite='tests',
    cmdclass={
        'test': PyTest,
    },
    entry_points={
        'console_scripts': [
            'shelter-admin = shelter.main:main',
        ]
    },
)
