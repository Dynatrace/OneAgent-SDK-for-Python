# -*- coding: utf-8 -*-
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
