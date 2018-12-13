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

import urllib.request as ur
from timeit import default_timer as gtm

import oneagent

def bench():
    with oneagent.get_sdk().trace_incoming_remote_call('a', 'b', 'c'):
        tdf = 0
        t_tot = 0
        t_inner = None
        do_req = ur.AbstractHTTPHandler.do_request_
        def wrap_req(self, req):
            nonlocal tdf
            req.host # pylint:disable=pointless-statement
            tdf += gtm() - t_inner
            return do_req(self, req)
        ur.AbstractHTTPHandler.do_request_ = wrap_req
        ur.HTTPHandler.http_request = wrap_req
        for _ in range(1):
            t_inner = gtm()
            ur.urlopen('http://localhost:8000/polls').close()
            t_tot += gtm() - t_inner
        return t_tot, tdf

if __name__ == '__main__':
    oneagent.initialize()

    t_total, t_diff = bench()

    oneagent.shutdown()
    print(t_total, t_diff, t_diff / t_total)
