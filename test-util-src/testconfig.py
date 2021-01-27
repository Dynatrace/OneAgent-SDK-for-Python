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

from __future__ import print_function

import logging

import pytest
from oneagent import logger
from oneagent import sdk as onesdk
import sdkmockiface

@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logger.setLevel(logging.DEBUG)

@pytest.fixture
def native_sdk_noinit():
    nsdk = sdkmockiface.SDKMockInterface()
    yield nsdk
    for i, root in enumerate(nsdk.finished_paths):
        itag = root.in_tag_as_id
        if itag is not None and nsdk.get_finished_node_by_id(itag):
            rootstr = str(root) + ' linked under ' + str(root.linked_parent)
        else:
            rootstr = root.dump()
        print('root#{:2}: {}'.format(i, rootstr))

@pytest.fixture
def native_sdk(native_sdk_noinit):
    native_sdk_noinit.initialize()
    yield native_sdk_noinit



@pytest.fixture
def sdk(native_sdk):
    return onesdk.SDK(native_sdk)
