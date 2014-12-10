import unittest
import redi.input


class EpicExportReader(unittest.TestCase):

    def test_read(self):
        csv = """
"result","loinc_component","loinc_code","low","high","units","date_time_stamp","study_id"
3.813,"Leukocytes","26464-8",3.8,10.8,"10*3/uL",2112-10-27,1
3.433,"Neutrophils","26499-4",1.5,7.8,"10*3/uL",2112-10-27,1
"""

        reader = redi.input.EpicExportReader()
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual(2, len(data))
        self.assertEqual("26464-8", data[0].component.loinc_code)
        self.assertEqual(3.433, data[1].result)
        self.assertEqual("10*3/uL", data[1].units)

    def test_read_custom_headers(self):
        csv = """
"test_results","loinc_desc","code_of_loinc","low","high","units_used","date_time_stamp","study_id"
3.813,"Leukocytes","26464-8",3.8,10.8,"10*3/uL",2112-10-27,1
3.433,"Neutrophils","26499-4",1.5,7.8,"10*3/uL",2112-10-27,1
"""

        reader = redi.input.EpicExportReader({
            'loinc_code': 'code_of_loinc',
            'loinc_component': 'loinc_desc',
            'result': 'test_results',
            'units': 'units_used',
            })
        data = reader.read(csv.strip().split('\n'))

        self.assertEqual(2, len(data))
        self.assertEqual("26464-8", data[0].component.loinc_code)
        self.assertEqual(3.433, data[1].result)
        self.assertEqual("10*3/uL", data[1].units)


if __name__ == '__main__':
    unittest.main()
