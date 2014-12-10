import csv

HEADER_LOINC_CODE = 'loinc_code'
HEADER_LOINC_COMPONENT = 'loinc_component'
HEADER_RESULT = 'result'
HEADER_UNITS = 'units'


class EpicExportReader(object):
    def __init__(self, headers=None):
        names = (HEADER_LOINC_CODE, HEADER_LOINC_COMPONENT, HEADER_RESULT,
                 HEADER_UNITS)
        self._headers = dict(zip(names, names))
        if headers:
            self._headers.update(headers)

    def read(self, stream):
        reader = csv.DictReader(stream)
        return ClinicalRecords(list(reader), self._headers)


class ClinicalRecords(object):

    def __init__(self, iterable, headers):
        self._records = iterable
        self._headers = headers

    def __len__(self):
        return len(self._records)

    def __getitem__(self, index):
        return ClinicalRecord(self._records[index], self._headers)


class ClinicalRecord(object):
    def __init__(self, record, headers):
        self._record = record
        self._headers = headers

    @property
    def component(self):
        loinc_component = self._record[self._headers[HEADER_LOINC_COMPONENT]]
        loinc_code = self._record[self._headers[HEADER_LOINC_CODE]]
        return ClinicalComponent(loinc_component, loinc_code)

    @property
    def result(self):
        return float(self._record[self._headers[HEADER_RESULT]])

    @property
    def units(self):
        return self._record[self._headers[HEADER_UNITS]]


class ClinicalComponent(object):
    def __init__(self, name, loinc_code):
        self.name = name
        self.loinc_code = loinc_code
