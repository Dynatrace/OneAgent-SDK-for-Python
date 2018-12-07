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

import traceback
import threading
from testhelpers import create_dummy_entrypoint, get_nsdk

def thread_worker(err, sdk):
    try:
        with create_dummy_entrypoint(sdk):
            pass
    except Exception: #pylint:disable=broad-except
        err.append(traceback.format_exc())



def test_threading(sdk):
    """Regression test for bug where the paththread local was only created on
    the thread where the constructor of the mock sdk was called."""
    err = []
    thread = threading.Thread(
        target=thread_worker,
        args=(err, sdk))
    thread.start()
    with create_dummy_entrypoint(sdk):
        pass
    thread.join()
    if err:
        raise RuntimeError('Exception on ' + thread.name + ': ' + err[0])

    assert len(get_nsdk(sdk).finished_paths) == 2
