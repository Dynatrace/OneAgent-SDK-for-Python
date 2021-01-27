# -*- coding: utf-8 -*-
#
# Copyright 2019 Dynatrace LLC
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

'''This example demonstrates how to use the OneAgent SDK for Python in a
parent/child process environment. The OneAgent SDK for Python will be initialized
in the parent process and the child processes can then use the SDK.

Note: this example will only work on Linux. There's no Windows support available.
'''

import os
import sys

import oneagent # SDK initialization functions
import oneagent.sdk as onesdk # All other SDK functions.

try: # Python 2 compatibility.
    input = raw_input #pylint:disable=redefined-builtin
except NameError:
    pass


getsdk = oneagent.get_sdk # Just to make the code shorter.


def do_some_fancy_stuff(proc_number):
    sdk = getsdk()

    # Initially, the state in the child will be PRE_INITIALIZED (2).
    print('Agent fork state (child process before SDK call):', sdk.agent_fork_state)

    # The agent state in the child process should be ACTIVE (0).
    print('Agent state (child process #{}): {}'.format(proc_number, sdk.agent_state), flush=True)

    # After calling any SDK function but agent_fork_state,
    # the state in the child will be FULLY_INITIALIZED (3).
    # In this case the SDK function called was the agent_state property accessed above.
    print('Agent fork state (child process after SDK call):', sdk.agent_fork_state)

    print('Agent found:', sdk.agent_found)
    print('Agent is compatible:', sdk.agent_is_compatible)
    print('Agent version:', sdk.agent_version_string)

    # This call below will complete the OneAgent for Python SDK initialization and then it
    # will start the tracer for tracing the custom service
    with sdk.trace_custom_service('my_fancy_transaction', 'MyFancyService #{}'.format(proc_number)):
        print('do some fancy stuff')

def create_child_process(proc_number):
    pid = os.fork()
    if pid == 0:
        print('child #{} is running ...'.format(proc_number))
        do_some_fancy_stuff(proc_number)
        print('child #{} is exiting ...'.format(proc_number))
        sys.exit(0)

    return pid

def fork_children():
    print('now starting children ...', flush=True)
    pid_1 = create_child_process(1)
    pid_2 = create_child_process(2)

    print('waiting for child #1 ...', flush=True)
    os.waitpid(pid_1, 0)
    print('child #1 exited', flush=True)

    print('waiting for child #2 ...', flush=True)
    os.waitpid(pid_2, 0)
    print('child #2 exited', flush=True)

    print('all children exited', flush=True)

def main():
    # This gathers arguments prefixed with '--dt_' from sys.argv into the
    # returned list. See also the basic-sdk-sample.
    sdk_options = oneagent.sdkopts_from_commandline(remove=True)

    # Before using the SDK you have to initialize the OneAgent. In this scenario, we
    # initialize the SDK and prepare it for forking.
    #
    # Passing in the sdk_options is entirely optional and usually not required
    # as all settings will be automatically provided by the Dynatrace OneAgent
    # that is installed on the host.
    #
    # To activate the forking support add the optional 'forkable' parameter and set it to True.
    #
    # If you run this example on Windows then you'll get an "Invalid Argument" error back
    # because there's no forking support for Windows available.
    init_result = oneagent.initialize(sdk_options, forkable=True)
    try:
        if init_result.error is not None:
            print('Error during SDK initialization:', init_result.error)

        # While not by much, it is a bit faster to cache the result of
        # oneagent.get_sdk() instead of calling the function multiple times.
        sdk = getsdk()

        # The agent state is one of the integers in oneagent.sdk.AgentState.
        # Since we're using the 'forkable' mode the state will be TEMPORARILY_INACTIVE (1) on Linux.
        print('Agent state (parent process):', sdk.agent_state)

        # In the parent, the state will be PARENT_INITIALIZED (1).
        print('Agent fork state (parent process):', sdk.agent_fork_state)

        # The instance attribute 'agent_found' indicates whether an agent could be found or not.
        print('Agent found:', sdk.agent_found)

        # If an agent was found but it is incompatible with this version of the SDK for Python
        # then 'agent_is_compatible' would be set to false.
        print('Agent is compatible:', sdk.agent_is_compatible)

        # The agent version is a string holding both the OneAgent version and the
        # OneAgent SDK for C/C++ version separated by a '/'.
        print('Agent version:', sdk.agent_version_string)

        if init_result.error is None:
            fork_children()
            input('Now wait until the path appears in the UI ...')
    finally:
        shutdown_error = oneagent.shutdown()
        if shutdown_error:
            print('Error shutting down SDK:', shutdown_error)

if __name__ == '__main__':
    main()
