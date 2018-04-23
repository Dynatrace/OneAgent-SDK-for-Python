from __future__ import print_function

import logging

import pytest
from oneagent import logger
from oneagent import sdk as onesdk
from oneagent._impl.native import sdkmockiface

@pytest.fixture(scope='session', autouse=True)
def setup_logging():
    logger.setLevel(logging.DEBUG)

@pytest.fixture
def native_sdk():
    nsdk = sdkmockiface.SDKMockInterface()
    nsdk.initialize()
    yield nsdk
    for i, root in enumerate(nsdk.finished_paths):
        itag = root.in_tag_as_id
        if itag is not None and nsdk.get_finished_node_by_id(itag):
            rootstr = str(root) + ' linked under ' + str(root.linked_parent)
        else:
            rootstr = root.dump()
        print('root#{:2}: {}'.format(i, rootstr))


@pytest.fixture
def sdk(native_sdk):
    return onesdk.SDK(native_sdk)
