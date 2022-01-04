#!/usr/bin/env python

from setuptools import setup


setup(
    name="exampleapp",
    version='0.0.0',
    author='Seznam.cz, a.s.',
    author_email="jan.seifert@firma.seznam.cz",
    description=(
        "Example application which use Shelter."
    ),
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    packages=['exampleapp'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'shelter',
        'setproctitle<1.2',
    ],
    entry_points={
        'console_scripts': [
            'manage-exampleapp = exampleapp:main',
        ]
    },
)
