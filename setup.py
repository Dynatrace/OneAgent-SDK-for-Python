#! /usr/bin/env python3

# Beware when cross-building 64/32 bit:
# When using --plat-name to override this, make sure to `rm -r build` othewise
# files from the wrong platform might be reused.
# Also, on Linux because of https://bugs.python.org/issue18987, using a 32 bit
# Python on a 64 bit OS is not enough to change the platform tag.

from __future__ import print_function

import io
import os
from os import path
import re

# https://github.com/PyCQA/pylint/issues/73
#pylint:disable=no-name-in-module,import-error
from distutils.util import get_platform
from distutils.command.build import build
#pylint:enable=no-name-in-module,import-error


from setuptools import setup, find_packages, Distribution
from setuptools.command.install import install
from setuptools.command.build_ext import build_ext

try:
    from wheel.bdist_wheel import bdist_wheel
except ImportError:
    bdist_wheel = None

CSDK_ENV_NAME = 'DT_PYSDK_CSDK_PATH'

_THIS_DIR = path.dirname(path.abspath(__file__))

with io.open(path.join(_THIS_DIR, 'README.md'), encoding='utf-8') as readmefile:
    long_description = readmefile.read()
del readmefile

VER_RE = re.compile(r"^__version__ = '([^']+)'$")

verfilepath = path.join(_THIS_DIR, 'src/oneagent/__init__.py')
with io.open(verfilepath, encoding='utf-8') as verfile:
    for line in verfile:
        match = VER_RE.match(line)
        if match:
            __version__ = match.group(1)
            break
    else:
        raise AssertionError('Version not found in src/oneagent/__init__.py')
del match, verfile, verfilepath, VER_RE


def compilefile(fname, mode='exec'):
    with open(fname) as srcfile:
        codestr = srcfile.read()
    return compile(codestr, fname, mode)

def adjust_plat_name(self):
    #pylint:disable=access-member-before-definition
    if self.plat_name is not None:
        return
    baseplat = get_platform()
    if baseplat.startswith('linux'):
        platname = baseplat.split('-', 2)
        platname[0] = 'manylinux1'
        #pylint:disable=attribute-defined-outside-init
        self.plat_name = '-'.join(platname)
    else:
        self.plat_name = baseplat

if bdist_wheel is not None:
    class BdistWheel(bdist_wheel):
        def finalize_options(self):
            adjust_plat_name(self)
            bdist_wheel.finalize_options(self)

        def get_tag(self):
            plat_name = self.plat_name or get_platform()
            plat_name = plat_name.replace('-', '_').replace('.', '_')
            return (
                'py2.py3' if self.universal else self.python_tag, # impl-tag
                'none', # abi-tag
                plat_name)

def get_dll_info(plat_name):
    dll_info = {}
    #pylint:disable=exec-used
    infopath = path.join(_THIS_DIR, 'src/oneagent/_impl/native/sdkdllinfo.py')
    exec(compilefile(infopath), dll_info)
    if plat_name:
        is_win32 = plat_name.startswith('win')
        is_64bit = plat_name.endswith('64')
        dll_info['IS64BIT'] = is_64bit
        dll_info['WIN32'] = is_win32
    return dll_info

def get_dll_input_path(plat_name):
    sdkpath = os.getenv(CSDK_ENV_NAME)
    if not sdkpath:
        raise ValueError(
            'Need to set {} to point to SDK stub shared library.'.format(
                CSDK_ENV_NAME))
    if path.isdir(sdkpath):
        return get_dll_info(plat_name)['_dll_name_in_home'](sdkpath)
    return sdkpath

class PostBuildCommand(build):
    __base = build

    def finalize_options(self):
        #pylint:disable=access-member-before-definition
        has_build_lib = self.build_lib is not None
        self.__base.finalize_options(self)
        if not has_build_lib:
            #pylint:disable=attribute-defined-outside-init
            self.build_lib = self.build_platlib


class PostBuildExtCommand(build_ext):
    __base = build_ext

    def finalize_options(self):
        self.__base.finalize_options(self)

    def get_dll_output_path(self):
        targetdir = path.join(
            self.build_lib,
            'oneagent',
            '_impl',
            'native')
        return path.join(targetdir, get_dll_info(self.plat_name)['dll_name']())

    def get_outputs(self):
        return self.__base.get_outputs(self) + [self.get_dll_output_path()]

    def get_inputs(self):
        try:
            dll_input = get_dll_input_path(self.plat_name)
        except ValueError:
            return self.__base.get_inputs(self)
        else:
            return self.__base.get_inputs(self) + [dll_input]

    def run(self):
        src = get_dll_input_path(self.plat_name)
        dst = self.get_dll_output_path()
        self.__base.run(self)
        self.mkpath(path.dirname(dst))
        self.copy_file(src, dst)

    def copy_extensions_to_source(self):
        self.__base.copy_extensions_to_source(self)

        build_py = self.get_finalized_command('build_py')
        src_filename = self.get_dll_output_path()
        package = 'oneagent._impl.native'
        package_dir = build_py.get_package_dir(package)
        dest_filename = path.join(package_dir, path.basename(src_filename))
        self.copy_file(src_filename, dest_filename)



class PostInstallCommand(install):
    def finalize_options(self):
        #pylint:disable=access-member-before-definition
        if self.install_lib is None:
            #pylint:disable=attribute-defined-outside-init
            self.install_lib = self.install_platlib
        return install.finalize_options(self)

class BinaryDistribution(Distribution):
    def has_ext_modules(self): #pylint:disable=no-self-use
        return True

cmdclss = {
    'build': PostBuildCommand,
    'build_ext': PostBuildExtCommand,
    'install': PostInstallCommand,
}

if bdist_wheel is not None:
    cmdclss['bdist_wheel'] = BdistWheel

def main():
    setup(
        packages=find_packages('src'),
        package_dir={'': 'src'},
        include_package_data=True,
        zip_safe=True,
        python_requires='>=2.7,!=3.0,!=3.1,!=3.2,!=3.3',
        cmdclass=cmdclss,
        name='oneagent-sdk',
        version=__version__,
        distclass=BinaryDistribution,

        description='Dynatrace OneAgent SDK for Python',
        long_description=long_description,
        long_description_content_type='text/markdown',
        url='https://www.dynatrace.com/',
        maintainer='Dynatrace LLC',
        maintainer_email='dynatrace.oneagent.sdk@dynatrace.com',
        license='Apache License 2.0',
        classifiers=[
            'Development Status :: 2 - Pre-Alpha',
            'Intended Audience :: Developers',
            'License :: OSI Approved :: Apache Software License', # 2.0
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.3',
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6',
            'Programming Language :: Python :: Implementation :: CPython',
            #'Programming Language :: Python :: Implementation :: PyPy',
            'Operating System :: POSIX :: Linux',
            'Operating System :: Microsoft :: Windows',
            'Topic :: Software Development :: Libraries',
            'Topic :: System :: Monitoring'
        ])

if __name__ == '__main__':
    main()
