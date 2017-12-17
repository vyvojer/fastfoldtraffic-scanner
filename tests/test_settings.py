from unittest import TestCase

from scanner import settings


class SettingsTest(TestCase):

    def test_settings(self):
        self.assertEqual(settings.SCANNER_NAME, 'LOCAL_SCANNER')
        self.assertEqual(settings.PAPERTRAIL_PORT, 12590)