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

'''SDK tracer factory functions and misc functions.

.. class:: Channel

    A (transport-layer) communication channel.

    .. automethod:: __new__

    .. attribute:: type_

       A :class:`int` describing the type of the channel. One of the
       :class:`oneagent.common.ChannelType` constants.

    .. attribute:: endpoint

       An optional :class:`str` describing the endpoint of the channel. See the
       documentation for the channel type constants for what this should be for
       each channel type.
'''

from collections import namedtuple, Mapping

from oneagent._impl import six
from oneagent._impl.native.nativeagent import try_get_sdk as _try_get_nsdk
from oneagent import initialize as _init_nsdk, logger

from oneagent.common import * #pylint:disable=wildcard-import

from . import tracers


Channel = namedtuple('Channel', 'type_ endpoint')
Channel.__new__.__defaults__ = (None,) # endpoint is optional
# Note: Cannot set __doc__ of types and the tuple slots on Python 2.
Channel.__new__.__doc__ = '''Creates a new :class:`Channel`.

:param int type_: The type of the channel. See :attr:`type_`.
:param str endpoint: The channel endpoint. See :attr:`endpoint`.'''


def _get_kvc(kv_arg):
    '''Returns a tuple keys, values, count for kv_arg (which can be a dict or a
        tuple containing keys, values and optinally count.'''
    if isinstance(kv_arg, Mapping):
        return six.iterkeys(kv_arg), six.itervalues(kv_arg), len(kv_arg)
    assert 2 <= len(kv_arg) <= 3, \
        'Argument must be a mapping or a sequence (keys, values, [len])'
    return (
        kv_arg[0],
        kv_arg[1],
        kv_arg[2] if len(kv_arg) == 3 else len(kv_arg[0]))

class SDK(object):
    '''The main entry point to the Dynatrace SDK.'''

    def _applytag(self, tracer, str_tag, byte_tag):
        if str_tag is None and byte_tag is None:
            return
        if byte_tag is not None:
            if str_tag is not None:
                warn = self._nsdk.agent_get_logging_callback()
                if warn:
                    warn('Both str_tag and byte_tag specified. Use only one!')
                return # Discard tags, to not let this error go unnoticed
            self._nsdk.tracer_set_incoming_byte_tag(tracer.handle, byte_tag)
        else:
            self._nsdk.tracer_set_incoming_string_tag(tracer.handle, str_tag)

    def __init__(self, native_sdk):
        self._nsdk = native_sdk

    # Keyword-only arguments are only available in Python 3, so
    #pylint:disable=too-many-arguments

    def create_database_info(
            self,
            name,
            vendor,
            channel):
        '''Creates a database info with the given information for use with
        :meth:`trace_sql_database_request`.

        :param str name: The name (e.g., connection string) of the database.
        :param str vendor: The type of the database (e.g., sqlite, PostgreSQL,
            MySQL).
        :param Channel channel: The channel used to communicate with the
            database.
        :returns: A new handle, holding the given database information.
        :rtype: DbInfoHandle
        '''
        return DbInfoHandle(self._nsdk, self._nsdk.databaseinfo_create(
            name, vendor, channel.type_, channel.endpoint))

    def create_web_application_info(
            self, virtual_host, application_id, context_root):
        '''Creates a web application info for use with
        :meth:`trace_incoming_web_request`.

        See
        <https://www.dynatrace.com/support/help/server-side-services/introduction/how-does-dynatrace-detect-and-name-services/#web-request-services>
        for more information about the meaning of the parameters.

        :param str virtual_host: The logical name of the web server that hosts
            the application.
        :param str application_id: A unique ID for the web application. This
            will also be used as the display name.
        :param str context_root: The context root of the web application. This
            is the common path prefix for requests which will be routed to the
            web application.

            If all requests to this server are routed to this application, use
            a slash :code:`'/'`.
        :rtype: WebapplicationInfoHandle
        '''
        return WebapplicationInfoHandle(
            self._nsdk, self._nsdk.webapplicationinfo_create(
                virtual_host, application_id, context_root))


    def trace_sql_database_request(self, database, sql):
        '''Create a tracer for the given database info and SQL statement.

        :param DbInfoHandle database: Database information (see
            :meth:`create_database_info`).
        :param str sql: The SQL statement to trace.
        :rtype: tracers.DatabaseRequestTracer
        '''
        assert isinstance(database, DbInfoHandle)
        return tracers.DatabaseRequestTracer(
            self._nsdk,
            self._nsdk.databaserequesttracer_create_sql(database.handle, sql))

    def trace_incoming_web_request(
            self,
            webapp_info,
            url,
            method,
            headers=None,
            remote_address=None,
            str_tag=None,
            byte_tag=None):
        '''Create a tracer for an incoming webrequest.

        :param WebapplicationInfoHandle webapp_info: Web application
            information (see :meth:`create_web_application_info`).
        :param str url: The requested URL (including scheme, hostname/port,
            path and query).
        :param str method: The HTTP method of the request (e.g., GET or
            POST).
        :param headers: The HTTP headers of the request. Can be either a
            dictionary mapping header name to value (:class:`str` to
            :class:`str`) or a tuple containing a sequence of string header
            names as first element, an equally long sequence of
            corresponding values as second element and optionally a count as
            third element (this will default to the :func:`len` of the
            header names).

            Some headers can appear multiple times in an HTTP request. To
            capture all the values, either use the tuple-form and provide
            the name and corresponding values for each, or if possible for
            that particular header, set the value to an appropriately
            concatenated string.

            .. warning:: If you use Python 2, be sure to use the UTF-8 encoding
                or the :class:`unicode` type! See :ref:`here
                <http-encoding-warning>` for more information.
        :type headers: \
            dict[str, str] or \
            tuple[~typing.Collection[str], ~typing.Collection[str]] or \
            tuple[~typing.Iterable[str], ~typing.Iterable[str], int]]
        :param str remote_address: The remote (client) IP address (of the
            peer of the socket connection via which the request was
            received).

            The remote address is useful to gain information about load
            balancers, proxies and ultimately the end user that is sending
            the request.

        For the other parameters, see :ref:`tagging`.

        :rtype: tracers.IncomingWebRequestTracer
        '''
        assert isinstance(webapp_info, WebapplicationInfoHandle)
        result = tracers.IncomingWebRequestTracer(
            self._nsdk,
            self._nsdk.incomingwebrequesttracer_create(
                webapp_info.handle, url, method))
        if not result:
            return result
        try:
            if headers:
                self._nsdk.incomingwebrequesttracer_add_request_headers(
                    result.handle, *_get_kvc(headers))
            if remote_address:
                self._nsdk.incomingwebrequesttracer_set_remote_address(
                    result.handle, remote_address)
            self._applytag(result, str_tag, byte_tag)
        except:
            result.end()
            raise
        return result

    def trace_outgoing_web_request(self, url, method, headers=None):
        '''Create a tracer for an outgoing webrequest.

        :param str url: The request URL (including scheme, hostname/port, path and query).
        :param str method: The HTTP method of the request (e.g., GET or POST).
        :param headers: The HTTP headers of the request. Can be either a
            dictionary mapping header name to value (:class:`str` to
            :class:`str`) or a tuple containing a sequence of string header
            names as first element, an equally long sequence of
            corresponding values as second element and optionally a count as
            third element (this will default to the :func:`len` of the
            header names).

            Some headers can appear multiple times in an HTTP request. To
            capture all the values, either use the tuple-form and provide
            the name and corresponding values for each, or if possible for
            that particular header, set the value to an appropriately
            concatenated string.

            .. warning:: If you use Python 2, be sure to use the UTF-8 encoding
                or the :class:`unicode` type! See :ref:`here
                <http-encoding-warning>` for more information.
        :type headers: \
            dict[str, str] or \
            tuple[~typing.Collection[str], ~typing.Collection[str]] or \
            tuple[~typing.Iterable[str], ~typing.Iterable[str], int]]

        :rtype: tracers.OutgoingWebRequestTracer

        .. versionadded:: 1.1.0
        '''
        result = tracers.OutgoingWebRequestTracer(
            self._nsdk, self._nsdk.outgoingwebrequesttracer_create(url, method))

        if not result:
            return result

        try:
            if headers:
                self._nsdk.outgoingwebrequesttracer_add_request_headers(result.handle,
                                                                        *_get_kvc(headers))
        except:
            result.end()
            raise

        return result

    def trace_outgoing_remote_call(
            self,
            method,
            service,
            endpoint,
            channel,
            protocol_name=None):
        '''Creates a tracer for outgoing remote calls.

        :param str method: The name of the service method/operation.
        :param str service: The name of the service class/type.
        :param str endpoint: A string identifying the "instance" of the the
            service. See also `the general documentation on service
            endpoints`__.
        :param Channel channel: The channel used to communicate with the
            service.
        :param str protocol_name: The name of the remoting protocol (on top of
            the communication protocol specified in :code:`channel.type_`.) that
            is used to to communicate with the service (e.g., RMI, Protobuf,
            ...).

            __ \
                https://github.com/Dynatrace/OneAgent-SDK#common-concepts-service-endpoints-and-communication-endpoints

        :rtype: tracers.OutgoingRemoteCallTracer
        '''
        result = tracers.OutgoingRemoteCallTracer(
            self._nsdk,
            self._nsdk.outgoingremotecalltracer_create(
                method,
                service,
                endpoint,
                channel.type_,
                channel.endpoint))
        if protocol_name is not None:
            self._nsdk.outgoingremotecalltracer_set_protocol_name(
                result.handle, protocol_name)
        return result

    def trace_incoming_remote_call(
            self,
            method,
            name,
            endpoint,
            protocol_name=None,
            str_tag=None,
            byte_tag=None):
        '''Creates a tracer for incoming remote calls.

        For the parameters, see :ref:`tagging` (:code:`str_tag` and
        :code:`byte_tag`) and :meth:`trace_outgoing_remote_call` (all others).

        :rtype: tracers.IncomingRemoteCallTracer
        '''
        result = tracers.IncomingRemoteCallTracer(
            self._nsdk,
            self._nsdk.incomingremotecalltracer_create(method, name, endpoint))
        if protocol_name is not None:
            self._nsdk.incomingremotecalltracer_set_protocol_name(
                result.handle, protocol_name)
        self._applytag(result, str_tag, byte_tag)
        return result

    def create_in_process_link(self):
        '''Creates an in-process link.

        An application can call this function to retrieve an in-process link, which can then be
        used to trace related processing at a later time and/or in a different thread.

        In-process links allow an application to associate (link) tasks, that will be executed
        asynchronously in the same process, with the currently running task/operation. The linked
        tasks may be started and completed at arbitrary times - it's not necessary for them to
        complete (or even start) before the "parent" operation to which they are linked completes.

        For further information, see the high level SDK documentation at
        <https://github.com/Dynatrace/OneAgent-SDK/#in-process-linking>.

        .. note::
            * If no tracer is active on the current thread, the retrieved link will be empty
              (have zero length).
            * Links returned by this function are not compatible with dynatrace string or byte tags,
              they can only be used with :meth:`trace_in_process_link`.
            * Links returned by this function can only be used in the process in which they were
              created.

        :rtype: bytes

        .. versionadded:: 1.1.0
        '''
        return self._nsdk.create_in_process_link()

    def trace_in_process_link(self, link_bytes):
        '''Creates a tracer for tracing asynchronous related processing in the same process.

        For more information see :meth:`create_in_process_link`.

        :param bytes link_bytes: An in-process link created using :meth:`create_in_process_link`.

        :rtype: tracers.InProcessLinkTracer

        .. versionadded:: 1.1.0
        '''
        return tracers.InProcessLinkTracer(self._nsdk,
                                           self._nsdk.trace_in_process_link(link_bytes))

    def set_diagnostic_callback(self, callback):
        '''Sets a callback to be informed of unusual events.

        Unusual events include:

        - API usage errors.
        - Other unexpected events (like out of memory situations) that prevented
          an operation from completing successfully.

        .. warning:: Use this as a development and debugging aid only. Your application should not
            rely on a calling sequence or any message content being set or passed to the callback.

        :param callable callback: The callback function. Receives the (unicode)
            error message as its only argument.
        '''
        self._nsdk.agent_set_logging_callback(callback)

    @property
    def agent_state(self):
        '''Returns the current agent state (one of the constants in
        :class:`oneagent.common.AgentState`).

        :rtype: int'''
        return self._nsdk.agent_get_current_state()

    @property
    def agent_version_string(self):
        '''Returns the version string of the loaded SDK agent module.

        If the agent has not been initialized yet this function will return an
        empty string.

        .. warning:: Your application should not try to parse the version string
            or make any assumptions about it's format.

        :rtype: str'''
        return self._nsdk.agent_get_version_string()

    @property
    def agent_found(self):
        '''Returns whether an OneAgent could be found or not.

        :rtype: bool

        .. versionadded:: 1.1.0
        '''
        return self._nsdk.agent_found()

    @property
    def agent_is_compatible(self):
        '''Returns whether the found OneAgent is compatible with this version of the OneAgent
        SDK for Python.

        :rtype: bool

        .. versionadded:: 1.1.0
        '''
        return self._nsdk.agent_is_compatible()

    def add_custom_request_attribute(self, key, value):
        '''Adds a custom request attribute to the current active tracer.

            :param str key: The name of the custom request attribute, the name is mandatory and
                may not be None.
            :param value: The value of the custom request attribute. Currently supported types
                are integer, float and string values. The value is mandatory and may
                not be None.
            :type value: str or int or float

            .. versionadded:: 1.1.0
        '''

        if isinstance(value, int):
            self._nsdk.customrequestattribute_add_integer(key, value)
        elif isinstance(value, float):
            self._nsdk.customrequestattribute_add_float(key, value)
        elif isinstance(value, six.string_types):
            self._nsdk.customrequestattribute_add_string(key, value)
        else:
            warn = self._nsdk.agent_get_logging_callback()
            if warn:
                warn('Can\'t add custom request attribute \'{0}\' '
                     'because the value type \'{1}\' is not supported!'.format(key, type(value)))

    # messaging

    def create_messaging_system_info(self, vendor_name, destination_name,
                                     destination_type, channel):
        '''Creates a messaging system info object.

            This function creates a messaging system info object which is required for tracing
            sending, receiving and processing messages.

            :param str vendor_name:
                One of the constants from :class:`oneagent.common.MessagingVendor` for well known
                vendors, or a custom string otherwise.
            :param str destination_name:
                The "destination" name, i.e. queue name or topic name.
            :param MessagingDestinationType destination_type:
                One of the constants from :class:`oneagent.common.MessagingDestinationType`.
            :param Channel channel:
                The channel used for communication.

            :rtype: MessagingSystemInfoHandle

            .. versionadded:: 1.2.0
        '''

        return MessagingSystemInfoHandle(
            self._nsdk, self._nsdk.messagingsysteminfo_create(
                vendor_name, destination_name, destination_type, channel.type_, channel.endpoint))

    def trace_outgoing_message(self, messaging_system_info):
        '''Creates a tracer for tracing an outgoing message.

            :param MessagingSystemInfoHandle messaging_system_info:
                Messaging system information (see :meth:`create_messaging_system_info`)

            :rtype: tracers.OutgoingMessageTracer

            .. versionadded:: 1.2.0
        '''

        return tracers.OutgoingMessageTracer(
            self._nsdk, self._nsdk.outgoingmessagetracer_create(messaging_system_info.handle))

    def trace_incoming_message_receive(self, messaging_system_info):
        '''Creates a tracer for tracing the receipt of an incoming message.

            Tracing the receipt of the message is optional but may make sense if receiving
            may take a significant amount of time, e.g. when doing a blocking receive. It
            might make less sense when tracing a polling receive. If you do use a receive
            tracer, start and end the corresponding incoming message process tracer
            (see :meth:`trace_incoming_message_process`) while the receive tracer
            is still active.

            :param MessagingSystemInfoHandle messaging_system_info:
                Messaging system information (see :meth:`create_messaging_system_info`)

            :rtype: tracers.IncomingMessageReceiveTracer

            .. versionadded:: 1.2.0
        '''

        return tracers.IncomingMessageReceiveTracer(
            self._nsdk,
            self._nsdk.incomingmessagereceivetracer_create(messaging_system_info.handle))

    def trace_incoming_message_process(self, messaging_system_info, str_tag=None, byte_tag=None):
        '''Creates a tracer for tracing the processing of an incoming message.

            Use this tracer to trace the actual, logical processing of the message as opposed
            to the time it takes to receive it.
            If you use an incoming message receive tracer
            (see :meth:`trace_incoming_message_receive`) to trace the receipt of the
            processed message, start and end the corresponding incoming message process tracer
            while the receive tracer is still active.

            :param MessagingSystemInfoHandle messaging_system_info:
                Messaging system information (see :meth:`create_messaging_system_info`)
            :param str str_tag:
                The Dynatrace tag as string (see also :ref:`tagging`).
            :param bytes byte_tag:
                The Dynatrace tag as byte array.

            :rtype: tracers.IncomingMessageProcessTracer

            .. versionadded:: 1.2.0
        '''

        result = tracers.IncomingMessageProcessTracer(
            self._nsdk, self._nsdk.incomingmessageprocesstracer_create(
                messaging_system_info.handle))

        if result is not None:
            self._applytag(result, str_tag, byte_tag)

        return result

    #pylint:enable=invalid-name

    def trace_custom_service(self, service_method, service_name):
        '''Creates a tracer for custom services.

            Custom service tracers are used to trace service calls for which there is no other
            suitable tracer. To create a custom service tracer, an application can simply call
            :meth:`trace_custom_service`.

            For further information, see the high level SDK documentation at
            <https://github.com/Dynatrace/OneAgent-SDK/#customservice>

            : param str service_method:
                The name of the service method.
            : param str service_name:
                The name of the service.

            :rtype: tracers.CustomServiceTracer

            .. versionadded:: 1.2.0
        '''
        return tracers.CustomServiceTracer(
            self._nsdk, self._nsdk.customservicetracer_create(service_method, service_name))
