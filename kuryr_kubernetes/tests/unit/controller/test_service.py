# Copyright (c) 2016 Mirantis, Inc.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import mock

from kuryr_kubernetes.controller import service
from kuryr_kubernetes.tests import base as test_base


class TestControllerService(test_base.TestCase):

    @mock.patch('oslo_service.service.launch')
    @mock.patch('kuryr_kubernetes.config.init')
    @mock.patch('kuryr_kubernetes.config.setup_logging')
    @mock.patch('kuryr_kubernetes.clients.setup_clients')
    @mock.patch('kuryr_kubernetes.controller.service.KuryrK8sService')
    def test_start(self, m_svc, m_setup_clients, m_setup_logging,
                   m_config_init, m_oslo_launch):
        m_launcher = mock.Mock()
        m_oslo_launch.return_value = m_launcher

        service.start()

        m_config_init.assert_called()
        m_setup_logging.assert_called()
        m_setup_clients.assert_called()
        m_svc.assert_called()
        m_oslo_launch.assert_called()
        m_launcher.wait.assert_called()
