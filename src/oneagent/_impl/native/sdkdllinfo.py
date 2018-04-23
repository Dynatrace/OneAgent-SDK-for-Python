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
