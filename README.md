**Disclaimer: This SDK is currently in early access and still work in
progress.**


# Dynatrace OneAgent SDK for Python

This SDK enables Dynatrace customers to extend request level visibility into
Python applications.

It provides the Python implementation of the [Dynatrace OneAgent
SDK](https://github.com/Dynatrace/OneAgent-SDK). 


## Package contents

- `LICENSE`: License under which the whole SDK and sample applications are
  published.
- `src/`: Actual source code of the Python OneAgent SDK.
- `docs/`: Source files for the ([Sphinx](https://sphinx-doc.org)-based) HTML
  documentation. For the actual, readable documentation, see
  [here](#documenation).
- `tests/`: Contains tests that are useful (only) for developers wanting
  contribute to the SDK itself.
- `setup.py`, `setup.cfg`, `MANIFEST.in`: Development Files required for
  creating e.g. the PyPI package for the Python OneAgent SDK.
- `tox.ini`, `pylintrc`: Supporting files for developing the SDK itself. See
  <https://tox.readthedocs.io/en/latest/> and <https://www.pylint.org/>.


## Features

Dynatrace OneAgent SDK for Python currently implements support for the following
features (corresponding to features specified in [Dynatrace OneAgent
SDK](https://github.com/Dynatrace/OneAgent-SDK)):

- Outgoing and incoming remote calls
- SQL Database requests
- Incoming web requests


## Documentation

The reference documentation is included in this package. The most recent version
is also available online at <https://dynatrace.github.io/OneAgent-SDK-for-Python/>

A high level documentation/description of OneAgent SDK concepts is available at
<https://github.com/Dynatrace/OneAgent-SDK/>.
