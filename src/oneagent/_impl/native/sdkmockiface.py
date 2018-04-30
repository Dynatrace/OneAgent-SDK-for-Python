# -*- coding: utf-8 -*-
'''SDK interface with mock implementation, for testing etc. Uses strict error
handling, i.e. does not support broken paths.'''

from __future__ import print_function

import sys
import warnings
from functools import wraps
import threading
import base64
import struct
from itertools import chain


from oneagent._impl.six.moves import _thread, range #pylint:disable=import-error

from oneagent._impl import six
from oneagent.common import AgentState, ErrorCode, MessageSeverity

from .sdknulliface import SDKNullInterface

class SDKLeakWarning(RuntimeWarning):
    '''Warning that is emitted when a SDK resource was not properly disposed
    of.'''

class _Handle(object):
    def __str__(self):
        return '{}@0x{:X}'.format(type(self).__name__, id(self))

    def __repr__(self):
        return '{}{!r}@0x{:X}'.format(type(self).__name__, self.vals, id(self))

    def __init__(self, *vals):
        self.vals = vals
        self.is_live = True

    def close(self):
        self.is_live = False

    def __del__(self):
        if self.is_live:
            warnings.warn('Leaked handle {}'.format(self), SDKLeakWarning)



class DbInfoHandle(_Handle):
    pass

class WsAppHandle(_Handle):
    pass

class ThreadBoundObject(object):
    def __init__(self):
        self.tid = _thread.get_ident()

    def check_thread(self):
        if self.tid != _thread.get_ident():
            raise ValueError(
                '{} was created on T{}, but T{} attempted an access'.format(
                    self, self.tid, _thread.get_ident()))

class TracerHandle(_Handle, ThreadBoundObject):
    CREATED = 0
    STARTED = 1
    ENDED = 2

    LINK_CHILD = 0
    LINK_TAG = 1

    _TAG_STRUCT = struct.Struct('>Q') # Big/network-endian unsigned long long

    is_in_taggable = False
    has_out_tag = False
    is_entrypoint = False

    def __init__(self, _nsdk, *vals):
        assert isinstance(_nsdk, SDKMockInterface)
        _Handle.__init__(self, *vals)
        ThreadBoundObject.__init__(self)
        self.path = None
        self.state = self.CREATED
        self.err_info = None
        self.children = [] #[(link_kind: int, child: TracerHandle)]
        self.linked_parent = None
        self.in_tag = None
        self.is_in_tag_resolved = False

    def close(self):
        self.check_thread()
        self.state = self.ENDED
        if any(lnk == self.LINK_CHILD and c.state == self.STARTED
               for lnk, c in self.children):
            raise ValueError(
                'Ending tracer {} that has un-ended children: {}'.format(
                    self, self.children))
        _Handle.close(self)

    def all_original_children(self):
        '''Yields all (direct and indirect) children with LINK_CHILD.'''
        return chain.from_iterable(
            c.all_nodes_in_subtree()
            for lnk, c in self.children
            if lnk == self.LINK_CHILD)

    def all_nodes_in_subtree(self):
        '''Yields self and all (incl indirect) children with LINK_CHILD.'''
        return chain((self,), self.all_original_children())

    @property
    def out_tag(self):
        if not self.has_out_tag:
            raise ValueError(
                '{} tracer is not OutgoingTaggable'.format(type(self)))
        if self.state != self.STARTED:
            raise ValueError('Can only obtain tag when started!')
        return self._TAG_STRUCT.pack(id(self))

    def set_in_tag(self, tag):
        if not self.is_in_taggable:
            raise ValueError(
                '{} tracer is not IncomingTaggable'.format(type(self)))
        if self.state != self.CREATED:
            raise ValueError('Cannot set tags after starting.')

        self.in_tag = tag

    @property
    def in_tag_as_id(self):
        if self.in_tag is None:
            return None
        (result,) = self._TAG_STRUCT.unpack(self.in_tag)
        return result

    def dump(self, indent=''):
        result = '{}{}(S={}'.format(indent, str(self), self.state)
        intag = self.in_tag_as_id
        if intag is not None:
            result += ',I={}0x{:x}'.format(
                '' if self.is_in_tag_resolved else '!', intag)
        result += ')'
        valstr = ', '.join(map(repr, self.vals))
        if valstr:
            result += '\n{} V=({})'.format(indent, valstr)
        for lnk, child in self.children:
            result += '\n{} {}\n{}'.format(
                indent, lnk, child.dump(indent + '  '))
        return result


class RemoteCallHandleBase(TracerHandle):
    def __init__(self, *args, **kwargs):
        TracerHandle.__init__(self, *args, **kwargs)
        self.protocol_name = None
class InRemoteCallHandle(RemoteCallHandleBase):
    is_entrypoint = True
    is_in_taggable = True
class OutRemoteCallHandle(RemoteCallHandleBase):
    has_out_tag = True

class DbRequestHandle(TracerHandle):
    def __init__(self, *args, **kwargs):
        TracerHandle.__init__(self, *args, **kwargs)
        self.returned_row_count = None
        self.round_trip_count = None

class InWebReqHandle(TracerHandle):
    is_entrypoint = True
    is_in_taggable = True

    def __init__(self, *args, **kwargs):
        TracerHandle.__init__(self, *args, **kwargs)
        self.req_hdrs = []
        self.resp_hdrs = []
        self.params = []
        self.resp_code = None
        self.remote_addr = None

class Path(ThreadBoundObject):
    def __init__(self):
        ThreadBoundObject.__init__(self)
        self.nodestack = []

    def start(self, tracer):
        assert tracer.tid == self.tid
        if tracer.state != TracerHandle.CREATED:
            raise ValueError(
                'Tracer state {} is != CREATED'.format(tracer.state))
        if self.nodestack:
            self.nodestack[-1].children.append(
                (TracerHandle.LINK_CHILD, tracer))
        self.nodestack.append(tracer)
        tracer.state = TracerHandle.STARTED

    def end(self, tracer):
        tracer.close()
        if self.nodestack[-1] is not tracer:
            raise ValueError('Attempt to end {} while {} was active'.format(
                tracer, self.nodestack[-1]))
        else:
            self.nodestack.pop()

def _typecheck(val, expected_ty):
    if not isinstance(val, expected_ty):
        raise TypeError('Expected type {} but got {}({})'.format(
            expected_ty, type(val), val))
    if isinstance(val, ThreadBoundObject):
        val.check_thread()

def _livecheck(val, expected_ty, state=None):
    _typecheck(val, expected_ty)
    if not val.is_live:
        raise ValueError('Handle already closed: {}'.format(val))
    if state is not None and val.state != state:
        raise ValueError('Handle {} has state {}, but needs {}.'.format(
            val, val.state, state))

def _checkstate(state, maxstate=None, failure_r=ErrorCode.GENERIC):
    def checkstate_impl(func):
        @wraps(func)
        def state_checked(self, *args, **kwargs):
            #pylint:disable=protected-access
            if maxstate is not None:
                if not state <= self._state <= maxstate:
                    return failure_r
            elif state != self._state:
                return failure_r
            return func(self, *args, **kwargs)

        state_checked.__wrapped__ = func
        return state_checked

    return checkstate_impl

def _entry_field(func):

    @wraps(func)
    def checked(self, tracer_h, *args, **kwargs):
        if tracer_h.state != TracerHandle.CREATED:
            raise ValueError(
                'Attempt to set entry field too late: ' + func.__name__)
        return func(self, tracer_h, *args, **kwargs)

    checked.__wrapped__ = func
    return checked


def _strcheck(val, optional=False):
    if optional and val is None:
        return
    if not isinstance(val, six.string_types):
        raise TypeError('Expected a string type but got {}({})'.format(
            type(val), val))
    if not optional and not val.strip():
        raise ValueError('Expected non-empty string, but got {!r}'.format(val))

def _mk_add_kvs_fn(adder):

    def add_kvs(self, tracer_h, keys, vals, count):
        _livecheck(tracer_h, InWebReqHandle)
        _typecheck(count, int)
        for _, key, val in zip(range(count), keys, vals):
            adder(self, tracer_h, key, val)
    return add_kvs

class SDKMockInterface(object): #pylint:disable=too-many-public-methods
    def __init__(self):
        self._diag_cb = self.stub_default_logging_function
        self._log_cb = self.stub_default_logging_function
        self._state = AgentState.NOT_INITIALIZED
        self._log_level = MessageSeverity.FINEST
        self._path_tls = threading.local()
        self.finished_paths = []
        self.finished_paths_lk = threading.RLock()

    def all_finished_nodes(self):
        with self.finished_paths_lk:
            for node in self.finished_paths:
                for subnode in node.all_nodes_in_subtree():
                    yield subnode


    def get_finished_node_by_id(self, id_tag):
        with self.finished_paths_lk:
            for node in self.all_finished_nodes():
                if id(node) == id_tag:
                    return node
        return None


    def process_finished_paths_tags(self):
        unresolved = []
        with self.finished_paths_lk:
            for node in self.all_finished_nodes():
                in_id = node.in_tag_as_id
                if in_id is None:
                    continue
                linked = self.get_finished_node_by_id(in_id)
                if not linked:
                    unresolved.append(node)
                    continue
                linked.children.append((TracerHandle.LINK_TAG, node))
                node.is_in_tag_resolved = True
                node.linked_parent = linked
        return unresolved

    def get_path(self, create=False):
        path = getattr(self._path_tls, 'path', None)
        if not path and create:
            path = Path()
            self.set_path(path)
        return path

    def set_path(self, path):
        self._path_tls.path = path

    #pylint:disable=no-self-use,unused-argument

    def stub_is_sdk_cmdline_arg(self, arg):
        return arg.startswith('--dt_')

    def stub_process_cmdline_arg(self, arg, replace):
        _strcheck(arg)
        _typecheck(replace, bool)
        if self._state != AgentState.NOT_INITIALIZED:
            return ErrorCode.GENERIC
        return ErrorCode.SUCCESS

    def stub_set_variable(self, assignment, replace):
        _strcheck(assignment)
        _typecheck(replace, bool)
        if self._state != AgentState.NOT_INITIALIZED:
            return ErrorCode.GENERIC
        return ErrorCode.SUCCESS

    def stub_set_logging_level(self, level):
        _typecheck(level, int)
        if level < MessageSeverity.FINEST or level > MessageSeverity.DEBUG:
            warnings.warn('Bad message severity level.', RuntimeWarning)

    def stub_default_logging_function(self, level, msg):
        print('[OneSDK:Mock]', level, msg, file=sys.stderr)

    stub_set_logging_callback = SDKNullInterface.stub_set_logging_callback

    @_checkstate(AgentState.NOT_INITIALIZED)
    def stub_free_variables(self):
        pass

    def agent_get_version_string(self):
        return u'0.000.0.00000000-{}'.format(type(self).__name__)

    @_checkstate(AgentState.NOT_INITIALIZED)
    def initialize(self):
        self._state = AgentState.ACTIVE
        return ErrorCode.SUCCESS

    @_checkstate(AgentState.ACTIVE, AgentState.TEMPORARILY_INACTIVE)
    def shutdown(self):
        self._state = AgentState.NOT_INITIALIZED
        return ErrorCode.SUCCESS

    def agent_get_current_state(self):
        return self._state

    agent_set_logging_callback = SDKNullInterface.agent_set_logging_callback
    agent_get_logging_callback = SDKNullInterface.agent_get_logging_callback

    def strerror(self, error_code):
        if error_code == ErrorCode.SUCCESS:
            return u'Success.'
        elif error_code == ErrorCode.GENERIC:
            return u'Generic error.'
        return u'Unknown error #' + str(error_code)

    def webapplicationinfo_create(self, vhost, appid, ctxroot):
        _strcheck(vhost)
        _strcheck(appid)
        _strcheck(ctxroot)
        return WsAppHandle(vhost, appid, ctxroot)

    def webapplicationinfo_delete(self, wapp_h):
        _typecheck(wapp_h, WsAppHandle)
        wapp_h.close()

    def incomingwebrequesttracer_create(self, wapp_h, uri, http_method):
        _livecheck(wapp_h, WsAppHandle)
        _strcheck(uri)
        _strcheck(http_method)
        return InWebReqHandle(self, wapp_h, uri, http_method)

    #pylint:disable=invalid-name


    @_entry_field
    def incomingwebrequesttracer_add_request_header(self, tracer_h, key, val):
        _livecheck(tracer_h, InWebReqHandle)
        _strcheck(key)
        _strcheck(val)
        tracer_h.req_hdrs.append((key, val))

    incomingwebrequesttracer_add_request_headers = _mk_add_kvs_fn(
        incomingwebrequesttracer_add_request_header)

    def incomingwebrequesttracer_add_response_header(self, tracer_h, key, val):
        _livecheck(tracer_h, InWebReqHandle)
        _strcheck(key)
        _strcheck(val)
        tracer_h.resp_hdrs.append((key, val))

    incomingwebrequesttracer_add_response_headers = _mk_add_kvs_fn(
        incomingwebrequesttracer_add_response_header)

    def incomingwebrequesttracer_add_parameter(self, tracer_h, key, val):
        _livecheck(tracer_h, InWebReqHandle)
        _strcheck(key)
        _strcheck(val)
        tracer_h.params.append((key, val))

    incomingwebrequesttracer_add_parameters = _mk_add_kvs_fn(
        incomingwebrequesttracer_add_parameter)

    @_entry_field
    def incomingwebrequesttracer_set_remote_address(self, tracer_h, addr):
        _livecheck(tracer_h, InWebReqHandle)
        _strcheck(addr, optional=True)
        tracer_h.remote_addr = addr

    def incomingwebrequesttracer_set_status_code(self, tracer_h, code):
        _livecheck(tracer_h, InWebReqHandle)
        _typecheck(code, int)
        tracer_h.resp_code = code

    #pylint:enable=invalid-name

    def databaseinfo_create(self, dbname, dbvendor, chan_ty, chan_ep):
        _strcheck(dbname)
        _strcheck(dbvendor)
        _typecheck(chan_ty, int)
        _strcheck(chan_ep, optional=True)
        return DbInfoHandle(dbname, dbvendor, chan_ty, chan_ep)

    def databaseinfo_delete(self, dbh):
        _typecheck(dbh, DbInfoHandle)
        dbh.close()

    #pylint:disable=invalid-name

    def databaserequesttracer_create_sql(
            self, dbh, sql):
        _livecheck(dbh, DbInfoHandle)
        _strcheck(sql)
        return DbRequestHandle(self, dbh, sql)

    def databaserequesttracer_set_returned_row_count(self, tracer_h, count):
        _livecheck(tracer_h, DbRequestHandle)
        _typecheck(count, int)
        assert count >= 0, 'Invalid count'
        tracer_h.returned_row_count = count


    def databaserequesttracer_set_round_trip_count(self, tracer_h, count):
        _livecheck(tracer_h, DbRequestHandle)
        _typecheck(count, int)
        assert count >= 0, 'Invalid count'
        tracer_h.round_trip_count = count

    #pylint:enable=invalid-name

    def outgoingremotecalltracer_create( #pylint:disable=too-many-arguments
            self, svc_method, svc_name, svc_endpoint, chan_ty, chan_ep):
        _strcheck(svc_method)
        _strcheck(svc_name)
        _strcheck(svc_endpoint)
        _typecheck(chan_ty, int)
        _strcheck(chan_ep, optional=True)
        return OutRemoteCallHandle(
            self, svc_method, svc_name, svc_endpoint, chan_ty, chan_ep)

    @_entry_field
    def outgoingremotecalltracer_set_protocol_name( #pylint:disable=invalid-name
            self, tracer_h, protocol_name):
        _livecheck(tracer_h, OutRemoteCallHandle, TracerHandle.CREATED)
        _strcheck(protocol_name, optional=True)
        tracer_h.protocol_name = protocol_name

    def incomingremotecalltracer_create(
            self, svc_method, svc_name, svc_endpoint):
        _strcheck(svc_method)
        _strcheck(svc_name)
        _strcheck(svc_endpoint)
        return InRemoteCallHandle(self, svc_method, svc_name, svc_endpoint)

    @_entry_field
    def incomingremotecalltracer_set_protocol_name( #pylint:disable=invalid-name
            self, tracer_h, protocol_name):
        _livecheck(tracer_h, InRemoteCallHandle, TracerHandle.CREATED)
        _strcheck(protocol_name, optional=True)
        tracer_h.protocol_name = protocol_name

    def tracer_start(self, tracer_h):
        _livecheck(tracer_h, TracerHandle, TracerHandle.CREATED)
        path = self.get_path(create=tracer_h.is_entrypoint)
        if path:
            path.start(tracer_h)


    def tracer_end(self, tracer_h):
        _typecheck(tracer_h, TracerHandle)
        path = self.get_path()
        if not path:
            assert tracer_h.state in (TracerHandle.ENDED, TracerHandle.CREATED)
            tracer_h.close()
            return
        path.end(tracer_h)
        if not path.nodestack:
            with self.finished_paths_lk:
                self.finished_paths.append(tracer_h) # tracer_h is the root node

    def tracer_error(self, tracer_h, error_class, error_message):
        _livecheck(tracer_h, TracerHandle, TracerHandle.STARTED)
        _strcheck(error_class, optional=True)
        _strcheck(error_message, optional=True)
        tracer_h.err_info = (error_class, error_message)

    def tracer_get_outgoing_tag(self, tracer_h, use_byte_tag=False):
        _livecheck(tracer_h, TracerHandle, TracerHandle.STARTED)
        if use_byte_tag:
            return tracer_h.out_tag
        return base64.b64encode(tracer_h.out_tag).decode('ASCII')

    @_entry_field
    def tracer_set_incoming_string_tag(self, tracer_h, tag):
        _livecheck(tracer_h, TracerHandle, TracerHandle.CREATED)
        if tag is None:
            tracer_h.set_in_tag(None)
        _strcheck(tag, optional=True)
        tracer_h.set_in_tag(base64.b64decode(tag))

    @_entry_field
    def tracer_set_incoming_byte_tag(self, tracer_h, tag):
        _livecheck(tracer_h, TracerHandle, TracerHandle.CREATED)
        _typecheck(tag, (six.binary_type, type(None)))
        tracer_h.set_in_tag(tag)
