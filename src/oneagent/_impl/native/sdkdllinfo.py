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

'''Support for :mod:`.sdkctypesiface` and :code:`setup.py`.'''
# This file is imported from setup.py so it must not refer to any other local
# modules

import os
from os import path
import sys

WIN32 = os.name == 'nt'
IS64BIT = sys.maxsize > 2 ** 32

DLL_BASENAME = 'onesdk_shared'
def dll_name():
    if WIN32:
        pfx = ''
        ext = '.dll'
    else:
        pfx = 'lib'
        ext = '.so'
    return pfx + DLL_BASENAME + ext

def _dll_name_in_home(home, libfname=None):
    if libfname is None:
        libfname = dll_name()
    libsubdir = 'lib64' if IS64BIT else 'lib'
    return path.join(home, 'agent', libsubdir, libfname)
