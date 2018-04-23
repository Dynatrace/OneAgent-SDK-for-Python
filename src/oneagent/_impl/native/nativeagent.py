# -*- coding: utf-8 -*-
'''Provides access to the native SDK object and entry point of it's
initialization for higher levels.
'''

from oneagent.common import SDKError

_sdk = None

def _force_initialize(sdkinit):
    global _sdk #pylint:disable=global-statement
    _sdk = sdkinit
    return _sdk

def initialize(sdkinit=None):
    if _sdk:
        raise ValueError('Agent is already initialized.')
    if not sdkinit or isinstance(sdkinit, str):
        from .sdkctypesiface import loadsdk
        return _force_initialize(loadsdk(sdkinit))
    return _force_initialize(sdkinit)

def checkresult(nsdk, error_code, msg=None):
    if error_code == 0:
        return error_code
    emsg = nsdk.strerror(error_code)
    if msg:
        raise SDKError(error_code, msg + ': ' + emsg)
    raise SDKError(error_code, emsg)

def get_sdk():
    if not _sdk:
        raise ValueError('SDK not loaded')
    return _sdk

def try_get_sdk():
    return _sdk
