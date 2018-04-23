import urllib.request as ur
from timeit import default_timer as gtm

from oneagent.sdk import SDK

def bench():
    with SDK.get().trace_incoming_remote_call('a', 'b', 'c').start():
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
    t_total, t_diff = bench()
    print(t_total, t_diff, t_diff / t_total)
