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

import subprocess
import os
from os import path
import sys
from types import ModuleType

def get_nsdk(sdk):
    return sdk._nsdk #pylint:disable=protected-access

def create_dummy_entrypoint(sdk):
    return sdk.trace_incoming_remote_call('ENTRY', 'ENTRY', 'ENTRY')

def run_in_new_interpreter(target, extra_args=(), interpreter_args=()):
    if isinstance(target, ModuleType):
        tmod = target
    else:
        tmod = sys.modules.get(target)

    if tmod:
        pyfile = path.splitext(tmod.__file__)[0] + '.py'
    else:
        pyfile = target

    try:
        args = [sys.executable]
        args.extend(interpreter_args)
        args.append(pyfile)
        args.extend(extra_args)
        env = os.environ.copy()
        env['PYTHONPATH'] = os.pathsep.join(sys.path)
        return subprocess.check_output(
            args,
            env=env,
            stderr=subprocess.STDOUT,
            universal_newlines=True) # Force text mode
    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            'Error ' + str(e.returncode) + ': ' + e.output)

def exec_with_dummy_tracer(sdk, func):
    nsdk = get_nsdk(sdk)
    lbefore = len(nsdk.finished_paths)
    tracer = create_dummy_entrypoint(sdk)
    func(tracer)
    lafter = len(nsdk.finished_paths)
    assert lbefore + 1 == lafter
    return nsdk.finished_paths[-1]
