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

import pytest

from oneagent import sdk as onesdk
from oneagent._impl import six
from oneagent._impl.native import nativeagent

import sdkmockiface

from testhelpers import (
    get_nsdk,
    create_dummy_entrypoint,
    run_in_new_interpreter)
from . import sdk_diag_prog

RTERR_QNAME = RuntimeError.__module__ + '.RuntimeError'

def test_trace_in_remote_call(sdk):
    with sdk.trace_incoming_remote_call('a', 'b', 'c'):
        pass
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    root = nsdk.finished_paths[0]
    assert isinstance(root, sdkmockiface.InRemoteCallHandle)
    assert root.vals == ('a', 'b', 'c')

def test_trace_out_remote_call(sdk):
    print('SDK:', sdk)
    with create_dummy_entrypoint(sdk):
        print('SDK2:', sdk)
        tracer = sdk.trace_outgoing_remote_call(
            'a',
            'b',
            'c',
            onesdk.Channel(onesdk.ChannelType.OTHER, 'e'),
            protocol_name='foo')
        tracer.start()
        tracer.end()
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    _, root = nsdk.finished_paths[0].children[0]
    assert isinstance(root, sdkmockiface.OutRemoteCallHandle)
    assert root.vals == ('a', 'b', 'c', onesdk.ChannelType.OTHER, 'e')
    assert root.protocol_name == 'foo'

def test_trace_error(sdk):
    try:
        with sdk.trace_incoming_remote_call('a', 'b', 'c'):
            raise RuntimeError('bla')
    except RuntimeError:
        pass
    else:
        assert not 'Exception seems to have been swallowed!'
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    root = nsdk.finished_paths[0]
    assert isinstance(root, sdkmockiface.InRemoteCallHandle)
    assert root.vals == ('a', 'b', 'c')
    assert root.err_info == (RTERR_QNAME, 'bla')


DUMMY_SQL = 'SELECT * FROM tbl;'

def test_trace_sql_database_request(sdk):
    with create_dummy_entrypoint(sdk):
        dbi = sdk.create_database_info(
            'dbn', 'dbv', onesdk.Channel(onesdk.ChannelType.OTHER, 'ce'))
        hdbi = dbi.handle
        with dbi:
            tracer = sdk.trace_sql_database_request(dbi, DUMMY_SQL)
            with tracer:
                tracer.set_round_trip_count(1)
                tracer.set_rows_returned(42)
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    _, root = nsdk.finished_paths[0].children[0] # Strip dummy entrypoint
    assert isinstance(root, sdkmockiface.DbRequestHandle)
    assert root.vals[0] is hdbi
    assert root.vals[1] == DUMMY_SQL
    assert root.round_trip_count == 1
    assert root.returned_row_count == 42

DUMMY_URL = 'http://a/b/c'

def test_trace_iwr_minimal(sdk):
    with sdk.create_web_application_info('a', 'b', '/b') as wapp:
        wreq = sdk.trace_incoming_web_request(wapp, DUMMY_URL, 'GET')
        with wreq:
            pass
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    root = nsdk.finished_paths[0]
    assert isinstance(root, sdkmockiface.InWebReqHandle)
    assert root.vals[1:] == (DUMMY_URL, 'GET')
    assert root.vals[0].vals == ('a', 'b', '/b')

def test_trace_iwr_full(sdk):
    '''Tests an incoming web request with all optional properties (excluding
    tag) set.'''
    dummy_hdrs = {
        'X-MyHeader': 'my-value',
        'X-MyOtherHeader': 'another value'}
    dummy_len = 2
    dummy_params = (
        ['username', 'password', 'csrf'],
        ('heinz', 'seb2009', 'dummy', 'overlong'),
        dummy_len # Skip additional
    )
    dummy_params_x = (iter(dummy_params[0]), dummy_params[1], 2)
    with sdk.create_web_application_info('a', 'b', '/b') as wapp:
        wreq = sdk.trace_incoming_web_request(
            wapp,
            DUMMY_URL,
            'GET',
            headers=dummy_hdrs,
            remote_address='127.0.0.1')
        with wreq:
            wreq.add_parameters(*dummy_params)
            wreq.add_parameter('p2', 'vp2')
            wreq.add_response_header('Location', DUMMY_URL)
            wreq.add_response_headers(*dummy_params)
            wreq.set_status_code(200)
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    root = nsdk.finished_paths[0]
    assert isinstance(root, sdkmockiface.InWebReqHandle)
    assert root.vals[1:] == (DUMMY_URL, 'GET')
    assert root.vals[0].vals == ('a', 'b', '/b')
    assert root.req_hdrs == list(dummy_hdrs.items())
    assert root.params == [
        ('username', 'heinz'),
        ('password', 'seb2009'),
        ('p2', 'vp2')]
    assert root.resp_hdrs == [
        ('Location', DUMMY_URL),
        ('username', 'heinz'),
        ('password', 'seb2009')]
    assert root.resp_code == 200
    assert root.remote_addr == '127.0.0.1'

def test_trace_iwr_autocount(sdk):
    with sdk.create_web_application_info('a', 'b', '/b') as wapp:
        wreq = sdk.trace_incoming_web_request(
            wapp, DUMMY_URL, 'GET', headers=(['x', 'y'], ['xv', 'yv']))
        with wreq:
            wreq.add_response_headers(['u'], ['uv'])
    nsdk = get_nsdk(sdk)
    assert len(nsdk.finished_paths) == 1
    root = nsdk.finished_paths[0]
    assert root.req_hdrs == [('x', 'xv'), ('y', 'yv')]
    assert root.resp_hdrs == [('u', 'uv')]

def assert_resolve_all(nsdk):
    unresolved = nsdk.process_finished_paths_tags()
    if not unresolved:
        return
    raise AssertionError('{} nodes with unresolved in-tags: {}'.format(
        len(unresolved), ', '.join(map(str, unresolved))))

def exec_chk(chk, arg):
    try:
        result = chk(arg)
        if result is not None and result is not True:
            raise ValueError('{} returned.'.format(result))
    except AssertionError:
        raise
    except Exception as e:
        six.raise_from(
            AssertionError('{!r}({!r}) failed: {}'.format(chk, arg, e)), e)
        raise # Shut up pylint
    return result

def chk_seq(vals, chks):
    assert len(chks) == len(vals)
    for chk, val in zip(chks, vals):
        exec_chk(chk, val)

def chk_all(vals, chk):
    for val in vals:
        exec_chk(chk, val)

def test_public_sdk_sample(native_sdk):
    nativeagent._force_initialize(native_sdk) #pylint:disable=protected-access
    from . import onesdksamplepy
    onesdksamplepy.main()
    assert_resolve_all(native_sdk)

    def check_remote_node(node):
        assert node.vals[:3] == (
            'dummyPyMethod', 'DummyPyService',
            'dupypr://localhost/dummyEndpoint')
        assert node.protocol_name == 'DUMMY_PY_PROTOCOL'

    def check_root(root):
        assert type(root) is sdkmockiface.InRemoteCallHandle
        assert root.vals == ('main', 'main', 'main')

        def check_remote_child(child):
            link, node = child
            assert link == sdkmockiface.TracerHandle.LINK_CHILD
            assert type(node) is sdkmockiface.OutRemoteCallHandle
            check_remote_node(node)
            assert node.vals[3:] == (
                onesdk.ChannelType.IN_PROCESS, 'localhost')

        def check_remote_child_err(child):
            check_remote_child(child)
            node = child[1]
            assert node.err_info == (
                RTERR_QNAME, 'Remote call failed on the server side.')

            def check_linked_remote_thread_err(rmchild):
                rmlink, rmnode = rmchild
                assert rmlink == sdkmockiface.TracerHandle.LINK_TAG
                assert type(rmnode) is sdkmockiface.InRemoteCallHandle
                check_remote_node(rmnode)
                assert not rmnode.children

            chk_seq(node.children, [check_linked_remote_thread_err])

        def check_remote_child_ok(child):
            check_remote_child(child)
            node = child[1]
            assert node.err_info is None

            def check_linked_remote_thread(rmchild):
                rmlink, rmnode = rmchild
                assert rmlink == sdkmockiface.TracerHandle.LINK_TAG
                assert type(rmnode) is sdkmockiface.InRemoteCallHandle
                check_remote_node(rmnode)
                assert rmnode.children

                def chk_dbcall(dbchild):
                    dblnk, dbnode = dbchild
                    assert dblnk == sdkmockiface.TracerHandle.LINK_CHILD
                    assert type(dbnode) is sdkmockiface.DbRequestHandle

                chk_all(rmnode.children, chk_dbcall)

            chk_seq(node.children, [check_linked_remote_thread])

        chk_seq(
            root.children,
            [check_remote_child_ok] * 2 + [check_remote_child_err])

    def check_is_linked(root):
        assert root.linked_parent

    def check_is_inprocess_link(root):
        assert type(root) is sdkmockiface.InProcessLinkTracerHandle

    def check_incoming_web_request(root):
        assert type(root) is sdkmockiface.InWebReqHandle
        assert len(root.custom_attribs) == 3
        key, value = root.custom_attribs[0]
        assert key == 'custom int attribute'
        assert value == 42
        key, value = root.custom_attribs[1]
        assert key == 'custom float attribute'
        assert value == 1.778
        key, value = root.custom_attribs[2]
        assert key == 'custom string attribute'
        assert value == 'snow is falling'

    def check_outgoing_weg_request(root):
        assert type(root) is sdkmockiface.OutWebReqHandle
        assert root.resp_code == 200
        assert len(root.req_hdrs) == 1
        header, value = root.req_hdrs[0]
        assert header == 'X-not-a-useful-header'
        assert value == 'python-was-here'
        assert len(root.resp_hdrs) == 1
        header, value = root.resp_hdrs[0]
        assert header == 'Content-Length'
        assert value == '1234'

    chk_seq(
        native_sdk.finished_paths,
        ([check_incoming_web_request] + [check_outgoing_weg_request] + [check_is_linked] * 3
         + [check_root] + [check_is_linked] + [check_is_inprocess_link]))

@pytest.mark.dependsnative
def test_sdk_callback_smoke():
    print(run_in_new_interpreter(sdk_diag_prog))
