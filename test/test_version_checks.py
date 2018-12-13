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

import pytest

from oneagent._impl.native.sdkversion import OnesdkStubVersion

def _check_helper(version, higher_version, equal_version):
    assert version < higher_version
    assert not higher_version < version
    assert version <= higher_version
    assert not higher_version <= version
    assert higher_version > version
    assert not version > higher_version
    assert not version == higher_version
    assert version <= equal_version
    assert version >= equal_version
    assert version == equal_version
    assert version != higher_version
    assert higher_version != equal_version
    assert not version != equal_version

def test_version_major():
    version1 = OnesdkStubVersion(1, 4, 0)
    version2 = OnesdkStubVersion(2, 2, 0)
    version3 = OnesdkStubVersion(1, 4, 0)
    _check_helper(version1, version2, version3)

def test_version_minor():
    version1 = OnesdkStubVersion(2, 2, 4)
    version2 = OnesdkStubVersion(2, 3, 1)
    version3 = OnesdkStubVersion(2, 2, 4)
    _check_helper(version1, version2, version3)

def test_version_patch():
    version1 = OnesdkStubVersion(2, 2, 1)
    version2 = OnesdkStubVersion(2, 2, 4)
    version3 = OnesdkStubVersion(2, 2, 1)
    _check_helper(version1, version2, version3)

def test_none_instance():
    version = OnesdkStubVersion(2, 2, 1)
    assert not version is None
    with pytest.raises(TypeError):
        assert version > None
    with pytest.raises(TypeError):
        assert version < None
    with pytest.raises(TypeError):
        assert version >= None
    with pytest.raises(TypeError):
        assert version <= None

def test_wrong_instance():
    version = OnesdkStubVersion(2, 2, 1)
    with pytest.raises(TypeError):
        assert not version == '2.2.1'   #pylint:disable=unneeded-not
    assert str(version) == '2.2.1'
    with pytest.raises(TypeError):
        assert version > 'huhu'
    with pytest.raises(TypeError):
        assert version < 'huhu'
    with pytest.raises(TypeError):
        assert version >= 'huhu'
    with pytest.raises(TypeError):
        assert version <= 'huhu'
