import unittest
import tempfile
import os
from lxml import etree
from mock import patch
import redi
from utils import redi_email
from utils.redcapClient import RedcapClient
import utils.SimpleConfigParser as SimpleConfigParser
from requests import RequestException

file_dir = os.path.dirname(os.path.realpath(__file__))
goal_dir = os.path.join(file_dir, "../")
proj_root = os.path.abspath(goal_dir)+'/'

DEFAULT_DATA_DIRECTORY = os.getcwd()

class TestResearchIdToRedcapId(unittest.TestCase):

    def setUp(self):
        self.sortedData = """
    <study>
    <subject>
        <NAME>HEMOGLOBIN</NAME>
        <loinc_code>1534435</loinc_code>
        <RESULT>10.5</RESULT>
        <REFERENCE_LOW>12.0</REFERENCE_LOW>
        <REFERENCE_HIGH>16.0</REFERENCE_HIGH>
        <REFERENCE_UNIT>g/dL</REFERENCE_UNIT>
        <DATE_TIME_STAMP/>
        <STUDY_ID>999-0059</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>hemo_lborres</redcapFieldNameValue><redcapFieldNameUnits>hemo_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>hemo_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>WBC</NAME>
        <loinc_code>999</loinc_code>
        <RESULT>5.4</RESULT>
        <REFERENCE_LOW/>
        <REFERENCE_HIGH/>
        <REFERENCE_UNIT/>
        <DATE_TIME_STAMP/>
        <STUDY_ID>999-0059</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>wbc_lborres</redcapFieldNameValue><redcapFieldNameUnits>wbc_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>wbc_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>PLATELET COUNT</NAME>
        <loinc_code>1009</loinc_code>
        <RESULT>92</RESULT>
        <REFERENCE_LOW/>
        <REFERENCE_HIGH/>
        <REFERENCE_UNIT/>
        <DATE_TIME_STAMP/>
        <STUDY_ID>999-0059</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>plat_lborres</redcapFieldNameValue><redcapFieldNameUnits>plat_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>plat_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>HEMOGLOBIN</NAME>
        <loinc_code>1534435</loinc_code>
        <RESULT>9.5</RESULT>
        <REFERENCE_LOW>12.0</REFERENCE_LOW>
        <REFERENCE_HIGH>16.0</REFERENCE_HIGH>
        <REFERENCE_UNIT>g/dL</REFERENCE_UNIT>
        <DATE_TIME_STAMP/>
        <STUDY_ID>999-0059</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>hemo_lborres</redcapFieldNameValue><redcapFieldNameUnits>hemo_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>hemo_lbstat</redcapFieldNameStatus></subject>
    </study>"""

        self.data = etree.ElementTree(etree.fromstring(self.sortedData))
        self.serverResponse = """<records>
    <item><dm_subjid><![CDATA[3]]></dm_subjid><redcap_event_name><![CDATA[1_arm_1]]></redcap_event_name><dm_usubjid><![CDATA[999-0001]]></dm_usubjid></item>
<item><dm_subjid><![CDATA[76]]></dm_subjid><redcap_event_name><![CDATA[1_arm_1]]></redcap_event_name><dm_usubjid><![CDATA[999-0059]]></dm_usubjid></item>
<item><dm_subjid><![CDATA[5]]></dm_subjid><redcap_event_name><![CDATA[1_arm_1]]></redcap_event_name><dm_usubjid><![CDATA[001-0005]]></dm_usubjid></item></records>"""


        self.output = """<study>
    <subject>
        <NAME>HEMOGLOBIN</NAME>
        <loinc_code>1534435</loinc_code>
        <RESULT>10.5</RESULT>
        <REFERENCE_LOW>12.0</REFERENCE_LOW>
        <REFERENCE_HIGH>16.0</REFERENCE_HIGH>
        <REFERENCE_UNIT>g/dL</REFERENCE_UNIT>
        <DATE_TIME_STAMP/>
        <STUDY_ID>1</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>hemo_lborres</redcapFieldNameValue><redcapFieldNameUnits>hemo_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>hemo_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>WBC</NAME>
        <loinc_code>999</loinc_code>
        <RESULT>5.4</RESULT>
        <REFERENCE_LOW/>
        <REFERENCE_HIGH/>
        <REFERENCE_UNIT/>
        <DATE_TIME_STAMP/>
        <STUDY_ID>1</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>wbc_lborres</redcapFieldNameValue><redcapFieldNameUnits>wbc_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>wbc_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>PLATELET COUNT</NAME>
        <loinc_code>1009</loinc_code>
        <RESULT>92</RESULT>
        <REFERENCE_LOW/>
        <REFERENCE_HIGH/>
        <REFERENCE_UNIT/>
        <DATE_TIME_STAMP/>
        <STUDY_ID>1</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>plat_lborres</redcapFieldNameValue><redcapFieldNameUnits>plat_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>plat_lbstat</redcapFieldNameStatus></subject>
    <subject>
        <NAME>HEMOGLOBIN</NAME>
        <loinc_code>1534435</loinc_code>
        <RESULT>9.5</RESULT>
        <REFERENCE_LOW>12.0</REFERENCE_LOW>
        <REFERENCE_HIGH>16.0</REFERENCE_HIGH>
        <REFERENCE_UNIT>g/dL</REFERENCE_UNIT>
        <DATE_TIME_STAMP/>
        <STUDY_ID>1</STUDY_ID>
    <timestamp/><redcapFormName>cbc</redcapFormName><eventName/><formDateField>cbc_lbdtc</formDateField><formCompletedFieldName>cbc_complete</formCompletedFieldName><formImportedFieldName>cbc_nximport</formImportedFieldName><redcapFieldNameValue>hemo_lborres</redcapFieldNameValue><redcapFieldNameUnits>hemo_lborresu</redcapFieldNameUnits><redcapFieldNameStatus>hemo_lbstat</redcapFieldNameStatus></subject>
    </study>"""

        self.expect = etree.tostring(etree.fromstring(self.output))
        self.configuration_directory = tempfile.mkdtemp('/')
        self.research_id_to_redcap_id = "research_id_to_redcap_id_map.xml"
        try:
            f = open(os.path.join(self.configuration_directory, self.research_id_to_redcap_id), "w+")
            f.write("""<subject_id_field_mapping>
  <redcap_id_field_name>dm_subjid</redcap_id_field_name>
  <research_id_field_name>dm_usubjid</research_id_field_name>
</subject_id_field_mapping>""")
            f.close()
        except:
            print("setUp failed to create file '" + self.research_id_to_redcap_id + "'")

    def dummy_redcapClient_initializer(self, redcap_uri, token, verify_ssl):
        pass
        
    def dummy_get_data_from_redcap(self,records_to_fecth=[],events_to_fetch=[], fields_to_fetch=[], forms_to_fetch=[], return_format='xml'):
        dummy_output = """<?xml version="1.0" encoding="UTF-8" ?>
<records>
<item><dm_subjid><![CDATA[1]]></dm_subjid><redcap_event_name><![CDATA[1]]></redcap_event_name><dm_usubjid><![CDATA[999-0059]]></dm_usubjid></item>
</records>"""
        return dummy_output

    def dummy_redcapClient_initializer_with_exception(self, redcap_uri, token, verify_ssl):
        raise RequestException

    def dummy_send_email_redcap_connection_error(email_settings):
        raise Exception

    @patch.multiple(RedcapClient, __init__ = dummy_redcapClient_initializer, get_data_from_redcap = dummy_get_data_from_redcap)
    def test_research_id_to_redcap_id_converter(self):
        redi.configure_logging(DEFAULT_DATA_DIRECTORY)
        email_settings = {}
        redcap_settings = {}
        redcap_settings['redcap_uri'] = 'https://example.org/redcap/api/'
        redcap_settings['token'] = 'ABCDEF878D219CFA5D3ADF7F9AB12345'
        redcap_settings['verify_ssl'] = False
        redi.research_id_to_redcap_id_converter(self.data, redcap_settings, email_settings, self.research_id_to_redcap_id, False, self.configuration_directory)
        result = etree.tostring(self.data)
        self.assertEqual(self.expect, result)

    @patch.multiple(RedcapClient, __init__ = dummy_redcapClient_initializer_with_exception, get_data_from_redcap = dummy_get_data_from_redcap)
    def test_research_id_to_redcap_id_converter_connection_error(self):
        redi.configure_logging(DEFAULT_DATA_DIRECTORY)
        email_settings = {}
        redcap_settings = {}
        redcap_settings['redcap_uri'] = 'https://example.org/redcap/api/'
        redcap_settings['token'] = 'ABCDEF878D219CFA5D3ADF7F9AB12345'
        redcap_settings['verify_ssl'] = False
        self.assertRaises(SystemExit,redi.research_id_to_redcap_id_converter,self.data,redcap_settings,email_settings, self.research_id_to_redcap_id, True, self.configuration_directory)
    
    @patch.multiple(RedcapClient, __init__ = dummy_redcapClient_initializer_with_exception, get_data_from_redcap = dummy_get_data_from_redcap)
    @patch.multiple(redi_email,send_email_redcap_connection_error=dummy_send_email_redcap_connection_error)
    def test_research_id_to_redcap_id_converter_mail_key_error(self):
        redi.configure_logging(DEFAULT_DATA_DIRECTORY)
        email_settings = {}
        redcap_settings = {}
        redcap_settings['redcap_uri'] = 'https://example.org/redcap/api/'
        redcap_settings['token'] = 'ABCDEF878D219CFA5D3ADF7F9AB12345'
        self.assertRaises(Exception,redi.research_id_to_redcap_id_converter,self.data,redcap_settings,email_settings, self.research_id_to_redcap_id, False, self.configuration_directory)

    def tearDown(self):
        try:
            os.unlink(os.path.join(self.configuration_directory, self.research_id_to_redcap_id))
        except:
            print("setUp failed to unlink file '" + "research_id_to_redcap_id_map.xml" + "'")
        try:
            os.rmdir(self.configuration_directory)
        except OSError:
            raise LogException("Folder " + self.configuration_directory + "is not empty, hence cannot be deleted.")
        return()

if __name__ == "__main__":
    unittest.main()
