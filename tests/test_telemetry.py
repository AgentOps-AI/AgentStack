import os
import unittest
from agentstack.utils import get_telemetry_opt_out


class TelemetryTest(unittest.TestCase):
    def test_telemetry_opt_out_env_var_set(self):
        AGENTSTACK_TELEMETRY_OPT_OUT = os.getenv("AGENTSTACK_TELEMETRY_OPT_OUT")
        assert AGENTSTACK_TELEMETRY_OPT_OUT

    def test_telemetry_opt_out_set_in_test_environment(self):
        assert get_telemetry_opt_out()
