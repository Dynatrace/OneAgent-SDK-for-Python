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

from __future__ import print_function

import os
from os import path
import inspect
import pytest

import oneagent
from oneagent._impl.native import nativeagent
from oneagent._impl import six
from oneagent import common as sdkcommon
import oneagent._impl.native.sdkctypesiface as csdk
import oneagent._impl.native.sdknulliface as nsdk

import sdkmockiface as msdk
from sdkmockiface import SDKMockInterface

try:
    getfullargspec = inspect.getfullargspec
except AttributeError:
    getfullargspec = inspect.getargspec

ignoredmods = set([
    'oneagent.launch_by_import',
    ])

@pytest.fixture(scope='module', autouse=True)
def set_sdk():
    nativeagent.initialize(SDKMockInterface())
    yield set_sdk
    nativeagent._force_initialize(None) #pylint:disable=protected-access

def test_import_all():
    pkgroot = path.dirname(oneagent.__file__)
    for root, dirs, files in os.walk(pkgroot):
        try:
            dirs.remove('__pycache__')
        except ValueError:
            pass
        for fname in files:
            name, ext = path.splitext(fname)
            if ext != '.py':
                continue
            fullmodname = root[len(pkgroot):].strip('/\\')
            fullmodname = fullmodname.replace('/', '.').replace('\\', '.')
            fullmodname = 'oneagent.' + fullmodname
            if name != '__init__':
                if not fullmodname.endswith('.'):
                    fullmodname += '.'
                fullmodname += name
            fullmodname = fullmodname.strip('.')
            if fullmodname in ignoredmods:
                continue
            if six.PY2 and 'py3' in fullmodname:
                continue
            print('Importing', fullmodname)
            __import__(fullmodname)


def pubnames(obj):
    return frozenset(name for name in dir(obj) if not name.startswith('_'))

@pytest.fixture(scope='module')
def csdkinst():
    sdk = csdk.loadsdk()
    assert isinstance(sdk, csdk.SDKDllInterface)
    return sdk

@pytest.mark.dependsnative
def test_sdkctypesiface_smoke(csdkinst):
    sdk = csdkinst
    nativeagent.checkresult(
        sdk, sdk.stub_set_variable('agentactive=true', False))
    state = sdk.agent_get_current_state()
    assert state == sdkcommon.AgentState.NOT_INITIALIZED
    sdk.stub_free_variables()

def argstr(func):
    while hasattr(func, '__wrapped__'):
        func = func.__wrapped__
    #pylint:disable=deprecated-method
    if not inspect.ismethod(func) and not inspect.isfunction(func):
        return '({})'.format(', '.join('_arg' + str(i) for i in range(len(func.argtypes))))
    sig = inspect.signature(func)
    iparams = iter(sig.parameters)
    if sig.parameters and next(iparams) == 'self':
        #pylint:disable=no-member,protected-access
        sig = sig.replace(parameters=[sig.parameters[k] for k in iparams])
    nparams = []
    for i, param in enumerate(sig.parameters.values()):
        if param.kind != inspect.Parameter.KEYWORD_ONLY:
            param = param.replace(name="_arg" + str(i))
        nparams.append(param)

    return str(sig.replace(parameters=nparams))

def check_sdk_iface(csdkinst, actual):
    cnames = pubnames(csdkinst)
    anames = pubnames(actual)
    missing = cnames - anames
    assert not missing
    for name in cnames:
        cfunc = getattr(csdkinst, name)
        if not callable(cfunc):
            continue
        cargspec = argstr(cfunc)
        aargspec = argstr(getattr(actual, name))
        try:
            assert cargspec == aargspec
        except AssertionError as e:
            raise AssertionError('Mismatch for {}: {}'.format(name, str(e)))


    return anames - cnames

@pytest.mark.dependsnative
def test_mock_sdk_impl_match(csdkinst):
    print(
        'Additional names in SDKMockInterface: ',
        ', '.join(check_sdk_iface(csdkinst, msdk.SDKMockInterface)))

@pytest.mark.dependsnative
def test_null_sdk_impl_match(csdkinst):
    nulliface = nsdk.SDKNullInterface()
    # No additional names allowed in SDKNullInterface, it should be minimal
    assert not check_sdk_iface(csdkinst, nulliface)
