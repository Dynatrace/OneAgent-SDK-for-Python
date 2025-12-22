.. _encoding:

String encoding and unicode issues
==================================

This section mostly concerns Python 2.

When the documentation says that a :class:`str` is accepted, an :class:`unicode`
is also always accepted on Python 2. What is more, when the documentation says
that a :class:`str` is returned or passed to a callback, on Python 2 it is
actually a :class:`unicode` (you mostly don't need to care about that though,
because most string operations on Python 2 allow mixing :class:`str` and
:class:`unicode`).

When passing a :class:`bytes` object (or, equivalently, a :code:`str` object on
Python 2) to a SDK function that says that it accepts a :class:`str`, the bytes
will be interpreted as being UTF-8 encoded. Beware: If the string has invalid
UTF-8 (e.g., Latin-1/ISO-8859-1, as it may occur in :ref:`HTTP headers
<http-encoding-warning>`), the function to which it was passed may fail either
partially or fully. Such failures are guaranteed to neither throw exceptions nor
violate any invariants of the involved objects, but some or all of the
information passed in that function call may be lost (for example, a single
invalid HTTP header passed to
:meth:`oneagent.sdk.SDK.trace_incoming_web_request` may cause an null-tracer to
be returned -- but it is also allowed to, for example, truncate that HTTP header
and discard all that follow; the exact failure mode is undefined and you should
take care to not pass invalid strings). Also, the diagnostic callback
(:meth:`oneagent.sdk.SDK.set_diagnostic_callback`) may be invoked (but is not
guaranteed to).

.. _http-encoding-warning:

HTTP Request and Response Header Encoding
-----------------------------------------

The strings passed to the :code:`add_request_header()`, :code:`add_request_headers()`,
:code:`add_parameter()`, :code:`add_parameters()`, :code:`add_response_header()` and
:code:`add_response_headers()` methods of the :class:`oneagent.sdk.tracers.IncomingWebRequestTracer`
and :class:`oneagent.sdk.tracers.OutgoingWebRequestTracer` classes follow the usual SDK
:ref:`encoding <encoding>` conventions, i.e., must be either unicode strings or UTF-8 bytes objects.

.. warning:: However, `HTTP <https://tools.ietf.org/html/rfc7230#section-3.2.4>`_ and `Python's WSGI
	<https://www.python.org/dev/peps/pep-3333/#unicode-issues>`_ will use the Latin-1 encoding on
	Python 2. Before passing such Python 2 native strings to these methods, use
	:code:`s.decode('Latin-1')` (see :meth:`bytes.decode`) to convert the string to unicode, which
	can be correctly handled.
