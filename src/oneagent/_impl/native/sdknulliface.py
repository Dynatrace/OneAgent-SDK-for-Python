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

'''SDK interface with null implementation, for testing etc.'''

from __future__ import print_function

import sys

from oneagent._impl import six

from oneagent.common import ErrorCode, AgentState

NULL_HANDLE = 0

class SDKNullInterface(object): #pylint:disable=too-many-public-methods
    def __init__(self, version='-/-'):
        self._diag_cb = None
        self._log_cb = None
        self._agent_version = version

    #pylint:disable=no-self-use,unused-argument

    def stub_is_sdk_cmdline_arg(self, arg):
        return arg.startswith('--dt_')

    def stub_process_cmdline_arg(self, arg, replace):
        return ErrorCode.AGENT_NOT_ACTIVE

    def stub_set_variable(self, assignment, replace):
        return ErrorCode.AGENT_NOT_ACTIVE

    def stub_set_logging_level(self, level):
        pass

    def stub_default_logging_function(self, level, msg):
        print('[OneSDK:NULL]', level, msg, file=sys.stderr)

    def stub_set_logging_callback(self, sink):
        self._log_cb = sink

    def stub_free_variables(self):
        pass

    def agent_get_version_string(self):
        return self._agent_version

    def agent_found(self):
        return False

    def agent_is_compatible(self):
        return False

    def initialize(self):
        return ErrorCode.AGENT_NOT_ACTIVE

    def shutdown(self):
        return ErrorCode.SUCCESS

    def agent_get_current_state(self):
        # Although PERMANENTLY_INACTIVE might be more fitting, NOT_INITIALIZED
        # is what the stub also returns if it cannot find the agent.
        return AgentState.NOT_INITIALIZED

    def agent_set_logging_callback(self, callback):
        self._diag_cb = callback

    def agent_get_logging_callback(self):
        return self._diag_cb

    def strerror(self, error_code):
        if error_code == ErrorCode.AGENT_NOT_ACTIVE:
            return u'The agent is inactive.'
        return u'Unknown error ' + str(error_code)

    def webapplicationinfo_create(self, vhost, appid, ctxroot):
        return NULL_HANDLE

    def webapplicationinfo_delete(self, handle):
        pass

    def incomingwebrequesttracer_create(self, wapp_h, uri, http_method):
        return NULL_HANDLE

    #pylint:disable=invalid-name

    def incomingwebrequesttracer_add_request_headers(
            self, tracer_h, keys, vals, count):
        pass

    def incomingwebrequesttracer_add_request_header(self, tracer_h, key, val):
        pass

    def incomingwebrequesttracer_add_response_headers(
            self, tracer_h, keys, vals, count):
        pass

    def incomingwebrequesttracer_add_response_header(self, tracer_h, key, val):
        pass

    def incomingwebrequesttracer_add_parameters(
            self, tracer_h, keys, vals, count):
        pass

    def incomingwebrequesttracer_add_parameter(self, tracer_h, key, val):
        pass

    def incomingwebrequesttracer_set_remote_address(self, tracer_h, addr):
        pass

    def incomingwebrequesttracer_set_status_code(self, tracer_h, code):
        pass

    #pylint:enable=invalid-name

    def outgoingwebrequesttracer_create(self, uri, http_method):
        return NULL_HANDLE

    #pylint:disable=invalid-name

    def outgoingwebrequesttracer_add_request_headers(
            self, tracer_h, keys, vals, count):
        pass

    def outgoingwebrequesttracer_add_request_header(self, tracer_h, key, val):
        pass

    def outgoingwebrequesttracer_add_response_headers(
            self, tracer_h, keys, vals, count):
        pass

    def outgoingwebrequesttracer_add_response_header(self, tracer_h, key, val):
        pass

    def outgoingwebrequesttracer_set_status_code(self, tracer_h, code):
        pass

    #pylint:enable=invalid-name

    def databaseinfo_create(self, dbname, dbvendor, chan_ty, chan_ep):
        return NULL_HANDLE

    #pylint:disable=invalid-name

    def databaserequesttracer_create_sql(
            self, dbh, sql):
        return NULL_HANDLE

    def databaserequesttracer_set_returned_row_count(
            self, tracer_h, count):
        pass

    def databaserequesttracer_set_round_trip_count(
            self, tracer_h, count):
        pass

    #pylint:enable=invalid-name

    def databaseinfo_delete(self, dbh):
        pass

    def outgoingremotecalltracer_create( #pylint:disable=too-many-arguments
            self, svc_method, svc_name, svc_endpoint, chan_ty, chan_ep):
        return NULL_HANDLE

    def outgoingremotecalltracer_set_protocol_name( #pylint:disable=invalid-name
            self, tracer_h, protocol_name):
        pass

    def incomingremotecalltracer_create(
            self, svc_method, svc_name, svc_endpoint):
        return NULL_HANDLE

    def incomingremotecalltracer_set_protocol_name( #pylint:disable=invalid-name
            self, tracer_h, protocol_name):
        pass

    def tracer_start(self, tracer_h):
        pass

    def tracer_end(self, tracer_h):
        pass

    def tracer_error(self, tracer_h, error_class, error_message):
        pass

    def tracer_get_outgoing_tag(self, tracer_h, use_byte_tag=False):
        if use_byte_tag:
            return six.binary_type()
        return six.text_type()

    def tracer_set_incoming_string_tag(self, tracer_h, tag):
        pass

    def tracer_set_incoming_byte_tag(self, tracer_h, tag):
        pass

    #pylint:disable=invalid-name

    def customrequestattribute_add_integers(self, keys, values, count):
        pass

    def customrequestattribute_add_integer(self, key, value):
        pass

    def customrequestattribute_add_floats(self, keys, values, count):
        pass

    def customrequestattribute_add_float(self, key, value):
        pass

    def customrequestattribute_add_strings(self, keys, values, count):
        pass

    def customrequestattribute_add_string(self, key, value):
        pass

    def trace_in_process_link(self, link_bytes):
        pass

    def create_in_process_link(self):
        pass

    # Messaging API

    #pylint:disable=too-many-arguments
    def messagingsysteminfo_create(self, vendor_name, destination_name, destination_type,
                                   channel_type, channel_endpoint):
        return NULL_HANDLE

    def messagingsysteminfo_delete(self, handle):
        pass

    def outgoingmessagetracer_create(self, handle):
        return NULL_HANDLE

    def outgoingmessagetracer_set_vendor_message_id(self, handle, vendor_message_id):
        pass

    def outgoingmessagetracer_set_correlation_id(self, handle, correlation_id):
        pass

    def incomingmessagereceivetracer_create(self, handle):
        return NULL_HANDLE

    def incomingmessageprocesstracer_create(self, handle):
        return NULL_HANDLE

    def incomingmessageprocesstracer_set_vendor_message_id(self, handle, message_id):
        pass

    def incomingmessageprocesstracer_set_correlation_id(self, handle, correlation_id):
        pass

    #pylint:enable=too-many-arguments
    #pylint:enable=invalid-name

    def customservicetracer_create(self, service_method, service_name):
        return NULL_HANDLE
