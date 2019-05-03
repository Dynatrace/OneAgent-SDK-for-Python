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

'''Defines the public SDK tracer types (constructors should be considered
private though).

Use the factory functions from :class:`oneagent.sdk.SDK` to create tracers.'''

from oneagent._impl.util import error_from_exc as _error_from_exc
from oneagent._impl import six

class OutgoingTaggable(object):
    '''Mixin base class for tracers that support having other paths linked to
    them.

    .. seealso:: Documentation on :ref:`tagging`.
    '''

    # Abstract, for pylint
    handle = None
    nsdk = None

    @property
    def outgoing_dynatrace_string_tag(self):
        '''Get a string tag (:class:`str` on Python 3, :class:`unicode` on
        Python 2) identifying the node of this tracer. Must be called between
        starting and ending the tracer (i.e., while it is started).'''
        return self.nsdk.tracer_get_outgoing_tag(self.handle, False)

    @property
    def outgoing_dynatrace_byte_tag(self):
        '''Get a :class:`bytes` tag identifying the node of this tracer. Must be
        called between starting and ending the tracer (i.e., while it is
        started).'''
        return self.nsdk.tracer_get_outgoing_tag(self.handle, True)

class Tracer(object):
    '''Base class for tracing of operations.

    Note that tracer are not only not thread-safe but thread-affine: They may
    only ever be used on the thread that created them.

    If a tracer object evaluates to :data:`False` (i.e., is falsy), tracing has
    been rejected for some reason (e.g., because the agent is currently or
    permanently inactive). You may then skip adding more information to the
    tracer, which might speed up your application.

    .. _tracer-states:

    The usual life-cycle of a tracer is as follows:

        1. Create a tracer using the appropriate
           :code:`oneagent.sdk.SDK.trace_*` method. The tracer is now in the
           :dfn:`unstarted` state.
        2. Start the tracer (via :meth:`.start` or by using the tracer as a
           context manager, i.e., in a :code:`with`-block). Timing starts here.
           The tracer is now :dfn:`started`.
        3. Optionally mark the tracer as failed once (using
           :meth:`mark_failed_exc`, :meth:`.mark_failed` or automatically when
           an exception leaves the with-block for which this tracer was used as
           a context manager). It is still started but also marked as
           :dfn:`failed`.
        4. End the tracer (via :meth:`.end` or automatically by using the tracer
           as a context manager). Timing stops here. The tracer is now
           :dfn:`ended` and no further operations are allowed on it.

    Unless specified otherwise, all operations on tracer are only allowed in the
    started state.

    You may short-circuit the life-cycle by calling :meth:`.end` already in the
    unstarted state (i.e., before starting the tracer). No nodes or path will be
    produced then. However, it is usually better to avoid creating the tracer in
    the first place instead of throwing it away unused that way.

    Tracers can be used as context-managers, i.e., in :code:`with` blocks::

        with tracer:
            # code

    This will start the tracer upon entering the :code:`with`-block and end it
    upon leaving it. Additionally, if an exception leaves the block,
    :meth:`.mark_failed_exc` will be called on the tracer.
    '''

    def __init__(self, nsdk, handle):
        self.nsdk = nsdk
        self.handle = handle

    def start(self):
        '''Start the tracer and timing.

        May only be called in the unstarted state. Transitions the state from
        unstarted to started.

        Prefer using the tracer as a context manager (i.e., with a
        :code:`with`-block) instead of manually calling this method.
        '''
        self.nsdk.tracer_start(self.handle)

    def end(self):
        '''Ends the tracer.

        May be called in any state. Transitions the state to ended and releases
        any SDK resources owned by this tracer (this includes only internal
        resources, things like passed-in
        :class:`oneagent.common.DbInfoHandle` need to be released manually).

        Prefer using the tracer as a context manager (i.e., with a
        :code:`with`-block) instead of manually calling this method.
        '''
        if self.handle is not None:
            self.nsdk.tracer_end(self.handle)
            self.handle = None

    def mark_failed(self, clsname, msg):
        '''Marks the tracer as failed with the given exception class name
        :code:`clsname` and message :code:`msg`.

        May only be called in the started state and only if the tracer is not
        already marked as failed. Note that this does not end the tracer! Once a
        tracer is marked as failed, attempts to do it again are forbidden.

        If possible, using the tracer as a context manager (i.e., with a
        :code:`with`-block) or :meth:`.mark_failed_exc` is more convenient than
        this method.

        :param str clsname: Fully qualified name of the exception type that
            caused the failure.
        :param str msg: Exception message that caused the failure.
        '''
        self.nsdk.tracer_error(self.handle, clsname, msg)

    def mark_failed_exc(self, e_val=None, e_ty=None):
        '''Marks the tracer as failed with the given exception :code:`e_val` of
        type :code:`e_ty` (defaults to the current exception).

        May only be called in the started state and only if the tracer is not
        already marked as failed. Note that this does not end the tracer! Once a
        tracer is marked as failed, attempts to do it again are forbidden.

        If possible, using the tracer as a context manager (i.e., with a
        :code:`with`-block) is more convenient than this method.

        If :code:`e_val` and :code:`e_ty` are both none, the current exception
        (as retured by :func:`sys.exc_info`) is used.

        :param BaseException e_val: The exception object that caused the
            failure. If :code:`None`, the current exception value
            (:code:`sys.exc_info()[1]`) is used.
        :param type e_ty: The type of the exception that caused the failure. If
            :code:`None` the type of :code:`e_val` is used. If that is also
            :code:`None`, the current exception type (:code:`sys.exc_info()[0]`)
            is used.
        '''
        _error_from_exc(self.nsdk, self.handle, e_val, e_ty)

    def __enter__(self):
        '''Starts the tracer (as if calling :meth:`.start`) and returns
        :code:`self`. For use with :code:`with` blocks.'''
        self.start()
        return self

    def __exit__(self, e_ty, e_val, e_tb):
        '''If any exception leaves the :code:`with`-block, marks the tracer as
        failed with that exception (see :meth:`mark_failed_exc`). In any case,
        ends the tracer (see :meth:`end`).'''
        try:
            del e_tb
            if e_ty is not None or e_val is not None:
                self.mark_failed_exc(e_val, e_ty)
        finally:
            self.end()

    def __del__(self):
        if self.handle is not None:
            # Intentionally don't end the tracer: Prefer resource leaks over
            # incorrect paths (we might be on another thread anyway).
            warn = self.nsdk.agent_get_logging_callback()
            if warn:
                warn('Un-ended SDK Tracer {}({})'.format(
                    type(self), self.handle))

    def __bool__(self):
        return bool(self.handle)

    __nonzero__ = __bool__

class DatabaseRequestTracer(Tracer):
    '''Traces a database request. See
        :meth:`oneagent.sdk.SDK.trace_sql_database_request`.'''

    def set_rows_returned(self, rows_returned):
        '''Sets the number of retrieved rows for this traced database request.

        :param int rows_returned: The number of rows returned Must not be
            negative.
        '''
        self.nsdk.databaserequesttracer_set_returned_row_count(
            self.handle, rows_returned)

    def set_round_trip_count(self, round_trip_count):
        '''Sets the number of round trips to the database server for this traced
        database request.

        :param int round_trip_count: The number of round trips. Must not be
            negative.
        '''
        self.nsdk.databaserequesttracer_set_round_trip_count(
            self.handle, round_trip_count)


class IncomingRemoteCallTracer(Tracer):
    '''Traces an incoming remote call. See
    :meth:`oneagent.sdk.SDK.trace_incoming_remote_call`.'''
    pass

class OutgoingRemoteCallTracer(Tracer, OutgoingTaggable):
    '''Traces an outgoing remote call. See
    :meth:`oneagent.sdk.SDK.trace_outgoing_remote_call`.'''
    pass

def _make_add_kvs_fn(fnname):
    add_kv_name = fnname
    add_kvs_name = add_kv_name + 's'

    def add_kvs_fn(self, names_or_dict, values=None, count=None):
        add_kvs_impl = getattr(self.nsdk, add_kvs_name)
        if values is None:
            add_kvs_impl(
                self.handle,
                six.iterkeys(names_or_dict),
                six.itervalues(names_or_dict),
                len(names_or_dict))
        else:
            add_kvs_impl(
                self.handle,
                names_or_dict,
                values,
                len(names_or_dict) if count is None else count)

    def add_kv_fn(self, name, value):
        add_kv_impl = getattr(self.nsdk, add_kv_name)
        add_kv_impl(self.handle, name, value)

    return add_kvs_fn, add_kv_fn

class IncomingWebRequestTracer(Tracer):
    '''Traces an incoming web (HTTP) request. See
    :meth:`oneagent.sdk.SDK.trace_incoming_web_request`.

    .. warning:: Regarding HTTP header encoding issues see :ref:`http-encoding-warning`.

    .. method:: add_parameter(name, value)
                add_parameters(data)
                add_parameters(names, values [, count])

        Adds the request (POST/form) parameter(s) with the given name(s) and
        value(s).

        :meth:`.add_parameter` adds a single parameter:

        :param str name: The name of the parameter.
        :param str value: The value of the parameter.

        :meth:`.add_parameters` adds multiple parameters and can be called
        either with a single mapping of parameter names to parameter values or
        with the names, corresponding values, and an optional count as separate
        iterables:

        :param data: A dictionary mapping a parameter name to a
            (single) parameter value.
        :type data: dict[str, str]
        :param names: An iterable (if the count is given) or collection (if not)
            of strings with the parameter names.
        :type names: ~typing.Iterable[str] or ~typing.Collection[str]
        :param values: An iterable (if the count is given) or collection (if
            not) of strings with the parameter values.
        :type values: ~typing.Iterable[str] or ~typing.Collection[str]
        :param int count: An optional integer giving the count of values in
            :code:`names` / :code:`values` to use.

    .. method:: add_response_header(name, value)
                add_response_headers(data)
                add_response_headers(names, values [, count])

        Adds the HTTP response header(s) with the given name(s) and value(s).
        For the parameters, see :meth:`.add_parameter` and
        :meth:`.add_parameters`.

        Some headers can appear multiple times in an HTTP response. To capture
        all the values, either call :meth:`.add_response_header` multiple times,
        or use the signature with names and values as separate values and
        provide the name and corresponding values for each, or, if possible for
        that particular header, set the value to an appropriately concatenated
        string.
    '''

    add_parameters, add_parameter = _make_add_kvs_fn('incomingwebrequesttracer_add_parameter')

    add_response_headers, add_response_header = _make_add_kvs_fn(
        'incomingwebrequesttracer_add_response_header')

    def set_status_code(self, code):
        '''Sets the HTTP status code for the response to the traced incoming
        request.

        :param int code: The HTTP status code of the HTTP response that is sent
            back to the client (e.g., 200 or 404).
        '''
        self.nsdk.incomingwebrequesttracer_set_status_code(self.handle, code)

class OutgoingWebRequestTracer(Tracer, OutgoingTaggable):
    '''Traces an outgoing web (HTTP) request. See
    :meth:`oneagent.sdk.SDK.trace_outgoing_web_request`.

    .. warning:: Regarding HTTP header encoding issues see :ref:`http-encoding-warning`.

    .. method:: add_response_header(name, value)
                add_response_headers(data)
                add_response_headers(names, values [, count])

        Adds the HTTP response header(s) with the given name(s) and value(s).
        For the parameters, see :meth:`.add_parameter` and
        :meth:`.add_parameters`.

        Some headers can appear multiple times in an HTTP response. To capture
        all the values, either call :meth:`.add_response_header` multiple times,
        or use the signature with names and values as separate values and
        provide the name and corresponding values for each, or, if possible for
        that particular header, set the value to an appropriately concatenated
        string.

        .. versionadded:: 1.1.0
    '''

    add_response_headers, add_response_header = \
        _make_add_kvs_fn('outgoingwebrequesttracer_add_response_header')

    def set_status_code(self, code):
        '''Sets the HTTP status code for the response of the traced outgoing
        request.

        :param int code: The HTTP status code of the HTTP response (e.g., 200 or 404).

        .. versionadded:: 1.1.0
        '''
        self.nsdk.outgoingwebrequesttracer_set_status_code(self.handle, code)

class InProcessLinkTracer(Tracer):
    '''Traces in-process asynchronous execution.

        See :meth:`oneagent.sdk.SDK.create_in_process_link` and
        :meth:`oneagent.sdk.SDK.trace_in_process_link` for more information.

    .. versionadded:: 1.1.0
    '''
    pass

class OutgoingMessageTracer(Tracer, OutgoingTaggable):
    '''Tracer for outgoing messages.

        See :meth:`oneagent.sdk.SDK.trace_outgoing_message` for more information.

        .. versionadded:: 1.2.0
    '''

    def set_vendor_message_id(self, message_id):
        '''Sets the vendor message ID of an outgoing message.

        :param str message_id: The vendor message ID provided by the messaging system.

        .. note:: This information is often only available after the message was sent. Thus,
            calling this function is also supported after starting the tracer.

        .. versionadded:: 1.2.0
        '''
        self.nsdk.outgoingmessagetracer_set_vendor_message_id(self.handle, message_id)

    def set_correlation_id(self, correlation_id):
        '''Sets the corrrelation ID of an outgoing message.

        :param str correlation_id: The correlation ID for the message, usually application-defined.

        .. note:: This information is often only available after the message was sent. Thus,
            calling this function is also supported after starting the tracer.

        .. versionadded:: 1.2.0
        '''
        self.nsdk.outgoingmessagetracer_set_correlation_id(self.handle, correlation_id)

class IncomingMessageReceiveTracer(Tracer):
    '''Tracer for receiving messages.

        See :meth:`oneagent.sdk.SDK.trace_incoming_message_receive` for more information.

        .. versionadded:: 1.2.0
    '''
    pass

class IncomingMessageProcessTracer(Tracer):
    '''Tracer for processing incoming messages.

        See :meth:`oneagent.sdk.SDK.trace_incoming_message_process` for more information.

        .. versionadded:: 1.2.0
    '''
    def set_vendor_message_id(self, message_id):
        '''Sets the vendor message ID of an incoming message.

        :param str message_id: The message ID provided by the messaging system.

        .. versionadded:: 1.2.0
        '''
        self.nsdk.incomingmessageprocesstracer_set_vendor_message_id(self.handle, message_id)

    def set_correlation_id(self, correlation_id):
        '''Sets the corrrelation ID of an incoming message.

        :param str correlation_id: The correlation ID for the message, usually application-defined.

        .. versionadded:: 1.2.0
        '''
        self.nsdk.incomingmessageprocesstracer_set_correlation_id(self.handle, correlation_id)

class CustomServiceTracer(Tracer):
    '''Tracer for custom services.

    See :meth:`oneagent.sdk.SDK.trace_custom_service` for more information.

        .. versionadded:: 1.2.0
    '''
    pass
