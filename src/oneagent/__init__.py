# -*- coding: utf-8 -*-
'''oneagent main module. Contains initialization and logging functionality.

.. data:: logger

    The :class:`logging.Logger` on which managed Python SDK messages will be
    written.

    This logger has set the log level so that no messages are displayed by
    default. Use e.g. :code:`oneagent.logger.setLevel(logging.INFO)` to see
    them. See :ref:`logging-basic-tutorial` in the official Python
    documentation for more on configuring the logger.

.. class:: InitResult

    Information about the success of a call to :func:`.try_init`. Instances of
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
        initialized, but there have been some warnings (e.g. some options could
        not be processed, or the agent is permanently inactive).

    .. data:: STATUS_ALREADY_INITIALIZED

        A positive status code meaning that the SDK has already been initialized
        (not necessarily with success), i.e. :func:`try_init` has already been
        called (possibly implicitly via :meth:`oneagent.sdk.SDK.get`).
        :attr:`error` is always :data:`None` with this status.
'''

import logging
import sys
from collections import namedtuple
from threading import Lock

from oneagent._impl.six.moves import range #pylint:disable=import-error

from .common import SDKError, ErrorCode
from ._impl.native import nativeagent

# See https://www.python.org/dev/peps/pep-0440/ "Version Identification and
# Dependency Specification"
__version__ = '1.0.0'

logger = logging.getLogger('py_sdk')
logger.setLevel(logging.CRITICAL + 1) # Disabled by default

class InitResult(namedtuple('InitResult', 'status error')):
    __slots__ = ()

    STATUS_STUB_LOAD_ERROR = -2
    STATUS_INIT_ERROR = -1
    STATUS_INITIALIZED = 0
    STATUS_INITIALIZED_WITH_WARNING = 1
    STATUS_ALREADY_INITIALIZED = 2

    __nonzero__ = __bool__ = lambda self: self.status >= 0


_sdk_ref_lk = Lock()
_sdk_ref_count = 0

def sdkopts_from_commandline(argv=None, remove=False, prefix='--dt_'):
    '''Creates a SDK option list for use with the :code:`sdkopts` parameter of
    :func:`.try_init` from a list :code:`argv` of command line parameters.

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


def try_init(sdkopts=(), sdklibname=None):
    '''Attempts to initialize the SDK with the specified options.

    Even if initialization fails, a dummy SDK will be available so that SDK
    functions can be called but will do nothing.

    If you call this function multiple times, you must call :func:`shutdown`
    just as many times. The options from all but the first :code:`try_init` call
    will be ignored (the return value will have the
    :data:`InitResult.STATUS_ALREADY_INITIALIZED` status code in that case).

    :param sdkopts: A sequence of strings of the form
        :samp:`{NAME}={VALUE}` that set the given SDK options. Igored in all but
        the first :code:`try_init` call.
    :type sdkopts: ~typing.Iterable[str]
    :param str sdklibname: The file or directory name of the native C SDK
        DLL. If None, the shared library packaged directly with the agent is
        used. Using a value other than None is only acceptable for debugging.
        You are responsible for providing a native SDK version that matches the
        Python SDK version.

    :rtype: .InitResult
    '''

    global _sdk_ref_count #pylint:disable=global-statement

    with _sdk_ref_lk:
        result = _try_init_noref(sdkopts, sdklibname)
        _sdk_ref_count += 1
    return result


def _try_init_noref(sdkopts=(), sdklibname=None):
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
            'Initializing SDK with options=%s, libname=%s.',
            sdkopts, sdklibname)
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

        nativeagent.checkresult(sdk, sdk.initialize(), 'onesdk_initialize')
        return InitResult(
            (InitResult.STATUS_INITIALIZED_WITH_WARNING if have_warning else
             InitResult.STATUS_INITIALIZED),
            None)
    except Exception as e: #pylint:disable=broad-except
        #pylint:disable=no-member
        if isinstance(e, SDKError) and e.code == ErrorCode.AGENT_NOT_ACTIVE:
        #pylint:enable=no-member
            return InitResult(InitResult.STATUS_INITIALIZED_WITH_WARNING, e)
        logger.exception('Failed initializing agent.')
        sdk = nativeagent.try_get_sdk()
        if sdk:
            logger.warning('Continuing with stub-SDK only.')
            return InitResult(InitResult.STATUS_INIT_ERROR, e)
        from ._impl.native.sdknulliface import SDKNullInterface
        nativeagent.initialize(SDKNullInterface())
        logger.warning('Continuing with NULL-SDK only.')
        return InitResult(InitResult.STATUS_STUB_LOAD_ERROR, e)


def shutdown():
    '''Shut down the SDK.

    :returns: An exception object if an error occurred, a falsy value otherwise.

    :rtype: Exception
    '''
    global _sdk_ref_count #pylint:disable=global-statement

    with _sdk_ref_lk:
        nsdk = nativeagent.try_get_sdk()
        if not nsdk:
            return None
        if _sdk_ref_count > 1:
            _sdk_ref_count -= 1
            return None
        try:
            nativeagent.checkresult(nsdk, nsdk.shutdown(), 'shutdown')
        except SDKError as e:
            logger.warning('shutdown failed', exc_info=sys.exc_info())
            return e
        _sdk_ref_count = 0
        nativeagent._force_initialize(None) #pylint:disable=protected-access
        return None

#pylint:disable=wrong-import-position
from .sdk import SDK # Public
