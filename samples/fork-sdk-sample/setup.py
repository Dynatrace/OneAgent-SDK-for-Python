#!/usr/bin/env python3
#
# Copyright 2018 Dynatrace LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import io

from setuptools import setup

with io.open('README.md', encoding='utf-8') as readmefile:
    long_description = readmefile.read()
del readmefile

setup(
    py_modules=['fork_sdk_sample'],
    zip_safe=True,
    name='oneagent-sdk-fork-sample',
    version='0.0', # This sample is not separately versioned

    install_requires=['oneagent-sdk==1.*,>=1.3'],

    description='OneAgent SDK for Python: Fork sample application',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/Dynatrace/OneAgent-SDK-for-Python',
    maintainer='Dynatrace LLC',
    maintainer_email='dynatrace.oneagent.sdk@dynatrace.com',
    license='Apache License 2.0',
    entry_points={
        'console_scripts': ['oneagent-sdk-basic-sample=fork_sdk_sample:main'],
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
