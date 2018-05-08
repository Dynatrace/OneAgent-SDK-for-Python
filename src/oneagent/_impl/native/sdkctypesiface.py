# -*- coding: utf-8 -*-
'''ctypes SDK wrapper for use as oneagent.nativeagent backend.

Allows accessing (most) functions of the onesdk_shared DLL in a type-safe but
low-level manner.
'''

import ctypes
import ctypes.util
import sys
from os import path
from functools import wraps

from oneagent import logger
from oneagent._impl import six
from oneagent.common import SDKError, ErrorCode

from .sdkdllinfo import WIN32, dll_name, _dll_name_in_home

CCSID_NULL = 0
CCSID_ASCII = 367
CCSID_ISO8859_1 = 819 # Latin-1
CCSID_UTF8 = 1209
CCSID_UTF16_BE = 1201
CCSID_UTF16_LE = 1203


bool_t = ctypes.c_int32
result_t = ctypes.c_uint32 if WIN32 else ctypes.c_int32
xchar_p = ctypes.c_wchar_p if WIN32 else ctypes.c_char_p
ccsid_t = ctypes.c_uint16
handle_t = ctypes.c_uint64
c_size_p = ctypes.POINTER(ctypes.c_size_t)
log_level_t = ctypes.c_int32
callback_base = ctypes.WINFUNCTYPE if WIN32 else ctypes.CFUNCTYPE
stub_logging_callback_t = callback_base(None, log_level_t, xchar_p)
agent_logging_callback_t = callback_base(None, ctypes.c_char_p)

if six.PY3:
    str_to_u8 = str.encode # Defaults to UTF-8 in Py3 (ASCII in Py2)
else:
    def str_to_u8(unicode_str):
        return unicode_str.encode('utf-8')

def u8_to_str(u8_bytes):
    return u8_bytes.decode('utf-8', 'replace')

class CCString(ctypes.Structure):
    _fields_ = (
        ('data', ctypes.c_void_p),
        ('bytes_length', ctypes.c_size_t),
        ('ccsid', ccsid_t))

    @classmethod
    def from_param(cls, pystr): # Special name for ctypes
        if isinstance(pystr, six.binary_type):
            return cls.from_u8_bytes(pystr)
        if pystr is None:
            return NULL_STR
        assert isinstance(pystr, six.text_type), \
            'Attempt to pass non-string type to SDK function expecting a' \
            ' string. Actual type: ' + str(type(pystr))
        return cls.from_unicode(pystr)

    @classmethod
    def from_u8_bytes(cls, pybstr):
        return cls(
            ctypes.cast(ctypes.c_char_p(pybstr), ctypes.c_void_p),
            len(pybstr),
            CCSID_UTF8)

    @classmethod
    def from_unicode(cls, pyustr):
        return cls.from_u8_bytes(str_to_u8(pyustr))


NULL_STR = CCString(None, 0, CCSID_NULL)

class XStrPInArg(object):
    '''ctypes argument type for xchar pointers.'''
    @staticmethod
    def from_param(pystr):
        return xchar_p(toxstr(pystr))

class CCStringPInArg(object):
    '''ctypes argument type for CCString pointers.'''
    @staticmethod
    def from_param(pystr):
        return ctypes.byref(CCString.from_param(pystr))


if xchar_p is ctypes.c_wchar_p:
    mkxstrbuf = ctypes.create_unicode_buffer
    def toxstr(pystr):
        if isinstance(pystr, six.text_type):
            return pystr
        return u8_to_str(pystr)
    def ufromxstr(xstr):
        return xstr
else:
    mkxstrbuf = ctypes.create_string_buffer
    def toxstr(pystr):
        if isinstance(pystr, six.binary_type):
            return pystr
        return str_to_u8(pystr)
    def ufromxstr(xstr):
        return u8_to_str(xstr)


class SDKDllInterface(object):

    _ONESDK_PREFIX = 'onesdk_'

    @classmethod
    def _fn_basename(cls, name):
        assert name.startswith(cls._ONESDK_PREFIX), \
            name + ' does not start with onesdk-prefix'
        name = name[len(cls._ONESDK_PREFIX):]
        if name.endswith('_p'):
            name = name[:-2]
        return name

    def _initfn(self, name, args, ret, public=True):
        fullname = self._ONESDK_PREFIX + name
        func = getattr(self._dll, fullname)
        func.argtypes = args
        func.restype = ret
        name = self._fn_basename(fullname)
        if not public:
            name = '_' + name
        setattr(self, name, func)
        return func

    def __init__(self, libname):
        self._log_cb = None
        self._diag_cb = None
        self._py_diag_cb = None

        self._dll = ctypes.WinDLL(libname) if WIN32 else ctypes.CDLL(libname)

        initfn = self._initfn

        # Args
        initfn(
            'stub_is_sdk_cmdline_arg',
            (XStrPInArg,),
            bool_t)
        initfn(
            'stub_process_cmdline_arg',
            (XStrPInArg, bool_t),
            result_t).__doc__ = '''(arg, replace_existing) -> result

            This expects arg in the format "--dt_<varname>=<value>".
            '''
        initfn(
            'stub_set_variable',
            (XStrPInArg, bool_t),
            result_t).__doc__ = '''(var_spec, replace_existing) -> result

            This expects var_spec in the format "<name>=<value>"
            '''

        # Missing: stub_strip_sdk_cmdline_args: Adding a Python implementation
        # of this would probably easier and more efficient than dealing with
        # modifying a string array.

        initfn(
            'stub_set_logging_level',
            (log_level_t,),
            None)
        initfn(
            'stub_default_logging_function',
            (log_level_t, XStrPInArg),
            None)
        initfn(
            'stub_set_logging_callback',
            (stub_logging_callback_t,),
            None,
            public=False)
        initfn(
            'stub_free_variables',
            (),
            None)

        # Init/Shutdown
        initfn(
            'agent_get_version_string',
            (),
            xchar_p,
            public=False)
        initfn(
            'initialize',
            (),
            result_t)
        initfn(
            'shutdown',
            (),
            result_t)

        # Missing: agent_internl_dispatch(int32, void*); probably useless

        initfn(
            'agent_get_current_state',
            (),
            ctypes.c_int32)
        initfn(
            'agent_set_logging_callback',
            (agent_logging_callback_t,),
            None,
            public=False)

        initfn(
            'stub_xstrerror',
            (result_t, xchar_p, ctypes.c_size_t),
            xchar_p,
            public=False)

        # Specific nodes

        ## Database
        initfn(
            'databaseinfo_create_p',
            (CCStringPInArg, CCStringPInArg, ctypes.c_int32, CCStringPInArg),
            handle_t).__doc__ = \
                '(dbname, dbvendor, chan_ty, chan_ep) -> dbh'
        initfn(
            'databaserequesttracer_create_sql_p',
            (handle_t, CCStringPInArg),
            handle_t)
        initfn(
            'databaserequesttracer_set_returned_row_count',
            (handle_t, ctypes.c_int32),
            None)
        initfn(
            'databaserequesttracer_set_round_trip_count',
            (handle_t, ctypes.c_int32),
            None)
        initfn(
            'databaseinfo_delete',
            (handle_t,),
            None)

        ## Outgoing remote call
        initfn(
            'outgoingremotecalltracer_create_p',
            (CCStringPInArg, CCStringPInArg, CCStringPInArg,
             ctypes.c_int32, CCStringPInArg),
            handle_t).__doc__ = \
                '(svcmethod, svcname, svcendpoint, chan_ty, chan_ep) -> tracer'
        initfn(
            'outgoingremotecalltracer_set_protocol_name_p',
            (handle_t, CCStringPInArg),
            None)

        ## Incoming remote call
        initfn(
            'incomingremotecalltracer_create_p',
            (CCStringPInArg, CCStringPInArg, CCStringPInArg),
            handle_t).__doc__ = \
                '(svc_method, svc_name, svc_endpoint) -> tracer'
        initfn(
            'incomingremotecalltracer_set_protocol_name_p',
            (handle_t, CCStringPInArg),
            handle_t)

        ## Incoming Webrequest
        initfn(
            'webapplicationinfo_create_p',
            (CCStringPInArg, CCStringPInArg, CCStringPInArg),
            handle_t).__doc__ = "(vhost, appid, ctxroot) -> wsh"
        initfn(
            'webapplicationinfo_delete',
            (handle_t,),
            None)
        initfn(
            'incomingwebrequesttracer_create_p',
            (handle_t, CCStringPInArg, CCStringPInArg),
            handle_t).__doc__ = "(wsh, uri, http_method) -> tracerh"
        headerlist_arg_ts = (
            handle_t,
            ctypes.POINTER(CCString),
            ctypes.POINTER(CCString),
            ctypes.c_size_t)
        self._wrap_headerlist_fn(initfn(
            'incomingwebrequesttracer_add_request_headers_p',
            headerlist_arg_ts,
            None,
            public=False))
        self._wrap_headerlist_fn(initfn(
            'incomingwebrequesttracer_add_response_headers_p',
            headerlist_arg_ts,
            None,
            public=False))
        self._wrap_headerlist_fn(initfn(
            'incomingwebrequesttracer_add_parameters_p',
            headerlist_arg_ts,
            None,
            public=False))
        initfn(
            'incomingwebrequesttracer_set_remote_address_p',
            (handle_t, CCStringPInArg),
            None)
        initfn(
            'incomingwebrequesttracer_set_status_code',
            (handle_t, ctypes.c_int32),
            None)


        # Generic nodes
        initfn(
            'tracer_start',
            (handle_t,),
            None)
        initfn(
            'tracer_end',
            (handle_t,),
            None)
        initfn(
            'tracer_error_p',
            (handle_t, CCStringPInArg, CCStringPInArg),
            None).__doc__ = \
                '''Mark tracer handle as failed with given error_class and
                error_message.

                tracer_end still needs to be called on the handle.'''
        initfn(
            'tracer_get_outgoing_dynatrace_string_tag',
            (handle_t, ctypes.c_char_p, ctypes.c_size_t, c_size_p),
            ctypes.c_size_t,
            public=False)

        # We just handle unsigned char* as char*
        initfn(
            'tracer_get_outgoing_dynatrace_byte_tag',
            (handle_t, ctypes.c_char_p, ctypes.c_size_t, c_size_p),
            ctypes.c_size_t,
            public=False)

        self.tracer_set_incoming_string_tag = initfn(
            'tracer_set_incoming_dynatrace_string_tag_p',
            (handle_t, CCStringPInArg),
            None,
            public=False)

        initfn(
            'tracer_set_incoming_dynatrace_byte_tag',
            (handle_t, ctypes.c_char_p, ctypes.c_size_t),
            None,
            public=False)

    def _wrap_headerlist_fn(self, func):
        fn_name = self._fn_basename(func.__name__)
        assert fn_name.endswith('s')
        fn_singular_name = fn_name[:-1]

        @wraps(func)
        def headerlist_fn(handle, keys, values, count):
            if count is None:
                count = len(keys)
            arr_t = CCString * count
            key_arr = arr_t()
            for i, key in enumerate(keys):
                key_arr[i] = CCString.from_param(key)
            val_arr = arr_t()
            for i, value in enumerate(values):
                val_arr[i] = CCString.from_param(value)
            return func(handle, key_arr, val_arr, count)
        headerlist_fn.__doc__ = "(tracer, keys, values, count)"

        def single_header_fn(handle, key, value):
            return func(
                handle,
                CCStringPInArg.from_param(key),
                CCStringPInArg.from_param(value),
                1)
        single_header_fn.__doc__ = "(tracer, key, value)"
        single_header_fn.__name__ = fn_singular_name

        setattr(self, fn_name, headerlist_fn)
        setattr(self, fn_singular_name, single_header_fn)
        return headerlist_fn, single_header_fn

    def strerror(self, error_code):
        buf = mkxstrbuf(1024)
        return ufromxstr(self._stub_xstrerror(error_code, buf, 1024))

    def stub_set_logging_callback(self, sink):
        if sink is None:
            self._stub_set_logging_callback(
                ctypes.cast(None, stub_logging_callback_t))
            self._log_cb = None
        else:
            def cb_wrapper(level, msg):
                return sink(level, ufromxstr(msg))
            c_cb = stub_logging_callback_t(cb_wrapper)
            self._stub_set_logging_callback(c_cb)
            self._log_cb = c_cb

    def agent_get_version_string(self):
        return ufromxstr(self._agent_get_version_string())

    def agent_set_logging_callback(self, callback):
        if callback is None:
            self._agent_set_logging_callback(
                ctypes.cast(None, agent_logging_callback_t))
            self._diag_cb = None
            self._py_diag_cb = None
        else:

            @wraps(callback)
            def cb_wrapper(msg):
                if isinstance(msg, six.binary_type):
                    msg = u8_to_str(msg)
                return callback(msg)

            c_cb = agent_logging_callback_t(cb_wrapper)
            self._agent_set_logging_callback(c_cb)
            self._diag_cb = c_cb
            self._py_diag_cb = cb_wrapper

    def __del__(self):
        # __del__ is also called when __init__ fails, so safeguard against that
        if hasattr(self, '_agent_set_logging_callback'):
            self.agent_set_logging_callback(None)
        if hasattr(self, '_stub_set_logging_callback'):
            self.stub_set_logging_callback(None)

    def agent_get_logging_callback(self):
        return self._py_diag_cb

    def tracer_get_outgoing_tag(self, tracer, use_byte_tag=False):
        tagsz = ctypes.c_size_t()
        getter = (
            self._tracer_get_outgoing_dynatrace_byte_tag if use_byte_tag
            else self._tracer_get_outgoing_dynatrace_string_tag)
        getter(tracer, None, 0, tagsz)
        buf = ctypes.create_string_buffer(tagsz.value)
        cnt = getter(tracer, buf, tagsz, None)
        if use_byte_tag:
            assert cnt == tagsz.value
            return buf.raw
        assert cnt + 1 == tagsz.value
        return buf.value

    def tracer_set_incoming_byte_tag(self, tracer, tag):
        self._tracer_set_incoming_dynatrace_byte_tag(tracer, tag, len(tag))


def loadsdk(libname=None):
    if libname:
        logger.warning('Overriding C SDK location with %s', libname)
        if not path.isfile(libname):
            libname = _dll_name_in_home(libname)
    else:
        try:
            import pkg_resources
            libname = pkg_resources.resource_filename(__name__, dll_name())
        except ImportError:
            logger.warning(
                'Could not import pkg_resources module:'
                ' loading SDK native library might fail',
                exc_info=sys.exc_info())
            thisdir = path.dirname(path.abspath(__file__))
            libname = path.join(thisdir, dll_name())

    try:
        logger.info('Loading native sdk "%s".', libname)
        return SDKDllInterface(libname)
    except OSError as e:
        msg = 'Failed loading SDK stub from ' + libname + ': ' + str(e)
        six.raise_from(SDKError(ErrorCode.LOAD_AGENT, msg), e)
