#!/usr/bin/env python3

import io

from setuptools import setup

with io.open('README.md', encoding='utf-8') as readmefile:
    long_description = readmefile.read()
del readmefile

setup(
    py_modules=['basic_sdk_sample'],
    zip_safe=True,
    name='oneagent-sdk-basic-sample',
    version='0.0', # This sample is not separately versioned

    install_requires=['oneagent-sdk==1.*,>=1.0'],

    description='OneAgent SDK for Python: Basic sample application',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Dynatrace/OneAgent-SDK-for-Python',
    maintainer='Dynatrace LLC',
    maintainer_email='dynatrace.oneagent.sdk@dynatrace.com',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': ['oneagent-sdk-basic-sample=basic_sdk_sample:main'],
    },
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved',
        'License :: OSI Approved :: Apache Software License', # 2.0
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: Implementation :: CPython',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: System :: Monitoring'
    ])
