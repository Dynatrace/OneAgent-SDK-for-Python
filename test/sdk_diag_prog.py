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

'''Helper module for .test_run_public_sdk.test_sdk_callback_smoke'''

from __future__ import print_function

import sys
import gc

import oneagent
from oneagent._impl import six
from oneagent import sdk as onesdk

def main():
    call_msg = []

    init_result = oneagent.initialize()
    if not init_result:
        print(init_result, file=sys.stderr)
        sys.exit(1)


    def diag_cb(msg):
        sys.stderr.flush()
        call_msg.append(msg)

    sdk = oneagent.get_sdk()
    try:
        sdk.set_diagnostic_callback(diag_cb)
        sdk.create_database_info(None, None, onesdk.Channel(0))
        gc.collect()
        gc.collect()
        gc.collect()
        print(call_msg)
        n_msgs = len(call_msg)

        # Database name must not be null (from CSDK), leaked db info handle
        assert n_msgs == 2

        assert all(isinstance(m, six.text_type) for m in call_msg)
        sdk.set_diagnostic_callback(None)
        sdk.create_database_info(None, None, onesdk.Channel(0))
        print(call_msg[n_msgs:])
        assert len(call_msg) == n_msgs
    finally:
        oneagent.shutdown()

if __name__ == '__main__':
    main()
