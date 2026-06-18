from __future__ import annotations

import unittest

from app.utils.stealth import USER_AGENTS, VIEWPORTS, _stealth_for_user_agent


class StealthTest(unittest.TestCase):
    def test_user_agent_pool_has_ten_entries(self) -> None:
        self.assertEqual(len(USER_AGENTS), 10)

    def test_viewports_match_desktop_sizes(self) -> None:
        self.assertEqual(
            VIEWPORTS,
            [
                {"width": 1366, "height": 768},
                {"width": 1440, "height": 900},
                {"width": 1920, "height": 1080},
            ],
        )

    def test_every_user_agent_can_build_stealth_config(self) -> None:
        for user_agent in USER_AGENTS:
            stealth = _stealth_for_user_agent(user_agent)
            self.assertGreaterEqual(len(list(stealth.enabled_scripts)), 1)


if __name__ == "__main__":
    unittest.main()
