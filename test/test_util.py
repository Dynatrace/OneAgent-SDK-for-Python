# -*- coding: utf-8 -*-

import oneagent._impl.util as util
from oneagent._impl import six
from testhelpers import get_nsdk, exec_with_dummy_tracer

class Foo(object):
    class Inner(object):
        pass

FooError = type('FooError', (RuntimeError,), {})
FooError.__module__ = None
FOO_ERROR_NAME = '<UNKNOWN_MODULE>.FooError'

def test_getfullname_inner():
    name = util.getfullname(Foo.Inner)
    if six.PY3:
        assert name == __name__ + '.Foo.Inner'
    else:
        assert name == __name__ + '.Inner'

def test_getfullname_dyn():
    assert util.getfullname(FooError) == FOO_ERROR_NAME

def exec_with_dummy_node(sdk, func):
    def do_exec_with_dummy_node(tracer):
        with tracer:
            func(tracer)
    return exec_with_dummy_tracer(sdk, do_exec_with_dummy_node)


def test_error_from_exc(sdk):
    nsdk = get_nsdk(sdk)
    def check_exc(func):
        err_code, err_msg = exec_with_dummy_node(sdk, func).err_info
        assert err_code == ValueError.__module__ + '.ValueError'
        assert err_msg == 'test'

    def do_raise_auto(tracer):
        try:
            raise ValueError('test')
        except ValueError:
            util.error_from_exc(nsdk, tracer.handle)

    def do_raise_val_only(tracer):
        util.error_from_exc(nsdk, tracer.handle, ValueError('test'))

    def do_raise_val_ty(tracer):
        util.error_from_exc(nsdk, tracer.handle, ValueError('test'), ValueError)

    def do_raise_val_other_ty(tracer):
        util.error_from_exc(
            nsdk, tracer.handle, ValueError(), RuntimeError)

    check_exc(do_raise_auto)
    check_exc(do_raise_val_only)
    check_exc(do_raise_val_ty)
    err_code, err_msg = exec_with_dummy_node(
        sdk, do_raise_val_other_ty).err_info
    assert err_code == RuntimeError.__module__ + '.RuntimeError'
    assert err_msg == ''

if six.PY3:
    DifficultClass = type(u'DîffîcültClâss', (Exception,), {})

    def test_getfullname_unicode():
        assert util.getfullname(DifficultClass) == __name__ + u'.DîffîcültClâss'

    def test_error_from_unicode_exc(sdk):
        nsdk = get_nsdk(sdk)
        def check_exc(func):
            err_code, _ = exec_with_dummy_node(sdk, func).err_info
            assert err_code == __name__ + '.' + DifficultClass.__name__

        def do_raise(tracer):
            util.error_from_exc(nsdk, tracer.handle, DifficultClass('test'))

        check_exc(do_raise)
