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

'''This example demonstrates instrumenting a (mocked) application that executes
a remote call that sometimes fails and does some database operations.'''

from __future__ import print_function # Python 2 compatibility.

import threading

import oneagent # SDK initialization functions
import oneagent.sdk as onesdk # All other SDK functions.

from oneagent.common import MessagingDestinationType


try: # Python 2 compatibility.
    input = raw_input #pylint:disable=redefined-builtin
except NameError:
    pass

getsdk = oneagent.get_sdk # Just to make the code shorter.

def traced_db_operation(dbinfo, sql):
    print('+db', dbinfo, sql)

    # Entering the with block automatically start the tracer.
    with getsdk().trace_sql_database_request(dbinfo, sql) as tracer:

        # In real-world code, you would do the actual database operation here,
        # i.e. call the database's API.

        # Set an optional "exit"-field on the tracer. Whenever there is a
        # setter available on a tracer (as opposed to an optional parameter to a
        # trace_* function), it may be called anytime between creating and
        # ending the tracer (i.e. also after starting it).
        tracer.set_round_trip_count(3)

    print('-db', dbinfo, sql)

def outgoing_remote_call(success):
    print('+remote')

    # We use positional arguments to specify required values and named arguments
    # to specify optional values.
    call = getsdk().trace_outgoing_remote_call(
        'dummyPyMethod', 'DummyPyService', 'dupypr://localhost/dummyEndpoint',
        onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'localhost'),
        protocol_name='DUMMY_PY_PROTOCOL')
    try:
        with call:

            # Note that this property can only be accessed after starting the
            # tracer. See the documentation on tagging for more information.
            strtag = call.outgoing_dynatrace_string_tag
            do_remote_call(strtag, success)
    except RuntimeError: # Swallow the exception raised above.
        pass
    print('-remote')

failed = [None]

def do_remote_call_thread_func(strtag, success):
    try:
        print('+thread')
        # We use positional arguments to specify required values and named
        # arguments to specify optional values.
        incall = getsdk().trace_incoming_remote_call(
            'dummyPyMethod', 'DummyPyService',
            'dupypr://localhost/dummyEndpoint',
            protocol_name='DUMMY_PY_PROTOCOL', str_tag=strtag)
        with incall:
            if not success:
                raise RuntimeError('Remote call failed on the server side.')
            dbinfo = getsdk().create_database_info(
                'Northwind', onesdk.DatabaseVendor.SQLSERVER,
                onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.0.0.42:6666'))

            # This with-block will automatically free the database info handle
            # at the end. Note that the handle is used for multiple tracers. In
            # general, it is recommended to reuse database (and web application)
            # info handles as often as possible (for efficiency reasons).
            with dbinfo:
                traced_db_operation(
                    dbinfo, "BEGIN TRAN;")
                traced_db_operation(
                    dbinfo,
                    "SELECT TOP 1 qux FROM baz ORDER BY quux;")
                traced_db_operation(
                    dbinfo,
                    "SELECT foo, bar FROM baz WHERE qux = 23")
                traced_db_operation(
                    dbinfo,
                    "UPDATE baz SET foo = foo + 1 WHERE qux = 23;")
                traced_db_operation(dbinfo, "COMMIT;")
        print('-thread')
    except Exception as e:
        failed[0] = e
        raise


def do_remote_call(strtag, success):
    # This function simulates doing a remote call by calling a function
    # do_remote_call_thread_func in another thread, passing a string tag. See
    # the documentation on tagging for more information.

    failed[0] = None
    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(strtag, success))
    workerthread.start()

    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

    if failed[0] is not None:
        raise failed[0] #pylint:disable=raising-bad-type

def mock_incoming_web_request():
    sdk = getsdk()
    wappinfo = sdk.create_web_application_info(
        virtual_host='example.com', # Logical name of the host server.
        application_id='MyWebApplication', # Unique web application ID.
        context_root='/my-web-app/') # App's prefix of the path part of the URL.

    with wappinfo:
        # This with-block will automatically free web application info handle
        # at the end. Note that the handle can be used for multiple tracers. In
        # general, it is recommended to reuse web application info handles as
        # often as possible (for efficiency reasons). For example, if you use
        # WSGI, the web application info could be stored as an attribute of the
        # application object.
        #
        # Note that different ways to specify headers, response headers and
        # parameter (form fields) not shown here also exist. Consult the
        # documentation for trace_incoming_web_request and
        # IncomingWebRequestTracer.
        wreq = sdk.trace_incoming_web_request(
            wappinfo,
            'http://example.com/my-web-app/foo?bar=baz',
            'GET',
            headers={'Host': 'example.com', 'X-foo': 'bar'},
            remote_address='127.0.0.1:12345')
        with wreq:
            wreq.add_parameter('my_form_field', '1234')
            # Process web request
            wreq.add_response_headers({'Content-Length': '1234'})
            wreq.set_status_code(200) # OK

            # Add 3 different custom attributes.
            sdk.add_custom_request_attribute('custom int attribute', 42)
            sdk.add_custom_request_attribute('custom float attribute', 1.778)
            sdk.add_custom_request_attribute('custom string attribute', 'snow is falling')

            # This call will trigger the diagnostic callback.
            sdk.add_custom_request_attribute('another key', None)

            # This call simulates incoming messages.
            mock_process_incoming_message()

def _process_my_outgoing_request(_tag):
    pass

def mock_outgoing_web_request():
    sdk = getsdk()

    # Create tracer and and request headers.
    tracer = sdk.trace_outgoing_web_request('http://example.com/their-web-app/bar?foo=foz', 'GET',
                                            headers={'X-not-a-useful-header': 'python-was-here'})

    with tracer:
        # Now get the outgoing dynatrace tag. You have to add this tag as request header to your
        # request if you want that the path is continued on the receiving site. Use the constant
        # oneagent.common.DYNATRACE_HTTP_HEADER_NAME as request header name.
        tag = tracer.outgoing_dynatrace_string_tag

        # Here you process and send your web request.
        _process_my_outgoing_request(tag)

        # As soon as the response is received, you can add the response headers to the
        # tracer and you shouldn't forget to set the status code, too.
        tracer.add_response_headers({'Content-Length': '1234'})
        tracer.set_status_code(200) # OK

def mock_process_incoming_message():
    sdk = getsdk()

    # Create the messaging system info object.
    msi_handle = sdk.create_messaging_system_info(
        'MyPythonSenderVendor', 'MyPythonDestination', MessagingDestinationType.QUEUE,
        onesdk.Channel(onesdk.ChannelType.UNIX_DOMAIN_SOCKET, 'MyPythonChannelEndpoint'))

    with msi_handle:
        # Create the receive tracer for incoming messages.
        with sdk.trace_incoming_message_receive(msi_handle):
            print('here we wait for incoming messages ...')

            # Create the tracer for processing incoming messages.
            tracer = sdk.trace_incoming_message_process(msi_handle)

            # Now we can set the vendor message and correlation IDs. It's possible to set them
            # either before the tracer is started or afterwards. But they have to be set before
            # the tracer ends.
            tracer.set_vendor_message_id('message_id')
            with tracer:
                print('handle incoming message')
                tracer.set_correlation_id('correlation_id')

def mock_outgoing_message():
    sdk = getsdk()

    # Create the messaging system info object.
    msi_handle = sdk.create_messaging_system_info(
        'MyPythonReceiverVendor', 'MyPythonDestination', MessagingDestinationType.TOPIC,
        onesdk.Channel(onesdk.ChannelType.TCP_IP, '10.11.12.13:1415'))

    with msi_handle:
        # Create the outgoing message tracer;
        with sdk.trace_outgoing_message(msi_handle) as tracer:
            # Set the message and correlation IDs.
            tracer.set_vendor_message_id('msgId')
            tracer.set_correlation_id('corrId')

            print('handle outgoing message')

def mock_custom_service():
    sdk = getsdk()

    with sdk.trace_custom_service('my_fancy_transaction', 'MyFancyService'):
        print('do some fancy stuff')

def _diag_callback(text):
    print(text)

def main():
    print('+main')

    # This gathers arguments prefixed with '--dt_' from sys.argv into the
    # returned list. See initialize below.
    sdk_options = oneagent.sdkopts_from_commandline(remove=True)

    # Before using the SDK you have to initialize the OneAgent. You can call oneagent.initialize()
    # as often as you want, but you also have to call oneagent.shutdown() for every call to
    # initialize() as well.
    #
    # Passing in the sdk_options is entirely optional and usually not required
    # as all settings will be automatically provided by the Dynatrace OneAgent
    # that is installed on the host.
    init_result = oneagent.initialize(sdk_options)
    try:
        if init_result.error is not None:
            print('Error during SDK initialization:', init_result.error)

        # While not by much, it is a bit faster to cache the result of
        # oneagent.get_sdk() instead of calling the function multiple times.
        sdk = getsdk()

        # Set the diagnostic callback.
        sdk.set_diagnostic_callback(_diag_callback)

        # The agent state is one of the integers in oneagent.sdk.AgentState.
        print('Agent state:', sdk.agent_state)

        # The instance attribute 'agent_found' indicates whether an agent could be found or not.
        print('Agent found:', sdk.agent_found)

        # If an agent was found but it is incompatible with this version of the SDK for Python
        # then 'agent_is_compatible' would be set to false.
        print('Agent is compatible:', sdk.agent_is_compatible)

        # The agent version is a string holding both the OneAgent version and the
        # OneAgent SDK for C/C++ version separated by a '/'.
        print('Agent version:', sdk.agent_version_string)

        mock_incoming_web_request()

        mock_outgoing_web_request()

        mock_outgoing_message()

        mock_custom_service()

        # We use trace_incoming_remote_call here, because it is one of the few
        # calls that create a new path if none is running yet.
        with sdk.trace_incoming_remote_call('main', 'main', 'main'):
            # We want to start an asynchronous execution at this time, so we create an
            # in-process link which we will use afterwards (or in a different thread).
            link = sdk.create_in_process_link()

            # Simulate some remote calls
            outgoing_remote_call(success=True)
            outgoing_remote_call(success=True)
            outgoing_remote_call(success=False)

        # Now the asynchronous execution starts. So we create an in-process tracer. We're using
        # the in-process link which we've created above. This link specifies where the traced
        # actions below will show up in the path.
        with sdk.trace_in_process_link(link):
            outgoing_remote_call(success=True)

        print('-main')
        input('Now wait until the path appears in the UI...')
    finally:
        shutdown_error = oneagent.shutdown()
        if shutdown_error:
            print('Error shutting down SDK:', shutdown_error)

if __name__ == '__main__':
    main()
