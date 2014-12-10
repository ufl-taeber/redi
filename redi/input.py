import csv
import decimal
import time

from lxml import etree

HEADER_LOINC_CODE = 'loinc_code'
HEADER_LOINC_COMPONENT = 'loinc_component'
HEADER_RESULT = 'result'
HEADER_UNITS = 'units'
HEADER_SUBJECT = 'study_id'
HEADER_TIMESTAMP = 'date_time_stamp'
ELEMENT_SUBJECT = 'subject'


class CsvReader(object):
    def __init__(self, clinical_components_service, headers=None, timestamp_format=None):
        names = (HEADER_LOINC_CODE, HEADER_LOINC_COMPONENT, HEADER_RESULT,
                 HEADER_UNITS, HEADER_SUBJECT, HEADER_TIMESTAMP)
        self._headers = dict(zip(names, names))
        if headers:
            self._headers.update(headers)

        self._clinical_components_service = clinical_components_service
        self._timestamp_format = timestamp_format

    def read(self, stream):
        reader = csv.DictReader(stream)
        return ClinicalRecords(list(reader), self._headers,
                               self._clinical_components_service,
                               self._timestamp_format)


class FlatXmlReader(CsvReader):
    class _LxmlWrapper(object):
        """Wraps an LXML element to support an indexer"""
        def __init__(self, element):
            self._element = element

        def __getitem__(self, item):
            return self._element.findtext(item)

    def read(self, stream):
        tree = etree.parse(stream)
        return ClinicalRecords([self._LxmlWrapper(s)
                                for s in tree.xpath('//' + ELEMENT_SUBJECT)],
                               self._headers, self._clinical_components_service,
                               self._timestamp_format)


class ClinicalRecords(object):

    def __init__(self, iterable, headers, clinical_components_service,
                 timestamp_format):
        self._records = iterable
        self._headers = headers
        self._clinical_components_service = clinical_components_service
        self._timestamp_format = timestamp_format

    def __len__(self):
        return len(self._records)

    def __getitem__(self, index):
        return ClinicalRecord(self._records[index], self._headers,
                              self._clinical_components_service,
                              self._timestamp_format)


class Result(object):
    def __init__(self, result_type, verbatim):
        self._type = result_type
        self._verbatim = verbatim

    @property
    def value(self):
        return self._type(self._verbatim)

    @property
    def verbatim(self):
        return self._verbatim


class ClinicalRecord(object):
    def __init__(self, record, headers, clinical_components_service,
                 timestamp_format):
        self._record = record
        self._headers = headers
        loinc_code = self._record[self._headers[HEADER_LOINC_CODE]]
        self._component = clinical_components_service[loinc_code]
        self._timestamp_format = timestamp_format

    @property
    def component(self):
        return self._component

    @property
    def result(self):
        return Result(self.component.type,
                      self._record[self._headers[HEADER_RESULT]])

    @property
    def subject(self):
        return self._record[self._headers[HEADER_SUBJECT]]

    @property
    def timestamp(self):
        return time.strptime(self._record[HEADER_TIMESTAMP], self._timestamp_format)

    @property
    def units(self):
        if not self.component.has_units:
            raise NotImplemented()
        return self._record[self._headers[HEADER_UNITS]]


def boolean(text):
    return text.strip("\"'").lower() in ('y', 'yes', 't', 'true')


def number(text):
    return decimal.Decimal(text)


class ClinicalComponent(object):
    TYPE_NUMBER = 'number'
    TYPE_BOOLEAN = 'boolean'
    TYPE_TEXT = 'text'

    KNOWN_TYPES = {
        TYPE_NUMBER: number,
        TYPE_BOOLEAN: boolean,
        TYPE_TEXT: str,
    }

    def __init__(self, name, loinc_code, type=TYPE_NUMBER, has_units=True):
        self.name = name
        self.loinc_code = loinc_code
        self.type = type
        if type in self.KNOWN_TYPES:
            self.type = self.KNOWN_TYPES[type]
        self.has_units = has_units


class ClinicalComponents(object):
    def __init__(self, components):
        self._components = dict(components)

    def __getitem__(self, loinc_code):
        return self._components[loinc_code]

    @staticmethod
    def from_csv(iterable):
        reader = csv.DictReader(iterable, skipinitialspace=True)
        components = {
            (r['loinc_code'],
             ClinicalComponent(r['loinc_component'], r['loinc_code'],
                               r['type'] or None,
                               r['has_units'] if r['has_units'] else True))
            for r in reader}
        return ClinicalComponents(components)