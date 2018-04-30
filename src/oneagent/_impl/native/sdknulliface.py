# -*- coding: utf-8 -*-
'''SDK interface with null implementation, for testing etc.'''

from __future__ import print_function

import sys

from oneagent._impl import six

from oneagent.common import ErrorCode, AgentState

NULL_HANDLE = 0

class SDKNullInterface(object): #pylint:disable=too-many-public-methods
    def __init__(self):
        self._diag_cb = None
        self._log_cb = None

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
        return ''

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
