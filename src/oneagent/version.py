#
# Copyright 2019 Dynatrace LLC
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

'''Version defines related to the OneAgent SDK for Python.
'''

from oneagent._impl.native.sdkversion import OnesdkStubVersion

# That's the OneAgent SDK for Python version.
# See https://www.python.org/dev/peps/pep-0440/ "Version Identification and
# Dependency Specification"
__version__ = '1.5.1'

# Define the OneAgent SDK for C/C++ version which should be shipped with this
# Python SDK version.
shipped_c_stub_version = '1.7.1'

# Below are the minimum and maximum required/supported OneAgent SDK for C/C++ versions.
min_stub_version = OnesdkStubVersion(1, 7, 1)
max_stub_version = OnesdkStubVersion(2, 0, 0)
