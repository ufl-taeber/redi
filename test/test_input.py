import io
import time
import unittest

import redi.input


class ClinicalComponentsTests(unittest.TestCase):
    def test_from_csv(self):
        config = """
loinc_code, loinc_component, type, has_units,
26464-8, Leukocytes,,,
"26499-4","Neutrophils",,,
"""
        cc = redi.input.ClinicalComponents.from_csv(config.strip().split('\n'))

        self.assertIsNotNone(cc['26464-8'])
        self.assertIsNotNone(cc['26499-4'])
        self.assertTrue(cc['26499-4'].has_units)


class CsvReaderTests(unittest.TestCase):

    def test_read(self):
        csv = """
"result","loinc_component","loinc_code","low","high","units","date_time_stamp","study_id"
3.813,"Leukocytes","26464-8",3.8,10.8,"10*3/uL",2112-10-27,1
3.433,"Neutrophils","26499-4",1.5,7.8,"10*3/uL",2112-10-27,1
"""
        cc = redi.input.ClinicalComponents({
            '26464-8': redi.input.ClinicalComponent('Leukocytes', '26464-8'),
            '26499-4': redi.input.ClinicalComponent('Neutrophils', '26599-4'),
        })

        reader = redi.input.CsvReader(cc)
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual(2, len(data))
        self.assertEqual("26464-8", data[0].component.loinc_code)
        self.assertEqual(3.433, float(data[1].result.value))
        self.assertEqual("10*3/uL", data[1].units)

    def test_read_custom_headers(self):
        csv = """
"test_results","loinc_desc","code_of_loinc","low","high","units_used","date_time_stamp","study_id"
3.813,"Leukocytes","26464-8",3.8,10.8,"10*3/uL",2112-10-27,1
3.433,"Neutrophils","26499-4",1.5,7.8,"10*3/uL",2112-10-27,1
"""
        cc = redi.input.ClinicalComponents({
            '26464-8': redi.input.ClinicalComponent('Leukocytes', '26464-8'),
            '26499-4': redi.input.ClinicalComponent('Neutrophils', '26599-4'),
        })

        reader = redi.input.CsvReader(cc, {
            'loinc_code': 'code_of_loinc',
            'loinc_component': 'loinc_desc',
            'result': 'test_results',
            'units': 'units_used',
            })
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual(2, len(data))
        self.assertEqual("26464-8", data[0].component.loinc_code)
        self.assertEqual(3.433, float(data[1].result.value))
        self.assertEqual("10*3/uL", data[1].units)

    def test_read_expected_non_numeric_units(self):
        csv = """
"result","loinc_component","loinc_code","low","high","units","date_time_stamp","study_id"
Yes,"Are you happy?","12345-0",,,,2112-10-27,1
"Doe, John","Name","12345-1",,,,2112-10-27,1
"""

        cc = redi.input.ClinicalComponents({
            '12345-0': redi.input.ClinicalComponent('Are you happy?', '12345-0',
                                                    type='boolean',
                                                    has_units=False),
            '12345-1': redi.input.ClinicalComponent('Name', '12345-1', type=str,
                                                    has_units=False)
        })

        reader = redi.input.CsvReader(cc)
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual(2, len(data))
        self.assertEqual(True, data[0].result.value)
        self.assertEqual("Doe, John", data[1].result.value)

    def test_read_date(self):
        csv = """
"result","loinc_component","loinc_code","low","high","units","date_time_stamp","study_id"
0.1,"LOINCNESS Monster","1",low,high,units,2112-10-27,1
        """

        cc = redi.input.ClinicalComponents({
            '1': redi.input.ClinicalComponent('Are you happy?', '1')
        })

        reader = redi.input.CsvReader(cc, timestamp_format='%Y-%m-%d')
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual('10/27/2112', time.strftime('%m/%d/%Y', data[0].timestamp))

    def test_read_xml(self):
        xml = """<?xml version="1.0" encoding="utf8"?>
            <study>
                <subject>
                    <result>3.813</result>
                    <loinc_component>Leukocytes</loinc_component>
                    <loinc_code>26464-8</loinc_code>
                    <low>3.8</low>
                    <high>10.8</high>
                    <units>10*3/uL</units>
                    <date_time_stamp>2112-10-27</date_time_stamp>
                    <study_id>1</study_id>
                </subject>
                <subject>
                    <result>3.433</result>
                    <loinc_component>Neutrophils</loinc_component>
                    <loinc_code>26499-4</loinc_code>
                    <low>1.5</low>
                    <high>7.8</high>
                    <units>10*3/uL</units>
                    <date_time_stamp>2112-10-27</date_time_stamp>
                    <study_id>1</study_id>
                </subject>
            </study>"""

        cc = redi.input.ClinicalComponents({
            '26464-8': redi.input.ClinicalComponent('Leukocytes', '26464-8'),
            '26499-4': redi.input.ClinicalComponent('Neutrophils', '26599-4'),
        })

        reader = redi.input.FlatXmlReader(cc)
        data = reader.read(io.BytesIO(xml))

        self.assertEqual(2, len(data))
        self.assertEqual("26464-8", data[0].component.loinc_code)
        self.assertEqual(3.433, float(data[1].result.value))
        self.assertEqual("10*3/uL", data[1].units)
        self.assertEqual(2, len(filter(lambda r: r.subject == '1', data)))
        self.assertEqual(1, len(filter(lambda r: r.result.verbatim == '3.813', data)))


if __name__ == '__main__':
    unittest.main()
