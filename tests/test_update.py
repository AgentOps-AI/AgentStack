import os
import unittest
from agentstack.update import should_update


class UpdateTest(unittest.TestCase):
    def test_updates_disabled_by_env_var_in_test(self):
        assert 'AGENTSTACK_UPDATE_DISABLE' in os.environ
        assert not should_update()
