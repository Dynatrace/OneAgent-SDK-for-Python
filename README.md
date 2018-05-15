**Disclaimer: This SDK is currently still work in progress.
Using the OneAgent SDK for Python is COMPLETELY UNSUPPORTED at this stage!**

# Dynatrace OneAgent SDK for Python

This SDK enables Dynatrace customers to extend request level visibility into
Python applications. It provides the Python implementation of the [Dynatrace OneAgent
SDK](https://github.com/Dynatrace/OneAgent-SDK).

## Features

The Dynatrace OneAgent SDK for Python currently supports the following features
(corresponding to features specified in [Dynatrace OneAgent
SDK](https://github.com/Dynatrace/OneAgent-SDK)):

- Outgoing and incoming remote calls
- SQL Database requests
- Incoming web requests

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
|0.1                    |1.1.0                 |≥1.141            |

## Using the OneAgent SDK for Python in your application

<a id="installation"></a>


Just do `python -m pip install --upgrade oneagent-sdk`, to install the latest
version of the OneAgent SDK for Python.

To verify your installation, execute

```bash
python -c "import oneagent; print(oneagent.try_init())"
```

If everything worked, you should get some output ending with
`InitResult(status=0, error=None)`. Otherwise, see
[Troubleshooting](#troubleshooting).

The output should end with `InitResult(status=0, error=None)`.

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

For this, follow the [tests/onesdksamplepy.py](test/onesdksamplepy.py) example
(see also the
[documentation](https://dynatrace.github.io/OneAgent-SDK-for-Python/quickstart.html)).

## Documentation

The most recent version of the documentation can be viewed at
<https://dynatrace.github.io/OneAgent-SDK-for-Python/>.

A high level documentation/description of OneAgent SDK concepts is available at
<https://github.com/Dynatrace/OneAgent-SDK/>.

## Troubleshooting

To debug your OneSDK installation, execute the following Python code:

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

## Repository contents

If you are viewing the [GitHub
repository](https://github.com/Dynatrace/OneAgent-SDK-for-Python), you will see:

- `LICENSE`: License under which the whole SDK and sample applications are
  published.
- `src/`: Actual source code of the Python OneAgent SDK.
- `docs/`: Source files for the ([Sphinx](https://sphinx-doc.org)-based) HTML
  documentation. For the actual, readable documentation, see
  [here](#documenation).
- `tests/`, `test-util-src/`: Contains tests and test support files that are
  useful (only) for developers wanting contribute to the SDK itself.
- `setup.py`, `setup.cfg`, `MANIFEST.in`, `project.toml`: Development files
  required for creating e.g. the PyPI package for the Python OneAgent SDK.
- `tox.ini`, `pylintrc`: Supporting files for developing the SDK itself. See
  <https://tox.readthedocs.io/en/latest/> and <https://www.pylint.org/>.
