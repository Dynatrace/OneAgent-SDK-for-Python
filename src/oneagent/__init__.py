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

'''oneagent main module. Contains initialization and logging functionality.

.. data:: logger

    The :class:`logging.Logger` on which managed Python SDK messages will be
    written.

    This logger has set the log level so that no messages are displayed by
    default. Use, for example, :code:`oneagent.logger.setLevel(logging.INFO)` to
    see them. See :ref:`logging-basic-tutorial` in the official Python
    documentation for more on configuring the logger.

.. class:: InitResult

    Information about the success of a call to :func:`.initialize`. Instances of
    this class are falsy iff :attr:`.status` is negative.

    .. attribute:: status

        A :class:`int` with more information about the status. One of the
        :code:`.STATUS_*` constants in this class.

    .. attribute:: error

        A :class:`Exception` that occured during this initialization attempt.
        Usually, but not necessarily a :class:`oneagent.common.SDKError`.
        Another exception class might indicate an incompatible Python version.

    .. data:: STATUS_STUB_LOAD_ERROR

        A negative status code, meaning that the native SDK stub could not be
        loaded. This usually indicates that the Dynatrace OneAgent SDK for
        Python was incorrectly installed (but see :attr:`error`). Note that even
        in this case, a dummy implementation of the SDK is available so that
        calls to SDK functions do not fail (but they will be no-ops).

    .. data:: STATUS_INIT_ERROR

        A negative status code, meaning that error occurred during
        initialization of the SDK. This usually indicates a problem with the
        Dynatrace OneAgent installation on the host (but see :attr:`error`).

    .. data:: STATUS_INITIALIZED

        This status code is equal to zero and means that the SDK has
        successfully been initialized. :attr:`error` is always :data:`None` with
        this status.

    .. data:: STATUS_INITIALIZED_WITH_WARNING

        A positive status code meaning that the SDK has sucessfully been
        initialized, but there have been some warnings (e.g., some options could
        not be processed, or the agent is permanently inactive).

    .. data:: STATUS_ALREADY_INITIALIZED

        A positive status code meaning that the SDK has already been initialized
        (not necessarily with success), i.e., :func:`initialize` has already been
        called.
        :attr:`error` is always :data:`None` with this status.
'''

import logging
import sys
from collections import namedtuple
from threading import Lock

from oneagent._impl.six.moves import range #pylint:disable=import-error
from oneagent.version import __version__

from .common import (
    SDKError, SDKInitializationError, ErrorCode,
    _ONESDK_INIT_FLAG_FORKABLE, _add_enum_helpers)
from ._impl.native import nativeagent
from ._impl.native.nativeagent import try_get_sdk
from ._impl.native.sdknulliface import SDKNullInterface
from ._impl.native.sdkdllinfo import WIN32

if hasattr(sys, 'implementation'):
    def _get_py_edition():
        return sys.implementation.name # pylint:disable=no-member
else:
    import platform

    def _get_py_edition():
        return platform.python_implementation()

logger = logging.getLogger('py_sdk')
logger.setLevel(logging.CRITICAL + 1) # Disabled by default

_PROCESS_TECH_PYTHON = 28
_PROCESS_TECH_ONEAGENT_SDK = 118

def _get_py_version():
    return '.'.join(map(str, sys.version_info[:3])) + (
        '' if sys.version_info.releaselevel == "final"
        else sys.version_info.releaselevel + str(sys.version_info.serial))

@_add_enum_helpers
class InitResult(namedtuple('InitResult', 'status error')):
    __slots__ = ()

    STATUS_STUB_LOAD_ERROR = -2
    STATUS_INIT_ERROR = -1
    STATUS_INITIALIZED = 0
    STATUS_INITIALIZED_WITH_WARNING = 1
    STATUS_ALREADY_INITIALIZED = 2

    __nonzero__ = __bool__ = lambda self: self.status >= 0

    def __repr__(self):
        return "InitResult(status={}, error={!r})".format(
            self._value_name(self.status), self.error) #pylint:disable=no-member


_sdk_ref_lk = Lock()
_sdk_ref_count = 0
_should_shutdown = False

_sdk_instance = None

def sdkopts_from_commandline(argv=None, remove=False, prefix='--dt_'):
    '''Creates a SDK option list for use with the :code:`sdkopts` parameter of
    :func:`.initialize` from a list :code:`argv` of command line parameters.

    An element in :code:`argv` is treated as an SDK option if starts with
    :code:`prefix`. The return value of this function will then contain the
    remainder of that parameter (without the prefix). If :code:`remove` is
    :data:`True`, these arguments will be removed from :code:`argv`.

    :param argv: An iterable of command line parameter
        strings. Defaults to :data:`sys.argv`. Must be a
        :obj:`~typing.MutableSequence` if :code:`remove` is :data:`True`.
    :type argv: ~typing.Iterable[str] or ~typing.MutableSequence[str]
    :param bool remove: Whether to remove a command line parameter that was
        recognized as an SDK option from :code:`argv` (if :data:`True`) or leave
        :code:`argv` unmodified (if :data:`False`). If :data:`True`,
        :code:`argv` must be a :obj:`~typing.MutableSequence`.
    :param str prefix: The prefix string by which SDK options are recognized and
        which is removed from the copy of the command line parameter that is
        added to the return value.

    :rtype: list[str]
    '''

    if argv is None:
        argv = sys.argv

    if not remove:
        return [param[len(prefix):] for param in argv
                if param.startswith(prefix)]
    result = []
    for i in range(len(argv) - 1, -1, -1):
        if argv[i].startswith(prefix):
            result.append(argv[i][len(prefix):])
            del argv[i]
    result.reverse()
    return result

def get_sdk():
    '''Returns a shared :class:`oneagent.sdk.SDK` instance.

    Repeated calls to this function are supported and will always return the
    same object.

    .. note:: You have to initialize the SDK first using :meth:`initialize`
        before this function will return a valid SDK instance.

    .. versionadded:: 1.1.0
    '''
    global _sdk_instance #pylint:disable=global-statement

    if _sdk_instance is None:
        return SDK(SDKNullInterface())

    return _sdk_instance

def initialize(sdkopts=(), sdklibname=None, forkable=False):
    '''Attempts to initialize the SDK with the specified options.

    Even if initialization fails, a dummy SDK will be available so that SDK
    functions can be called but will do nothing.

    If you call this function multiple times, you must call :func:`shutdown`
    just as many times. The options from all but the first :code:`initialize` call
    will be ignored (the return value will have the
    :data:`InitResult.STATUS_ALREADY_INITIALIZED` status code in that case).

    When setting the ``forkable`` flag the OneAgent SDK for Python will only be partly
    initialized. In this special **parent-initialized** initialization state, only the following
    functions can be called:

    * All functions that are valid to call before calling initialize remain valid.
    * :meth:`oneagent.sdk.SDK.agent_version_string` works as expected.
    * :meth:`oneagent.sdk.SDK.agent_state` will return
        :data:`oneagent.common.AgentState.TEMPORARILY_INACTIVE` - but see the note below.
    * :meth:`oneagent.sdk.SDK.set_diagnostic_callback` and
      :meth:`oneagent.sdk.SDK.set_verbose_callback` work as expected,
      the callback will be  carried over to forked child processes.
    * It is recommended you call :func:`shutdown` when the original process will not fork any more
        children that want to use the SDK.

    After you fork, the child becomes **pre-initialized**: the first call to an SDK function that
    needs a **fully initialized** agent will automatically complete the initialization.

    You can still fork another child (e.g. in a double-fork scenario) in the **pre-initialized**
    state. However if you fork another child in the **fully initialized** state, it will not be
    able to use the SDK - not even if it tries to shut down the SDK and initialize it again.

    .. note:: Calling :meth:`oneagent.sdk.SDK.agent_state` in the **pre-initialized** state will
        cause the agent to become **fully initialized**.

    All children forked from a **parent-initialized** process will use the same agent. That agent
    will shut down when all child processes and the original **parent-initialized** process have
    terminated or called shutdown. Calling :func:`shutdown` in a **pre-initialized** process is
    not required otherwise.

    :param sdkopts: A sequence of strings of the form
        :samp:`{NAME}={VALUE}` that set the given SDK options. Ignored in all but
        the first :code:`initialize` call.
    :type sdkopts: ~typing.Iterable[str]
    :param str sdklibname: The file or directory name of the native C SDK
        DLL. If None, the shared library packaged directly with the agent is
        used. Using a value other than None is only acceptable for debugging.
        You are responsible for providing a native SDK version that matches the
        Python SDK version.
    :param bool forkable: Use the SDK in 'forkable' mode.

    :rtype: InitResult
    '''

    global _sdk_ref_count #pylint:disable=global-statement
    global _sdk_instance #pylint:disable=global-statement

    with _sdk_ref_lk:
        logger.debug("initialize: ref count = %d", _sdk_ref_count)
        result = _try_init_noref(sdkopts, sdklibname, forkable)
        if _sdk_instance is None:
            _sdk_instance = SDK(try_get_sdk())
        _sdk_ref_count += 1
    return result


def _try_init_noref(sdkopts=(), sdklibname=None, forkable=False):
    global _should_shutdown #pylint:disable=global-statement

    sdk = nativeagent.try_get_sdk()
    if sdk:
        logger.debug(
            'Attempt to re-initialize agent'
            ' with options=%s, libname=%s only increases'
            ' reference count.',
            sdkopts,
            sdklibname)

        return InitResult(InitResult.STATUS_ALREADY_INITIALIZED, None)

    try:
        logger.info(
            'Initializing SDK on Python=%s with options=%s, libname=%s.',
            (sys.version or '?').replace('\n', '  ').replace('\r', ''), sdkopts, sdklibname)
        sdk = nativeagent.initialize(sdklibname)

        have_warning = False
        for opt in sdkopts:
            err = sdk.stub_set_variable(opt, False)
            if err:
                have_warning = True
                logger.warning(
                    'stub_set_variable failed for "%s" with error 0x%x: %s',
                    opt,
                    err,
                    sdk.strerror(err))

        if WIN32 and forkable:
            logger.warning('SDK can''t be initialized in forkable mode on Windows and Solaris')

        flags = _ONESDK_INIT_FLAG_FORKABLE if forkable else 0

        nativeagent.checkresult(sdk, sdk.initialize(flags), 'onesdk_initialize_2')
        _should_shutdown = True
        logger.debug('initialize successful, adding tech types...')
        sdk.ex_agent_add_process_technology(_PROCESS_TECH_ONEAGENT_SDK, 'Python', __version__)
        sdk.ex_agent_add_process_technology(
            _PROCESS_TECH_PYTHON, _get_py_edition(), _get_py_version())
        logger.debug('tech type reporting complete')
        return InitResult(
            (InitResult.STATUS_INITIALIZED_WITH_WARNING if have_warning else
             InitResult.STATUS_INITIALIZED),
            None)
    except Exception as e: #pylint:disable=broad-except
        _should_shutdown = False
        #pylint:disable=no-member
        if isinstance(e, SDKError) and e.code == ErrorCode.AGENT_NOT_ACTIVE:
        #pylint:enable=no-member
            logger.debug('initialized, but agent not active')
            return InitResult(InitResult.STATUS_INITIALIZED_WITH_WARNING, e)
        logger.exception('Failed initializing agent.')
        sdk = nativeagent.try_get_sdk()
        if sdk:
            logger.warning('Continuing with stub-SDK only.')
            return InitResult(InitResult.STATUS_INIT_ERROR, e)

        _v = '-/-' if not isinstance(e, SDKInitializationError) else e.agent_version

        nativeagent.initialize(SDKNullInterface(version=_v))

        logger.warning('Continuing with NULL-SDK only.')
        return InitResult(InitResult.STATUS_STUB_LOAD_ERROR, e)

def shutdown():
    '''Shut down the SDK.

    :returns: An exception object if an error occurred, a falsy value otherwise.

    :rtype: Exception
    '''
    global _sdk_ref_count #pylint:disable=global-statement
    global _sdk_instance #pylint:disable=global-statement
    global _should_shutdown #pylint:disable=global-statement

    with _sdk_ref_lk:
        logger.debug("shutdown: ref count = %d, should_shutdown = %s", \
                     _sdk_ref_count, _should_shutdown)
        nsdk = nativeagent.try_get_sdk()
        if not nsdk:
            logger.warning('shutdown: SDK not initialized or already shut down')
            _sdk_ref_count = 0
            return None
        if _sdk_ref_count > 1:
            logger.debug('shutdown: reference count is now %d', _sdk_ref_count)
            _sdk_ref_count -= 1
            return None
        logger.info('shutdown: Shutting down SDK.')
        try:
            if _should_shutdown:
                _rc = nsdk.shutdown()
                if _rc == ErrorCode.NOT_INITIALIZED:
                    logger.warning('shutdown: native SDK was not initialized')
                else:
                    nativeagent.checkresult(nsdk, _rc, 'shutdown')
                _should_shutdown = False
        except SDKError as e:
            logger.warning('shutdown failed', exc_info=sys.exc_info())
            return e
        _sdk_ref_count = 0
        _sdk_instance = None
        nativeagent._force_initialize(None) #pylint:disable=protected-access
        logger.debug('shutdown: completed')
        return None

#pylint:disable=wrong-import-position
from .sdk import SDK # Public
