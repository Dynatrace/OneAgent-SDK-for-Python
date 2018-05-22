**Disclaimer: This SDK is currently still work in progress.
Using the OneAgent SDK for Python is COMPLETELY UNSUPPORTED at this stage!**

> Read the latest version of this README, with working internal links, at
[GitHub](https://github.com/Dynatrace/OneAgent-SDK-for-Python#readme).

# Dynatrace OneAgent SDK for Python

This SDK enables Dynatrace customers to extend request level visibility into
Python applications. It provides the Python implementation of the [Dynatrace OneAgent
SDK](https://github.com/Dynatrace/OneAgent-SDK).

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
- [Troubleshooting](#troubleshooting)
- [Repository contents](#repository-contents)
- [Help & Support](#help--support)
  * [Read the manual](#read-the-manual)
  * [Let us help you](#let-us-help-you)
- [Release notes](#release-notes)
- [License](#license)

<!-- tocstop -->

<a name="requirements"></a>
## Requirements

The SDK supports Python 2 ≥ 2.7 and Python 3 ≥ 3.4. Only the official CPython
(that is, the "normal" Python, i.e. the Python implementation from
<https://python.org>) is supported.

The Dynatrace OneAgent SDK for Python includes the [Dynatrace OneAgent SDK for
C/C++](https://github.com/Dynatrace/OneAgent-SDK-for-C). See
[here](https://github.com/Dynatrace/OneAgent-SDK-for-C#dynatrace-oneagent-sdk-for-cc-requirements)
for its requirements, which also apply to the SDK for Python.

The version of the SDK for C/C++ that is included in each version of the SDK for
Python is shown in the following table. The SDK for C/C++'s requirement for the
Dynatrace OneAgent is also shown here, for your convenience (it is the same that
is [listed in the OneAgent SDK for C/C++'s
documentation](https://github.com/Dynatrace/OneAgent-SDK-for-C/blob/master/README.md#compatibility-of-dynatrace-oneagent-sdk-for-cc-releases-with-oneagent-releases)).

|OneAgent SDK for Python|OneAgent SDK for C/C++|Dynatrace OneAgent|
|:----------------------|:---------------------|:-----------------|
|1.0                    |1.1.0                 |≥1.141            |

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
python -c "import oneagent; print(oneagent.try_init())"
```

If everything worked, you should get some output ending with
`InitResult(status=0, error=None)`. Otherwise, see
[Troubleshooting](#troubleshooting).

You then need to load the SDK into the application and add code that traces your
application using the SDK. For a quick “Hello World” that should give you a Path
in the Dynatrace UI, try this:

```python
import oneagent
from oneagent.sdk import SDK

if not oneagent.try_init():
    print('Error initializing OneAgent SDK.')

with SDK.get().trace_incoming_remote_call('method', 'service', 'endpoint'):
    pass

print('It may take a few moments before the path appears in the UI.')
input('Please wait...')
oneagent.shutdown()
```

For this, follow the [provided sample
application](https://github.com/Dynatrace/OneAgent-SDK-for-Python/blob/master/samples/basic-sdk-sample/basic_sdk_sample.py)
(see also Quickstart section in the
[documentation](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/quickstart.html)).


<a name="api-concepts"></a>
## API Concepts

<a name="initialization-and-sdk-objects"></a>
### Initialization and SDK objects

Before first using any other SDK functions, you should initialize the SDK.

```python
init_result = oneagent.try_init()
print('OneAgent SDK initialization result' + repr(init_result))
if init_result:
    print('SDK should work (but agent might be inactive).')
if not init_result:
    print('SDK will definitely not work (i.e. functions will be no-ops).')
```

See the documentation for the [`try_init`
function](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.try_init)
and the [`InitResult`
class](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.InitResult)
for more information.

To then use the SDK, get a reference to the
[`SDK`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK)
singleton by calling its static
[`get`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.get)
static method. The first thing you may want to do with this object, is checking
if the agent is active by comparing the value of the
[`agent_state`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.agent_state)
property to the
[`oneagent.common.AgentState`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.common.AgentState)
constants.

```python
import oneagent.sdk
from oneagent.common import AgentState
# Initialize oneagent, as above

sdk = oneagent.sdk.SDK.get()
if sdk.agent_state not in (AgentState.ACTIVE,
        AgentState.TEMPORARILY_INACTIVE):
    print('Too bad, you will not see data from this process.')
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
explicit methods for starting, ending and attaching error information too; see
the
[documentation](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.Tracer)).

There are different tracer types requiring different information for creation.
As an example, to trace an incoming remote call, this would be the most simple
way to trace it:

```python
from oneagent.sdk import SDK

with SDK.get().trace_incoming_remote_call('method', 'service', 'endpoint'):
    pass # Here you would do the actual work that is timed
```

See the section on [remote calls](#remote-calls) for more information.

Some tracers also support attaching additional information before ending it.

**Important:** In Python 2, tracers accept both byte (“normal”) and unicode
strings. Byte strings must always use the UTF-8 encoding!


<a name="features-and-how-to-use-them"></a>
## Features and how to use them

<a name="remote-calls"></a>
### Remote calls

You can use the SDK to trace communication from one process to another. This
will enable you to see full Service Flow, PurePath and Smartscape topology for
remoting technologies that Dynatrace is not aware of.

To trace any kind of remote call you first need to create a Tracer. The Tracer
object represents the endpoint that you want to call, thus you need to supply
the name of the remote service and method. In addition, you need to transport
a tag in your remote call from the client side to the server side if you want
to trace it end to end.

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
* [General information on
  tagging](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/tagging.html)

<a name="sql-database-requests"></a>
### SQL database requests

To trace database requests you need a database info object which stores the
information about your database which does not change between individual
requests. This will typically be created somewhere in your initialization code
(after initializing the SDK):

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

Note that you need to release the database info object. You can do this by
calling `close()` on it or using it in a `with` block.

See the documentation for more information:

* [`create_database_info`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.create_database_info)
* [`trace_sql_database_request`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_sql_database_request)
* [`DatabaseRequestTracer`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.DatabaseRequestTracer)

<a name="incoming-web-requests"></a>
### Incoming web requests

[Like for database infos](#sql-database-requests), to trace incoming web
requests you need a web application info object which stores the information
about your web application which does not change:

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

Note that you need to release the web application info object. You can do this
by calling `close()` on it or using it in a `with` block.

Incoming web request tracers support some more features not shown here. Be sure
to check out the documentation:

* [`create_web_application_info`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.create_web_application_info)
* [`trace_incoming_web_request`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.SDK.trace_incoming_web_request)
* [`IncomingWebRequestTracer`](https://dynatrace.github.io/OneAgent-SDK-for-Python/docs/sdkref.html#oneagent.sdk.tracers.IncomingWebRequestTracer)

There is currently no explicit support for tracing outgoing web requests. You
can use an [outgoing remote call tracer](#remote-calls) instead.

<a name="troubleshooting"></a>
## Troubleshooting

To debug your OneAgent SDK for Python  installation, execute the following
Python code:

```python
import oneagent
oneagent.logger.setLevel(0)
init_result = oneagent.try_init(['loglevelsdk=finest', 'loglevel=finest'])
print('InitResult=' + repr(init_result))
```

If you get output containing `InitResult=InitResult(status=0, error=None)`, your
installation should be fine.

Otherwise, hopefully the output is helpful in determining the issue.

Known gotchas:

* `ImportError` or `ModuleNotFoundError` in line 1 that says that there is no
  module named `oneagent`.

  Make sure that the `pip install` or equivalent succeeded (see
  [here](#installation)). Also make sure you use the `pip` corresponding to your
  `python` (if in doubt, use `python -m pip` instead of `pip` for installing).

<a name="repository-contents"></a>
## Repository contents

If you are viewing the [GitHub
repository](https://github.com/Dynatrace/OneAgent-SDK-for-Python), you will see:

- `LICENSE`: License under which the whole SDK and sample applications are
  published.
- `src/`: Actual source code of the Python OneAgent SDK.
- `docs/`: Source files for the ([Sphinx](https://sphinx-doc.org)-based) HTML
  documentation. For the actual, readable documentation, see
  [here](#documentation).
- `tests/`, `test-util-src/`: Contains tests and test support files that are
  useful (only) for developers wanting contribute to the SDK itself.
- `setup.py`, `setup.cfg`, `MANIFEST.in`, `project.toml`: Development files
  required for creating e.g. the PyPI package for the Python OneAgent SDK.
- `tox.ini`, `pylintrc`: Supporting files for developing the SDK itself. See
  <https://tox.readthedocs.io/en/latest/> and <https://www.pylint.org/>.

<a name="help--support"></a>
## Help & Support

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

Make sure your issue is not already solved in the [available
documentation](#documenation) before you ask for help. Especially the
[troubleshooting section in this README](#troubleshooting) may prove helpful.


* Ask a question in the [product
  forums](https://answers.dynatrace.com/spaces/482/view.html).
* Open a [GitHub
  issue](https://github.com/Dynatrace/OneAgent-SDK-for-Python/issues) to:
  * Report minor defects or typos.
  * Ask for improvements or changes in the SDK API.
  * Ask any questions related to the community effort.

  SLAs don't apply for GitHub tickets.

<a name="release-notes"></a>
## Release notes

Please see the [GitHub
releases page](https://github.com/Dynatrace/OneAgent-SDK-for-Python/releases),
and the [PyPI release
history](https://pypi.org/project/oneagent-sdk/#history).

<a name="license"></a>
## License

See the LICENSE file for details. It should be included in your distribution.
Otherwise, see the most recent version on
[GitHub](https://github.com/Dynatrace/OneAgent-SDK-for-Python/blob/master/LICENSE).

Summary: This software is licensed under the terms of the Apache License Version
2.0 and comes bundled with the [six library by Benjamin
Peterson](http://six.readthedocs.io/), which is licensed under the terms of the
MIT license.
