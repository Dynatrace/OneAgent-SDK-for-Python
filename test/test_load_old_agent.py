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

import os

import oneagent
from oneagent import InitResult
from oneagent.common import AgentState

def test_load_old_agent():
    saved_path = os.environ.get('DT_AGENTLIBRARY', '')
    try:
        os.environ['DT_AGENTLIBRARY'] = os.environ.get('DT_OLDAGENTLIBRARY', '')
        assert os.environ['DT_AGENTLIBRARY'] is not None
        assert os.environ['DT_AGENTLIBRARY'] != ''

        sdk_options = oneagent.sdkopts_from_commandline(remove=True)
        init_result = oneagent.initialize(sdk_options)
        assert init_result.error is not None
        assert init_result.status == InitResult.STATUS_INIT_ERROR

        sdk = oneagent.get_sdk()

        assert sdk.agent_state == AgentState.NOT_INITIALIZED
        assert sdk.agent_found
        assert not sdk.agent_is_compatible
        assert sdk.agent_version_string == '1.141.112.20180322-095721/1.3.1'
    finally:
        oneagent.shutdown()
        os.environ['DT_AGENTLIBRARY'] = saved_path
