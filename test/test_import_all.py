from __future__ import print_function

import os
from os import path
import inspect
import pytest

import oneagent
from oneagent._impl.native import nativeagent
from oneagent._impl.native.sdkmockiface import SDKMockInterface
from oneagent._impl import six
from oneagent import common as sdkcommon
import oneagent._impl.native.sdkctypesiface as csdk
import oneagent._impl.native.sdkmockiface as msdk
import oneagent._impl.native.sdknulliface as nsdk

ignoredmods = set([
    'oneagent.launch_by_import',
    ])

@pytest.fixture(scope='module', autouse=True)
def set_sdk():
    nativeagent.initialize(SDKMockInterface())

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
        return '({})'.format(', '.join(len(func.argtypes) * ['arg']))
    spec = inspect.getargspec(func)
    if spec.args and spec.args[0] == 'self':
        #pylint:disable=no-member,protected-access
        spec = spec._replace(args=spec.args[1:])
    return inspect.formatargspec(*spec, formatarg=lambda arg: 'arg')

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
