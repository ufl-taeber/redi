import io
import unittest

from redi import settings


class SettingsParserTests(unittest.TestCase):
    def test_require_setting(self):
        parser = settings.SettingsParser()
        parser.add_setting('redcap_uri', required=True)

        sample_config = """redcap_uri = http://example.org"""

        config = parser.parse(io.BytesIO(sample_config))

        self.assertEqual("http://example.org", config['redcap_uri'])

    def test_required_setting_missing(self):
        parser = settings.SettingsParser()
        parser.add_setting('redcap_uri', required=True)

        sample_config = ""

        self.assertRaises(settings.MissingRequiredSettingError,
                          parser.parse, io.BytesIO(sample_config))

    def test_numeric_setting(self):
        parser = settings.SettingsParser()
        parser.add_setting('smtp_port_for_outbound_mail', default=25, type=int)

        sample_config = """smtp_port_for_outbound_mail=993"""

        config = parser.parse(io.BytesIO(sample_config))

        self.assertEqual(993, config['smtp_port_for_outbound_mail'])

    def test_wrong_type(self):
        parser = settings.SettingsParser()
        parser.add_setting('smtp_port_for_outbound_mail', default=25, type=int)

        sample_config = """smtp_port_for_outbound_mail= PORT_NUMBER"""

        self.assertRaises(settings.TypeError,
                          parser.parse, io.BytesIO(sample_config))


if __name__ == '__main__':
    unittest.main()