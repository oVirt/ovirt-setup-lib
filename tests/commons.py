#
# ovirt-setup-lib -- ovirt setup library
# Copyright (C) 2015 Red Hat, Inc.
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
#


import mock
import unittest


class BaseTestCase(unittest.TestCase):

    _patchers = {}

    def mock_base(self):
        if 'Base' not in self._patchers:
            self._patchers['Base'] = 'otopi.base.Base'

    def mock_plugin(self):
        import otopi.plugin  # imported here to make mock happy
        assert otopi.plugin  # assertion here to make pyflakes happy
        if 'Plugin' not in self._patchers:
            self.mock_base()
            self._patchers['Plugin'] = 'otopi.plugin.PluginBase'

    def mock_context(self):
        import otopi.context  # imported here to make mock happy
        assert otopi.context  # assertion here to make pyflakes happy
        if 'Context' not in self._patchers:
            self.mock_base()
            self._patchers['Context'] = 'otopi.context.Context'

    def mock_otopi(self):
        self.mock_plugin()
        self.mock_context()

    def apply_patch(self):
        for cls_name in self._patchers:
            patcher = mock.patch(self._patchers[cls_name])
            setattr(self, cls_name, patcher.start())
            self.addCleanup(patcher.stop)
