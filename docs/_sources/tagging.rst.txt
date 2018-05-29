.. _tagging:

Tagging
=======

.. currentmodule:: oneagent.sdk.tracers

Tagging allows you to link paths from different threads or processes
(potentially even running on completely different hosts) together, i.e. telling
Dynatrace that a particular path branched off from a particular other path node.
Semantically, this usually indicates some kind of remote-call, cross-thread call
or message flow.

The APIs for tagging are defined in the :class:`OutgoingTaggable` base class,
which allows retrieving a tag for attaching another path to that node, and in
the form of two optional and mutually exclusive :code:`byte_tag` or
:code:`str_tag` parameters to some :code:`trace_*` methods of
:class:`oneagent.sdk.SDK` (these are :dfn:`incoming-taggable`), which allows
attaching that node to the one with the given tag.

The following classes are incoming-taggable:

- :class:`IncomingRemoteCallTracer` /
  :meth:`oneagent.sdk.SDK.trace_incoming_remote_call`
- :class:`IncomingWebRequestTracer` / 
  :meth:`oneagent.sdk.SDK.trace_incoming_web_request`

The following classes are :class:`OutgoingTaggable`:

- :class:`OutgoingRemoteCallTracer`

You first use either :attr:`OutgoingTaggable.outgoing_dynatrace_string_tag` or
:attr:`OutgoingTaggable.outgoing_dynatrace_byte_tag` to retrieve a string or
binary tag from the tracer where you want branch off from. Then you somehow
forward the tag to the location you want to link. At this location, you pass
that tag as the corresponding :code:`tag` argument for a supported
:code:`trace_*` method.

Whether you use string or byte tags does not matter for the resulting paths (you
must not mix them, i.e. pass a byte tag as :code:`str_tag` or vice versa). Use
the one that is more convenient for you (e.g. if the tag must be transmitted via
text-based protocol, string tags are the natural choice). If you have no reason
to prefer string tags, byte tags are preferable because they are potentially
smaller and more efficient to process by Dynatrace.


Example
-------

For example let's say you want to gain insights into a client/server application
that communicates using a custom-built remoting protocol (e.g. over TCP/IP).
First you would instrument the applications separately using, e.g. using the
`trace_*` functions from :class:`oneagent.sdk.SDK` together with `with`-blocks::

   from oneagent.sdk import SDK, ChannelType, Channel

   # In the client:
   def call_remote(message):
      tracer = SDK.get().trace_outgoing_remote_call(
        'my_remote_function', 'MyRemoteService', 'MyRemoteEndpoint',
         Channel(ChannelType.TCP_IP, 'example.com:12345'))
      with tracer:
         myremotingchannel.send('my_remote_function', message)

   # In the server:
   def my_remote_function(message):
      tracer = SDK.get().trace_incoming_remote_call(
        'my_remote_function', 'MyRemoteService', 'MyRemoteEndpoint')
      with tracer:
         do_actual_work()

Now you will get two paths that will be completely unrelated from Dynatrace's
point of view. To change that, you do the following:

1. Obtain the outgoing tag at the call site.
2. Forward that tag through to the remote function.
3. In the remote function, pass the tag (which is now an incoming tag) when
   creating the tracer.

The result after doing this could look like this:

.. code-block:: python
   :emphasize-lines: 9-10,15,17

   from oneagent.sdk import SDK, ChannelType, Channel

   # In the client:
   def call_remote(message):
      tracer = SDK.get().trace_outgoing_remote_call(
        'my_remote_function', 'MyRemoteService', 'MyRemoteEndpoint',
         Channel(ChannelType.TCP_IP, 'example.com:12345'))
      with tracer: # Starts the tracer; required for obtaining a tag!
         tag = tracer.outgoing_dynatrace_byte_tag
         message.add_header('Dynatrace-Tag', tag) # Or some such
         myremotingchannel.send('my_remote_function', message)

   # In the server:
   def my_remote_function(message):
      tag = message.get_header_optional('Dynatrace-Tag')
      tracer = SDK.get().trace_incoming_remote_call(
        'my_remote_function', 'MyRemoteService', 'MyRemoteEndpoint',
        byte_tag=tag)
      with tracer:
         do_actual_work()

Note these points:

* You are responsible for forwarding the tag yourself. Apart from initially
  giving you a binary or string tag, the SDK can give you no help here. E.g. in
  the example above it is assumed that our remoting protocol allows adding
  arbitrary headers.
* Do not depend on the availability of the tag on the receiver side: you should
  always be careful to not introduce additional failure modes into your
  application when using the Dynatrace SDK.
* The outgoing tag can only be obtained between starting and ending the tracer.
* You should take care that obtaining the incoming tag is not an expensive
  operation, as it can not be accounted for in the timings of the resulting
  path.
