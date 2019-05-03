> Read the latest version of this README, with working internal links, at [GitHub](https://github.com/Dynatrace/OneAgent-SDK-for-Python#readme).

# Dynatrace OneAgent SDK for Python

This SDK enables Dynatrace customers to extend request level visibility into Python applications. It provides the Python implementation of the [Dynatrace OneAgent SDK](https://github.com/Dynatrace/OneAgent-SDK).

<!-- Generate with https://github.com/jonschlinkert/markdown-toc -->

<!-- toc -->

- [Requirements](#requirements)
- [Using the OneAgent SDK for Python in your application](#using-the-oneagent-sdk-for-python-in-your-application)
- [API Concepts](#api-concepts)
  * [Initialization and SDK objects](#initialization-and-sdk-objects)
  * [Tracers](#tracers)
- [Features and how to use them](#features-and-how-to-use-them)
  * [Remote calls](#remote-calls)
  * [SQL database requests](#sql-database-requests)
  * [Incoming web requests](#incoming-web-requests)
  * [Outgoing web requests](#outgoing-web-requests)
  * [Trace in-process asynchronous execution](#trace-in-process-asynchronous-execution)
  * [Custom request attributes](#custom-request-attributes)
  * [Custom services](#custom-services)
  * [Messaging](#messaging)
    * [Outgoing Messages](#outgoing-messaging)
    * [Incoming Messages](#incoming-messaging)
- [Troubleshooting](#troubleshooting)
  * [Installation issues](#installation-issues)
  * [Post-installation issues](#post-installation-issues)
- [Repository contents](#repository-contents)
- [Help & Support](#help--support)
  * [Read the manual](#read-the-manual)
  * [Let us help you](#let-us-help-you)
- [Release notes](#release-notes)
- [License](#license)

<!-- tocstop -->

<a name="requirements"></a>
## Requirements

The SDK supports Python 2 ≥ 2.7 and Python 3 ≥ 3.4. Only the official CPython (that is, the "normal" Python, i.e. the Python implementation
from <https://python.org>) is supported and only on Linux (musl libc is currently not supported) and Windows with the x86 (including
x86-64) architecture. Additionally, `pip` ≥ 8.1.0 (2016-03-05) is required for installation.

The Dynatrace OneAgent SDK for Python is a wrapper of the [Dynatrace OneAgent SDK for C/C++](https://github.com/Dynatrace/OneAgent-SDK-for-C)
and therefore the SDK for C/C++ is required and delivered with the Python SDK. See
[here](https://github.com/Dynatrace/OneAgent-SDK-for-C#dynatrace-oneagent-sdk-for-cc-requirements)
for its requirements, which also apply to the SDK for Python.

The version of the SDK for C/C++ that is included in each version of the SDK for Python is shown in the following table along with the required
Dynatrace OneAgent version (it is the same as
[listed in the OneAgent SDK for C/C++'s documentation](https://github.com/Dynatrace/OneAgent-SDK-for-C/blob/master/README.md#compatibility-of-dynatrace-oneagent-sdk-for-cc-releases-with-oneagent-releases)).

<a name="pycversiontab"></a>

|OneAgent SDK for Python|OneAgent SDK for C/C++|Dynatrace OneAgent|
|:----------------------|:---------------------|:-----------------|
|1.0                    |1.1.0                 |≥1.141            |
|1.1                    |1.3.1                 |≥1.151            |
|1.2                    |1.4.1                 |≥1.161            |

<a name="#using-the-oneagent-sdk-for-python-in-your-application"></a>
## Using the OneAgent SDK for Python in your application

<a name="installation"></a>

To install the latest version of the OneAgent SDK for Python, use the PyPI package
`oneagent-sdk`:

```bash
python -m pip install --upgrade oneagent-sdk
```

To verify your installation, execute

```bash
python -c "import oneagent; print(oneagent.initialize())"
```

If the installation was successful, you should get an output ending with `InitResult(status=0, error=None)`. Otherwise, see the [Troubleshooting](#troubleshooting) section.

To load the OneAgent SDK into your application, just add the following line at the top of your script:

```python
import oneagent
```

Here is a quick "Hello World" that will produce a service call in Dynatrace:

```python
import oneagent

if not oneagent.initialize():
    print('Error initializing OneAgent SDK.')

with oneagent.get_sdk().trace_incoming_remote_call('method', 'service', 'endpoint'):
    pass

print('It may take a few moments before the path appears in the UI.')
input('Please wait...')
oneagent.shutdown()
```

A more detailed [sample application is available here](https://github.com/Dynatrace/OneAgent-SDK-for-Python/blob/master/samples/basic-sdk-sample/basic_sdk_sample.py).
See also the Quickstart section in the [API documentation](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/quickstart.html).


<a name="api-concepts"></a>
## API Concepts

Common concepts of the Dynatrace OneAgent SDK are explained in the [Dynatrace OneAgent SDK repository](https://github.com/Dynatrace/OneAgent-SDK#apiconcepts).

<a name="initialization-and-sdk-objects"></a>
### Initialization and SDK objects

Before first using any other SDK functions, you need to initialize the SDK.

```python
init_result = oneagent.initialize()
print('OneAgent SDK initialization result' + repr(init_result))
if init_result:
    print('SDK should work (but agent might be inactive).')
if not init_result:
    print('SDK will definitely not work (i.e. functions will be no-ops).')
```

See the API documentation for the [`initialize` function](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.initialize)
and the [`InitResult` class](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.InitResult) for more information.

To use the SDK, get a reference to the [`SDK`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK)
singleton by calling the oneagent static [`get_sdk`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.get_sdk)
method. The first thing you may want to do with this object, is checking if the agent is active by comparing the value of the
[`agent_state`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.agent_state)
property to the [`oneagent.common.AgentState`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.common.AgentState)
constants. You can also have a look at the [extended SDK state information](#extended-sdk-state).

```python
import oneagent
from oneagent.common import AgentState
# Initialize oneagent, as above

sdk = oneagent.get_sdk()
if sdk.agent_state not in (AgentState.ACTIVE, AgentState.TEMPORARILY_INACTIVE):
    print('Too bad, you will not see data from this process.')
```

As a development and debugging aid it is recommended to set a diagnostic callback. The callback will be used by the SDK to inform about unusual events.

Unusual events that prevent an operation from completing successfully include:
* API usage errors
* other unexpected events (like out of memory situations)

> **NOTE**: Use this as a development and debugging aid only. Your application should not rely on a calling sequence or any message content being set
or passed to the callback.

```python
def _diag_callback(unicode_message):
	print(unicode_message)

sdk.set_diagnostic_callback(_diag_callback)
```


<a name="tracers"></a>
### Tracers

To trace any kind of call you first need to create a
[Tracer](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.Tracer),
using one of the various `trace_*` methods of the
[`SDK`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK)
object. The Tracer object controls the “life cycle” of a trace: Entering a
`with`-block with a tracer starts the trace, exiting it ends it. Exiting the
`with` block with an exception causes the trace to be marked as failed with the
exception message (if you do not want or need this behavior, tracers have
explicit methods for starting, ending and attaching error information too; see the
[documentation](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.Tracer)).

There are different tracer types requiring different information for creation.
As an example, to trace an incoming remote call, this would be the most simple
way to trace it:

```python
import oneagent

with oneagent.get_sdk().trace_incoming_remote_call('method', 'service', 'endpoint'):
    pass # Here you would do the actual work that is timed
```

See the section on [remote calls](#remote-calls) for more information.

Some tracers also support attaching additional information before ending it.

**Important:** In Python 2, tracers accept both byte (“normal”) and unicode
strings. Byte strings must always use the UTF-8 encoding!


<a name="features-and-how-to-use-them"></a>
## Features and how to use them

The feature sets differ slightly with each language implementation. More functionality will be added over time, see
[Planned features for OneAgent SDK](https://answers.dynatrace.com/spaces/483/dynatrace-product-ideas/idea/198106/planned-features-for-oneagent-sdk.html)
for details on upcoming features.

A more detailed specification of the features can be found in [Dynatrace OneAgent SDK](https://github.com/Dynatrace/OneAgent-SDK#features).

|Feature    |Required OneAgent SDK for Python version|
|:-----------------------------------------|:--------|
|Trace incoming and outgoing remote calls  |≥1.0.0   |
|SQL database requests                     |≥1.0.0   |
|Incoming web requests                     |≥1.0.0   |
|Outgoing web requests                     |≥1.1.0   |
|Custom request attributes                 |≥1.1.0   |
|In-process linking                        |≥1.1.0   |
|Messaging                                 |≥1.2.0   |
|Custom services                           |≥1.2.0   |

<a name="remote-calls"></a>
### Remote calls

You can use the SDK to trace communication from one process to another. This will enable you to see full Service Flow, PurePath and Smartscape topology
for remoting technologies that Dynatrace is not aware of.

To trace any kind of remote call you first need to create a Tracer. The Tracer object represents the endpoint that you want to call, thus you need to
supply the name of the remote service and method. In addition, you need to transport a tag in your remote call from the client side to the server side
if you want to trace it end to end.

On the client side, you would trace the outgoing remote call like this:

```python
outcall = sdk.trace_outgoing_remote_call(
    'remoteMethodToCall', 'RemoteServiceName', 'rmi://Endpoint/service',
    oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, 'remoteHost:1234'),
    protocol_name='RMI/custom')
with outcall:
    # Note: You can access outgoing_dynatrace_*_tag only after the trace
    # has started!
    strtag = outcall.outgoing_dynatrace_string_tag
    do_actual_remote_call(extra_headers={'X-dynaTrace': strtag})
```

On the server side, you would trace it like this:

```python
incall = sdk.trace_incoming_remote_call(
    'remoteMethodToCall', 'RemoteServiceName', 'rmi://Endpoint/service',
    protocol_name='RMI/custom',
    str_tag=my_remote_message.get_header_optional('X-dynaTrace'))
with incall:
    pass # Here you would do the actual work that is timed
```

See the documentation for more information:

* [`trace_incoming_remote_call`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_incoming_remote_call)
* [`trace_outgoing_remote_call`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.trace_outgoing_remote_call)
* [General information on tagging](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/tagging.html)

<a name="sql-database-requests"></a>
### SQL database requests

To trace database requests you need a database info object which stores the information about your database which does not change between individual
requests. This will typically be created somewhere in your initialization code (after initializing the SDK):

```python
dbinfo = sdk.create_database_info(
    'Northwind', oneagent.sdk.DatabaseVendor.SQLSERVER,
    oneagent.sdk.Channel(oneagent.sdk.ChannelType.TCP_IP, '10.0.0.42:6666'))
```

Then you can trace the SQL database requests:

```python
with sdk.trace_sql_database_request(dbinfo, 'SELECT foo FROM bar;') as tracer:
    # Do actual DB request
    tracer.set_rows_returned(42) # Optional
    tracer.set_round_trip_count(3) # Optional
```

Note that you need to release the database info object. You can do this by calling `close()` on it or using it in a `with` block.

See the documentation for more information:

* [`create_database_info`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.create_database_info)
* [`trace_sql_database_request`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_sql_database_request)
* [`DatabaseRequestTracer`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.DatabaseRequestTracer)

<a name="incoming-web-requests"></a>
### Incoming web requests

[Same as with database infos](#sql-database-requests), to trace incoming web requests you need a web application info object which stores the
information about your web application which does not change:

```python
wappinfo = sdk.create_web_application_info(
    virtual_host='example.com',
    application_id='MyWebApplication',
    context_root='/my-web-app/')
```

Then you can trace incoming web requests:

```python
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
```

Note that you need to release the web application info object. You can do this by calling `close()` on it or using it in a `with` block.

Incoming web request tracers support some more features not shown here. Be sure to check out the documentation:

* [`create_web_application_info`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.create_web_application_info)
* [`trace_incoming_web_request`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_incoming_web_request)
* [`IncomingWebRequestTracer`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.IncomingWebRequestTracer)


<a name="outgoing-web-requests"></a>
### Outgoing web requests

To trace an outgoing web request you need to create an 'Outgoing Web Request Tracer' object. You pass the destination URL, the HTTP method and
request headers as parameters.

Let's have a look at a web request example:
```python
from urllib.request import Request

# Create your web request.
url = 'http://example.com'

req = Request(url)
req.add_header('header1', '1234')
req.add_header('header2', '5678')
```

After creating/setting up the request you have to create the tracer object and pass the parameters.

```python
# Create the tracer.
tracer = sdk.trace_outgoing_web_request(url, req.get_method(), req.headers)
```

The next step is to start the tracer and then to retrieve the outgoing Dynatrace tag. The tag is being used to trace a transaction from end-to-end.
You have to send the tag to the destination via an additional request header which is called
[`DYNATRACE_HTTP_HEADER_NAME`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.common.DYNATRACE_HTTP_HEADER_NAME).
[Here you can find more information on tagging](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/tagging.html).

```python
with tracer:
	# Get and set the Dynatrace tag.
	tag = tracer.outgoing_dynatrace_string_tag
 	req.add_header(DYNATRACE_HTTP_HEADER_NAME, tag)

	# Here you process and send the web request.
	response = _process_your_outgoing_request(req)
```

Finally, get the response headers you want to trace and the status code of the response and add them to the tracer.

```python
        tracer.add_response_headers({'Content-Length': response.get_content_length()})
        tracer.set_status_code(response.get_status_code())
```

Be sure to check out the documentation:
* [`trace_outgoing_web_request`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_outgoing_web_request)
* [`OutgoingWebRequestTracer`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.OutgoingWebRequestTracer)
* [General information on tagging](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/tagging.html)


<a name="trace-in-process-asynchronous-execution"></a>
### Trace in-process asynchronous execution

You can use the SDK to trace asynchronous in-process code execution. This might be useful if the OneAgent does not support the threading framework
or specific asynchronous libraries. In-process linking should be used to link other services (Database, Webrequests, ...) between thread or
queueing boundaries currently not supported out-of-the-box by the OneAgent.

To link asynchronous execution, you need to create an in-process link, where the execution forks:

```python
in_process_link = sdk.create_in_process_link()
```

The provided in-process link must not be serialized and can only be used inside the process in which it was created. It must be used to start
tracing where the asynchronous execution takes place:

```python
with sdk.trace_in_process_link(in_process_link):
 	# Do the asynchronous job
 	:
```

<a name="custom-request-attributes"></a>
### Custom Request Attributes

You can use the SDK to add custom request attributes to the currently traced service. Custom request attributes allow you to do easier/better
filtering of your requests in Dynatrace.

Adding custom request attributes to the currently traced service call is pretty simple. Just call the `add_custom_request_attribute` method
with your key and value (only int, float and string values are currently supported):

```python
sdk.add_custom_request_attribute('errorCount', 42)
sdk.add_custom_request_attribute('gross weight', 2.39)
sdk.add_custom_request_attribute('famous actor', 'Benedict Cumberbatch')
```

Check out the documentation at:
* [`add_custom_request_attribute`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.add_custom_request_attribute)


<a name="custom-services"></a>
### Custom services
You can use the SDK to trace custom service methods. A custom service method is a meaningful part
of your code that you want to trace but that does not fit any other tracer. An example could be
the callback of a periodic timer.

```python
with sdk.trace_custom_service('onTimer', 'CleanupTask'):
	# Do the cleanup task
	:
```

Check out the documentation at:
* [`trace_custom_service`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_custom_service)


<a name="messaging"></a>
### Messaging

You can use the SDK to trace messages sent or received via a messaging system. When tracing messages,
we distinguish between:

* sending a message
* waiting for and receiving a message
* processing a received message

<a name="outgoing-messaging"></a>
#### Outgoing Messages

All messaging related tracers need a messaging system info object which you have to create prior
to the respective messaging tracer, which is an outgoing message tracer in the example below.

```python
msi_handle = sdk.create_messaging_system_info(
	'myMessagingSystem', 'requestQueue', MessagingDestinationType.QUEUE,
	ChannelType.TCP_IP, '10.11.12.13')

with msi_handle:
	with sdk.trace_outgoing_message(msi_handle) as tracer:
		# Get and set the Dynatrace tag.
		tag = tracer.outgoing_dynatrace_string_tag
		message_to_send.add_header_field(oneagent.sdk.DYNATRACE_MESSAGE_PROPERTY_NAME, tag)

		# Send the message.
		the_queue.send(message_to_send)

		# Optionally set message and/or correlation IDs
		tracer.set_vendor_message_id(message_to_send.get_message_id())
		tracer.set_correlation_id(message_to_send.get_correlation_id())
```

<a name="incoming-messaging"></a>
#### Incoming Messages

On the incoming side, we need to differentiate between the blocking receiving part and processing
the received message. Therefore two different tracers are being used:

* IncomingMessageReceiveTracer
* IncomingMessageProcessTracer

```python
msi_handle = sdk.create_messaging_system_info(
	'myMessagingSystem', 'requestQueue', MessagingDestinationType.QUEUE,
	ChannelType.TCP_IP, '10.11.12.13')

with msi_handle:
	# Create the receive tracer for incoming messages.
	with sdk.trace_incoming_message_receive(msi_handle):
		# This is a blocking call, which will return as soon as a message is available.
		Message query_message = the_queue.receive()

		# Get the Dynatrace tag from the message.
		tag = query_message.get_header_field(oneagent.sdk.DYNATRACE_MESSAGE_PROPERTY_NAME)

		# Create the tracer for processing incoming messages.
		tracer = sdk.trace_incoming_message_process(msi_handle, str_tag=tag)
		tracer.set_vendor_message_id(query_message.get_vendor_id())
		tracer.set_correlation_id(query_message.get_correlation_id())

		with tracer:
			# Now let's handle the message ...
			print('handle incoming message')
```

In case of non-blocking receive (e. g. using an event handler), there is no need to use an
IncomingMessageReceiveTracer - just trace processing of the message by using the IncomingMessageProcessTracer:

```python
msi_handle = sdk.create_messaging_system_info(
	'myMessagingSystem', 'requestQueue', MessagingDestinationType.QUEUE,
	ChannelType.TCP_IP, '10.11.12.13')

def on_message_received(message):
	# Get the Dynatrace tag from the message.
	tag = message.get_header_field(oneagent.sdk.DYNATRACE_MESSAGE_PROPERTY_NAME)

	# Create the tracer for processing incoming messages.
	tracer = sdk.trace_incoming_message_process(msi_handle, str_tag=tag)
	tracer.set_vendor_message_id(message.get_vendor_id())
	tracer.set_correlation_id(message.get_correlation_id())

	with tracer:
		# Now let's handle the message ...
		print('handle incoming message')
```

See the documentation for more information:

* [`create_messaging_system_info`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.create_messaging_system_info)
* [`trace_outgoing_message`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.trace_outgoing_message)
* [`trace_incoming_message_receive`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.trace_incoming_message_receive)
* [`trace_incoming_message_process`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.trace_incoming_message_process)
* [General information on tagging](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/tagging.html)


<a name="troubleshooting"></a>
## Troubleshooting

<a name="installation-issues"></a>
### Installation issues

* `ValueError` when installing, complaining about missing `DT_PYSDK_CSDK_PATH`.

  Make sure you are using pip to install a prebuilt package wheel for your system from PyPI, as described in [Using the OneAgent SDK for
  Python in your application](#installation). Also make sure you are using an up-to date version of `pip`, `setuptools` and `wheel`. You can
  try upgrading them with `python -m pip install --upgrade pip setuptools wheel` (make sure to use the same `python` that you use to install
  the `oneagent-sdk` package). ATTENTION: If you use the system-provided pip (e.g. installed via `apt-get` on Ubuntu) you should instead use
  a `pip` inside a `virtualenv` (the same as your project), as uprading system-provided packages via `pip` may cause issues.

  If this does not resolve the issue, make sure you are using a supported platform, as listed in [Requirements](#requirements). If you *are*
  using a supported system, you can try downloading the [OneAgent SDK for C/C++](https://github.com/Dynatrace/OneAgent-SDK-for-C) in the
  version corresponding to your OneAgent SDK for Python as listed in [the table in Requirements](#requirements). Then set the
  `DT_PYSDK_CSDK_PATH` environment variable to the `.so`/`.dll` file corresponding to your platform in the `lib` subdirectory of the C SDK
  and retry the installation (e.g. in a bash shell, use `export DT_PYSDK_CSDK_PATH=path/to/onesdk_shared.so`). If there is no corresponding
  directory, your platfom is not supported. Otherwise, regardless if it works with that method or not, please report an issue as desribed in
  [Let us help you](#let-us-help-you).


<a name="post-installation-issues"></a>
### Post-installation issues

To debug your OneAgent SDK for Python installation, execute the following Python code:

```python
import oneagent
oneagent.logger.setLevel(1)
init_result = oneagent.initialize(['loglevelsdk=finest', 'loglevel=finest'])
print('InitResult=' + repr(init_result))
```

If you get output containing `InitResult=InitResult(status=0, error=None)`, your installation should be fine. Otherwise, the output is helpful in
determining the issue. The [extended SKD state](#extended-sdk-state) might also help to diagnose your problem.

Known gotchas:

* `ImportError` or `ModuleNotFoundError` in line 1 that says that there is no module named `oneagent`.

  Make sure that the `pip install` or equivalent succeeded (see [here](#installation)). Also make sure you use the `pip` corresponding to your
  `python` (if in doubt, use `python -m pip` instead of `pip` for installing).


<a name="extended-sdk-state"></a>
### Extended SDK State

For debugging and/or diagnosing purposes you can also use the extended SDK state information.
```python
# The agent state is one of the integers in oneagent.sdk.AgentState.
print('Agent state:', oneagent.get_sdk().agent_state)

# The instance attribute 'agent_found' indicates whether an agent could be found or not.
print('Agent found:', oneagent.get_sdk().agent_found)

# If an agent was found but it is incompatible with this version of the SDK for Python
# then 'agent_is_compatible' would be set to false.
print('Agent is compatible:', oneagent.get_sdk().agent_is_compatible)

# The agent version is a string holding both the OneAgent version and the
# OneAgent SDK for C/C++ version separated by a '/'.
print('Agent version:', oneagent.get_sdk().agent_version_string)
```


<a name="repository-contents"></a>
## Repository contents

If you are viewing the [GitHub repository](https://github.com/Dynatrace/OneAgent-SDK-for-Python), you will see:

- `LICENSE`: License under which the whole SDK and sample applications are
  published.
- `src/`: Actual source code of the Python OneAgent SDK.
- `docs/`: Source files for the ([Sphinx](https://sphinx-doc.org)-based) HTML
  documentation. For the actual, readable documentation, see
  [here](#documentation).
- `tests/`, `test-util-src/`: Contains tests and test support files that are
  useful (only) for developers wanting to contribute to the SDK itself.
- `setup.py`, `setup.cfg`, `MANIFEST.in`, `project.toml`: Development files
  required for creating e.g. the PyPI package for the Python OneAgent SDK.
- `tox.ini`, `pylintrc`: Supporting files for developing the SDK itself. See
  <https://tox.readthedocs.io/en/latest/> and <https://www.pylint.org/>.

<a name="help--support"></a>
## Help & Support

The Dynatrace OneAgent SDK for Python is currently in beta status. The features are fully supported by Dynatrace.

<a name="documentation"></a>
<a name="read-the-manual"></a>
### Read the manual

* The most recent version of the documentation for the Python SDK can be viewed at
<https://dynatrace.github.io/OneAgent-SDK-for-Python/>.
* A high level documentation/description of OneAgent SDK concepts is available at
<https://github.com/Dynatrace/OneAgent-SDK/>.
* Of course, [this README](#) also contains lots of useful information.

<a name="let-us-help-you"></a>
### Let us help you

Make sure your issue is not already solved in the [available documentation](#documentation) before you ask for help. Especially the
[troubleshooting section in this README](#troubleshooting) may prove helpful.

**Get Help**
* Ask a question in the [product forums](https://answers.dynatrace.com/spaces/482/view.html).
* Read the <a href="https://www.dynatrace.com/support/help/" target="_blank">product documentation</a>

**Open a [GitHub issue](https://github.com/Dynatrace/OneAgent-SDK-for-Python/issues) to:**
  * Report minor defects or typos.
  * Ask for improvements or changes in the SDK API.
  * Ask any questions related to the community effort.

SLAs don't apply for GitHub tickets.

**Customers can open a ticket on the <a href="https://support.dynatrace.com/supportportal/" target="_blank">Dynatrace support portal</a> to:**
* Get support from the Dynatrace technical support engineering team
* Manage and resolve product related technical issues

SLAs apply according to the customer's support level.


<a name="release-notes"></a>
## Release notes

Please see the [GitHub releases page](https://github.com/Dynatrace/OneAgent-SDK-for-Python/releases),
and the [PyPI release history](https://pypi.org/project/oneagent-sdk/#history).


<a name="license"></a>
## License

See the LICENSE file for details. It should be included in your distribution.
Otherwise, see the most recent version on
[GitHub](https://github.com/Dynatrace/OneAgent-SDK-for-Python/blob/master/LICENSE).

Summary: This software is licensed under the terms of the Apache License Version
2.0 and comes bundled with the [six library by Benjamin
Peterson](http://six.readthedocs.io/), which is licensed under the terms of the
MIT license.

<!-- vim: set tw=140 linebreak: -->
