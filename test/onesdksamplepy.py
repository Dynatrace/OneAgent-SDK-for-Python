# -*- coding: utf-8 -*-
'''This example demonstrates instrumenting a (mocked) application that executes
a remote call that sometimes fails and does some database operations.'''

from __future__ import print_function # Python 2 compatibility.

import threading

import oneagent # SDK initialization functions
import oneagent.sdk as onesdk # All other SDK functions.

getsdk = onesdk.SDK.get # Just to make the code shorter.

def traced_db_operation(dbinfo, sql):
    print('+db', dbinfo, sql)

    # Entering the with block automatically start the tracer.
    with getsdk().trace_sql_database_request(dbinfo, sql) as tracer:

        # In real-world code, you would do the actual database operation here,
        # i.e. call the database's API.

        # Set an optional "exit"-field. On the tracer. Whenever there is a
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
        'dummyPyMethod', 'DummyPyService', 'dummyEndpoint',
        onesdk.Channel(onesdk.ChannelType.IN_PROCESS, 'localhost'),
        protocol_name='DUMMY_PY_PROTOCOL')
    try:
        with call:

            # Note that this property can only be accessed after starting the
            # tracer. See the documentation on tagging for more information.
            strtag = call.outgoing_dynatrace_string_tag

            if not success:
                # This demonstrates how an exception leaving a tracer's
                # with-block will mark the tracer as failed.
                raise RuntimeError('remote error message')
            do_remote_call(strtag)
    except RuntimeError: # Swallow the exception raised above.
        pass
    print('-remote')

failed = [False]

def do_remote_call_thread_func(strtag):
    try:
        print('+thread')
        # We use positional arguments to specify required values and named
        # arguments to specify optional values.
        incall = getsdk().trace_incoming_remote_call(
            'dummyPyMethod', 'DummyPyService', 'dummyEndpoint',
            protocol_name='DUMMY_PY_PROTOCOL', str_tag=strtag)
        with incall:
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
    except Exception:
        failed[0] = True
        raise


def do_remote_call(strtag):
    # This function simulates doing a remote call by calling a function
    # do_remote_call_thread_func in another thread, passing a string tag. See
    # the documentation on tagging for more information.

    workerthread = threading.Thread(
        target=do_remote_call_thread_func,
        args=(strtag,))
    workerthread.start()

    # Note that we need to join the thread, as all tagging assumes synchronous
    # calls.
    workerthread.join()

    assert not failed[0]


def main():
    print('+main')

    # If you do not call try_init() manually, the first call to
    # oneagent.sdk.SDK.get() will attempt to initialize the SDK with default
    # options, swallowing any errors, which is why manually calling try_init()
    # is recommended.
    init_result = oneagent.try_init()
    try:
        if init_result.error is not None:
            print('Error during SDK initialization:', init_result.error)

        # While not by much, it is a bit faster to cache the result of
        # oneagent.sdk.SDK.get() instead of calling the function multiple times.
        sdk = getsdk()

        # The agent state is one of the integers in oneagent.sdk.AgentState.
        print('Agent state:', sdk.agent_state)

        # The agent version is the version of the installed OneAgent, not the
        # version of the SDK.
        print('Agent version:', sdk.agent_version_string)

        # We use trace_incoming_remote_call here, because it is one of the few
        # calls that create a new path if none is running yet.
        with sdk.trace_incoming_remote_call('main', 'main', 'main'):
            # Simulate some remote calls
            outgoing_remote_call(success=True)
            outgoing_remote_call(success=True)
            outgoing_remote_call(success=False)
        print('-main')
    finally:
        shutdown_error = oneagent.shutdown()
        if shutdown_error:
            print('Error shutting down SDK:', shutdown_error)

if __name__ == '__main__':
    main()
